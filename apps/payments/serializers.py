"""
Serializers for the payments app.
"""

from rest_framework import serializers

from .models import Payment, Subscription


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for payment details."""

    booking_id = serializers.UUIDField(source="booking.id", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "booking",
            "booking_id",
            "razorpay_order_id",
            "razorpay_payment_id",
            "amount",
            "currency",
            "status",
            "paid_at",
            "created_at",
        ]
        read_only_fields = fields


class CreateOrderSerializer(serializers.Serializer):
    """Serializer for creating a Razorpay order."""

    booking_id = serializers.UUIDField()

    def validate_booking_id(self, value):
        from apps.bookings.models import Booking

        try:
            booking = Booking.objects.get(id=value)
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found.")

        # Check if payment already exists
        if hasattr(booking, "payment") and booking.payment.status == Payment.Status.PAID:
            raise serializers.ValidationError("This booking is already paid.")

        return value


class VerifyPaymentSerializer(serializers.Serializer):
    """Serializer for verifying Razorpay payment signature."""

    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for subscription details."""

    plan_display = serializers.CharField(source="get_plan_display", read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "plan",
            "plan_display",
            "start_date",
            "end_date",
            "is_active",
            "razorpay_subscription_id",
            "created_at",
        ]
        read_only_fields = ["id", "start_date", "end_date", "is_active", "razorpay_subscription_id", "created_at"]


class CreateSubscriptionSerializer(serializers.Serializer):
    """Serializer for creating a new subscription."""

    plan = serializers.ChoiceField(choices=Subscription.Plan.choices)
