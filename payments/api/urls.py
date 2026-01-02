from django.urls import path

from .views import (
    CancelView,
    CreateCheckoutSessionView,
    CreatePaymentIntentView,
    ItemDetailView,
    ItemListView,
    OrderCheckoutSessionView,
    OrderCreateView,
    OrderDetailView,
    OrderPaymentIntentView,
    SuccessView,
)

urlpatterns = [
    path(
        'item/<int:id>/', ItemDetailView.as_view(), name='item-detail'),
    path('success/', SuccessView.as_view(), name='success'),
    path('cancel/', CancelView.as_view(), name='cancel'),
    path(
        'buy/<int:id>/',
        CreateCheckoutSessionView.as_view(),
        name='create-checkout-session'
    ),
    path(
        'payment-intent/<int:id>/',
        CreatePaymentIntentView.as_view(),
        name='create-payment-intent'
    ),
    path(
        'order/<uuid:order_id>/checkout/',
        OrderCheckoutSessionView.as_view(),
        name='order-checkout'
    ),
    path(
        'order/<uuid:order_id>/payment-intent/',
        OrderPaymentIntentView.as_view(),
        name='order-payment-intent'
    ),
    path('api/items/', ItemListView.as_view(), name='item-list'),
    path('api/orders/', OrderCreateView.as_view(), name='order-create'),
    path(
        'api/orders/<uuid:order_id>/',
        OrderDetailView.as_view(),
        name='order-detail'
    ),
]
