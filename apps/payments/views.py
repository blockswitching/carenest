"""
Views for the payments app.
Razorpay integration for order creation and payment verification.
"""

import hashlib
import hmac
from datetime import date, timedelta

from decouple import config
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment, Subscription
from .serializers import (
    CreateOrderSerializer,
    CreateSubscriptionSerializer,
    PaymentSerializer,
    SubscriptionSerializer,
    VerifyPaymentSerializer,
)


def get_razorpay_client():
    """Lazy initialization of Razorpay client."""
    import razorpay

    return razorpay.Client(
        auth=(
            config("RAZORPAY_KEY_ID", default=""),
            config("RAZORPAY_KEY_SECRET", default=""),
        )
    )


@extend_schema(tags=["Payments"])
class CreateOrderView(APIView):
    """POST /api/v1/payments/create-order/ — Create a Razorpay order for a booking."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Create Razorpay order",
        description="Create a Razorpay order for a booking. Returns order_id, amount in paise, and key_id.",
        request=CreateOrderSerializer,
    )
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.bookings.models import Booking

        booking = Booking.objects.get(id=serializer.validated_data["booking_id"])
        amount_paise = int(booking.total_amount * 100)
        client = get_razorpay_client()

        try:
            razorpay_order = client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "receipt": str(booking.id),
                "notes": {
                    "booking_id": str(booking.id),
                    "patient": booking.patient.full_name,
                },
            })
        except Exception as e:
            return Response(
                {"detail": f"Failed to create Razorpay order: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        Payment.objects.update_or_create(
            booking=booking,
            defaults={
                "razorpay_order_id": razorpay_order["id"],
                "amount": booking.total_amount,
                "currency": "INR",
                "status": Payment.Status.CREATED,
            },
        )

        return Response(
            {
                "order_id": razorpay_order["id"],
                "amount": amount_paise,
                "currency": "INR",
                "key_id": config("RAZORPAY_KEY_ID", default=""),
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Payments"])
class VerifyPaymentView(APIView):
    """POST /api/v1/payments/verify/ — Verify Razorpay payment signature."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Verify payment",
        description="Verify Razorpay payment signature. Marks payment as PAID and booking as CONFIRMED on success.",
        request=VerifyPaymentSerializer,
    )
    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        razorpay_order_id = serializer.validated_data["razorpay_order_id"]
        razorpay_payment_id = serializer.validated_data["razorpay_payment_id"]
        razorpay_signature = serializer.validated_data["razorpay_signature"]

        secret = config("RAZORPAY_KEY_SECRET", default="")
        message = f"{razorpay_order_id}|{razorpay_payment_id}"
        expected_signature = hmac.new(
            secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        try:
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
        except Payment.DoesNotExist:
            return Response(
                {"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if hmac.compare_digest(expected_signature, razorpay_signature):
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.status = Payment.Status.PAID
            payment.paid_at = timezone.now()
            payment.save()

            booking = payment.booking
            if booking.status == "PENDING":
                booking._status_changed_by = request.user
                booking._status_change_note = "Payment verified"
                booking.status = "CONFIRMED"
                booking.save()

            return Response({
                "detail": "Payment verified successfully.",
                "payment": PaymentSerializer(payment).data,
            })
        else:
            payment.status = Payment.Status.FAILED
            payment.save()
            return Response(
                {"detail": "Payment verification failed."},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(tags=["Payments"])
class PaymentHistoryView(generics.ListAPIView):
    """GET /api/v1/payments/history/ — Patient's payment history."""

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Payment history",
        description="View payment history. Patients see own payments, admins see all.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN" or user.is_staff:
            return Payment.objects.all().select_related("booking")
        return Payment.objects.filter(booking__patient=user).select_related("booking")


@extend_schema(tags=["Payments"])
class CreateSubscriptionView(APIView):
    """POST /api/v1/subscriptions/create/ — Create a new subscription."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Create subscription",
        description="Subscribe to a plan (BASIC_299, FAMILY_599, PREMIUM_999). "
        "Deactivates any existing active subscription.",
        request=CreateSubscriptionSerializer,
        responses={201: SubscriptionSerializer},
    )
    def post(self, request):
        serializer = CreateSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = serializer.validated_data["plan"]
        today = date.today()

        Subscription.objects.filter(user=request.user, is_active=True).update(
            is_active=False
        )
        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            start_date=today,
            end_date=today + timedelta(days=30),
            is_active=True,
        )
        return Response(
            SubscriptionSerializer(subscription).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Payments"])
class MySubscriptionView(APIView):
    """GET /api/v1/subscriptions/me/ — Get current user's active subscription."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="My subscription",
        description="Get the current user's active subscription details.",
    )
    def get(self, request):
        instance = Subscription.objects.filter(
            user=request.user, is_active=True
        ).first()
        if instance is None:
            return Response(
                {"detail": "No active subscription found.", "subscription": None}
            )
        return Response({"subscription": SubscriptionSerializer(instance).data})
