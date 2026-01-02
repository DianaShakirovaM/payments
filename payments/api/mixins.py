import stripe

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from django.conf import settings
from core.models import Item, Order


class StripeKeysMixin:
    """Миксин для работы со Stripe-ключами"""

    def get_stripe_keys(self, currency):
        """Получает Stripe-ключи в зависимости от валюты"""
        if currency == 'eur':
            publishable_key = settings.STRIPE_PUBLISHABLE_KEY_EUR
            secret_key = settings.STRIPE_SECRET_KEY_EUR
        else:
            publishable_key = settings.STRIPE_PUBLISHABLE_KEY
            secret_key = settings.STRIPE_SECRET_KEY

        if not secret_key or not publishable_key:
            raise ValueError(
                f'Stripe-ключи не настроены для валюты: {currency}')

        return {
            'publishable_key': publishable_key,
            'secret_key': secret_key
        }

    def set_stripe_api_key(self, currency):
        """Устаналивает Stripe-ключ."""
        stripe_keys = self.get_stripe_keys(currency)
        stripe.api_key = stripe_keys['secret_key']
        return stripe_keys


class StripeErrorHandlerMixin:
    """Миксин для обработки ошибок Stripe."""

    def handle_stripe_error(self, stripe_error):
        """Обработка ошибок Stripe."""
        error_message = (
            str(stripe_error.user_message)
            if hasattr(stripe_error, 'user_message')
            else str(stripe_error)
        )
        return Response(
            {'error': error_message},
            status=status.HTTP_400_BAD_REQUEST
        )

    def handle_generic_error(self, exception):
        """Обработка общих ошибок."""
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ItemRetrievalMixin:
    """Миксин для получения товаров."""

    def get_item(self, item_id):
        return get_object_or_404(Item, id=item_id)


class OrderRetrievalMixin:
    """Миксин для получения заказов."""

    def get_order(self, order_id):
        return get_object_or_404(Order, id=order_id)


class LineItemsMixin:

    def create_item_line_item(self, item):
        return {
            'price_data': {
                'currency': item.currency,
                'product_data': {
                    'name': item.name,
                    'description': item.description,
                },
                'unit_amount': int(item.price * 100),
            },
            'quantity': 1,
        }

    def create_order_line_items(self, order):
        line_items = []
        for order_item in order.order_items.all():
            line_items.append({
                'price_data': {
                    'currency': order.get_currency(),
                    'product_data': {
                        'name': order_item.item.name,
                        'description': order_item.item.description,
                    },
                    'unit_amount': int(order_item.item.price * 100),
                },
                'quantity': order_item.quantity,
            })
        return line_items


class DiscountTaxMixin:
    """Миксин для работы со скидками и налогами."""

    def get_discount_params(self, order):
        """Получает параметры скидки."""
        return (
            [{'coupon': order.discount.coupon_id}] if order.discount
            and order.discount.coupon_id else None
        )

    def get_tax_params(self, order):
        """Получает параметры налога."""
        has_tax = bool(order.tax)
        return {
            'tax_id_collection': {'enabled': has_tax},
            'automatic_tax': {'enabled': has_tax},
        }

    def get_tax_rates(self, order):
        """Получает налоговую ставку."""
        return [order.tax.tax_id] if order.tax and order.tax.tax_id else []
