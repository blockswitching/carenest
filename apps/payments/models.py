"""
Models for the payments app.
Handles Razorpay payment processing and subscription management.
"""

from django.conf import settings
from django.db import models

from core.models import BaseModel


class Payment(BaseModel):
    """Payment record linked to a booking via Razorpay."""

    class Status(models.TextChoices):
        CREATED = "CREATED", "Created"
        PAID = "PAID", "Paid"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"

    booking = models.OneToOneField(
        "bookings.Booking",
        on_delete=models.CASCADE,
        related_name="payment",
    )
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.CREATED,
    )
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payments"
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.razorpay_order_id} - ₹{self.amount} ({self.status})"


class Subscription(BaseModel):
    """User subscription plan managed via Razorpay."""

    class Plan(models.TextChoices):
        BASIC_299 = "BASIC_299", "Basic - ₹299/month"
        FAMILY_599 = "FAMILY_599", "Family - ₹599/month"
        PREMIUM_999 = "PREMIUM_999", "Premium - ₹999/month"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    plan = models.CharField(max_length=20, choices=Plan.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    razorpay_subscription_id = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "subscriptions"
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.user.full_name} - {self.get_plan_display()}"
