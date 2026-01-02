import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.views import View
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Item, Order
from .mixins import (
    DiscountTaxMixin,
    ItemRetrievalMixin,
    LineItemsMixin,
    OrderRetrievalMixin,
    StripeErrorHandlerMixin,
    StripeKeysMixin,
)
from .serializers import ItemSerializer, OrderSerializer


class ItemDetailView(
    StripeKeysMixin,
    View
):
    """Отображает страницу с информацией о товаре."""

    def get(self, request, id):
        item = get_object_or_404(Item, id=id)
        stripe_keys = self.get_stripe_keys(item.currency)

        context = {
            'item': item,
            'stripe_publishable_key': stripe_keys['publishable_key'],
            'domain': settings.DOMAIN,
        }
        return render(request, 'items/item_detail.html', context)


class CreateCheckoutSessionView(
    StripeKeysMixin,
    StripeErrorHandlerMixin,
    ItemRetrievalMixin,
    LineItemsMixin,
    APIView
):
    """Создание Stripe Checkout Session для одного товара."""

    def get(self, request, id):
        item = self.get_item(id)
        # Убедимся, что у товара есть валюта.
        if not item.currency:
            return Response(
                {'error': 'Валюта товара не определена'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            self.set_stripe_api_key(item.currency)
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[self.create_item_line_item(item)],
                mode='payment',
                success_url=f'{settings.DOMAIN}/success/',
                cancel_url=f'{settings.DOMAIN}/cancel/',
            )
            return Response(
                {'id': checkout_session.id}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return self.handle_stripe_error(e)
        except Exception as e:
            return Response(
                {'error': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreatePaymentIntentView(
    StripeKeysMixin,
    StripeErrorHandlerMixin,
    ItemRetrievalMixin,
    APIView
):
    """Создает Stripe Payment Intent для одного товара"""

    def get(self, request, id):
        item = self.get_item(id)
        stripe_keys = self.set_stripe_api_key(item.currency)

        try:
            intent = stripe.PaymentIntent.create(
                amount=int(item.price * 100),
                currency=item.currency,
                metadata={'item_id': item.id},
                automatic_payment_methods={'enabled': True},
            )
            return Response({
                'clientSecret': intent.client_secret,
                'publishableKey': stripe_keys['publishable_key']
            }, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return self.handle_stripe_error(e)
        except Exception as e:
            return self.handle_generic_error(e)


class OrderCheckoutSessionView(
    StripeKeysMixin,
    StripeErrorHandlerMixin,
    OrderRetrievalMixin,
    LineItemsMixin,
    DiscountTaxMixin,
    APIView
):
    """Создает Checkout Session для Order с несколькими товарами"""

    def get(self, request, order_id):
        order = self.get_order(order_id)
        currency = order.get_currency()
        self.set_stripe_api_key(currency)

        try:
            checkout_params = {
                'payment_method_types': ['card'],
                'line_items': self.create_order_line_items(order),
                'mode': 'payment',
                'success_url': f'{settings.DOMAIN}/success/',
                'cancel_url': f'{settings.DOMAIN}/cancel/',
                'metadata': {'order_id': str(order.id)},
            }
            # Добавляем скидку если есть.
            discounts = self.get_discount_params(order)
            if discounts:
                checkout_params['discounts'] = discounts
            # Добавляем параметры налогов.
            tax_params = self.get_tax_params(order)
            checkout_params.update(tax_params)
            tax_rates = self.get_tax_rates(order)
            if tax_rates:
                checkout_params['tax_rates'] = tax_rates
            checkout_session = stripe.checkout.Session.create(
                **checkout_params)
            return Response(
                {'id': checkout_session.id}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return self.handle_stripe_error(e)
        except Exception as e:
            return self.handle_generic_error(e)


class OrderPaymentIntentView(
    StripeKeysMixin,
    StripeErrorHandlerMixin,
    OrderRetrievalMixin,
    DiscountTaxMixin,
    APIView
):
    """Создает Payment Intent для Order"""

    def post(self, request, order_id):
        order = self.get_order(order_id)
        currency = order.get_currency()
        stripe_keys = self.get_stripe_keys(currency)
        stripe.api_key = stripe_keys['secret_key']
        try:
            # Рассчитываем сумму в центах.
            total_amount = int(order.get_total_price() * 100)
            intent_params = {
                'amount': total_amount,
                'currency': currency,
                'metadata': {'order_id': str(order.id)},
                'automatic_payment_methods': {'enabled': True},
            }
            if order.tax:
                # Рассчитываем сумму без налога и налог отдельно.
                subtotal = sum(
                    float(item.price) * quantity
                    for item, quantity in
                    order.order_items.values_list('item', 'quantity')
                )
                tax_amount = subtotal * (order.tax.rate / 100)
                intent_params['amount'] = int((subtotal + tax_amount) * 100)
                intent_params['description'] = (
                    f'{order.tax.rate}% {order.tax.name}')
            # Если есть скидка
            if order.discount and order.discount.coupon_id:
                intent_params['discounts'] = [{
                    'coupon': order.discount.coupon_id
                }]
            intent = stripe.PaymentIntent.create(**intent_params)
            return Response({
                'clientSecret': intent.client_secret,
                'publishableKey': stripe_keys['publishable_key']
            }, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return self.handle_stripe_error(e)
        except Exception as e:
            return Response(
                {'error': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ItemListView(APIView):
    """Получает список товаров."""

    def get(self, request):
        items = Item.objects.all()
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderCreateView(APIView):
    """Создает новый заказ."""

    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.save()
            return Response(
                OrderSerializer(order).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderDetailView(APIView):
    """Получает детали заказа."""

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SuccessView(View):
    """Возрващает страницу успешной оплаты."""

    def get(self, request):
        return render(request, 'items/success.html')


class CancelView(View):
    """Возрващает страницу отмены оплаты."""

    def get(self, request):
        return render(request, 'items/cancel.html')
