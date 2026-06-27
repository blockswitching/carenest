"""
URL patterns for the payments app.
Mounted at /api/v1/
"""

from django.urls import path

from .views import (
    CreateOrderView,
    CreateSubscriptionView,
    MySubscriptionView,
    PaymentHistoryView,
    VerifyPaymentView,
)

urlpatterns = [
    path("payments/create-order/", CreateOrderView.as_view(), name="payment-create-order"),
    path("payments/verify/", VerifyPaymentView.as_view(), name="payment-verify"),
    path("payments/history/", PaymentHistoryView.as_view(), name="payment-history"),
    path("subscriptions/create/", CreateSubscriptionView.as_view(), name="subscription-create"),
    path("subscriptions/me/", MySubscriptionView.as_view(), name="subscription-me"),
]
