"""
Views for the notifications app.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FCMDevice, Notification
from .serializers import (
    EmergencySerializer,
    NotificationSerializer,
    RegisterDeviceSerializer,
)


@extend_schema(tags=["Notifications"])
class NotificationListView(generics.ListAPIView):
    """GET /api/v1/notifications/ — List user notifications (unread first)."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List notifications",
        description="Retrieve all notifications for the authenticated user, ordered by unread first then newest.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user, is_active=True)


@extend_schema(tags=["Notifications"])
class MarkNotificationReadView(APIView):
    """PATCH /api/v1/notifications/{id}/read/ — Mark a notification as read."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Mark notification as read",
        description="Mark a specific notification as read.",
        responses={200: NotificationSerializer},
    )
    def patch(self, request, pk):
        try:
            notification = Notification.objects.get(
                id=pk, user=request.user, is_active=True
            )
        except Notification.DoesNotExist:
            return Response(
                {"detail": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        notification.is_read = True
        notification.save(update_fields=["is_read", "updated_at"])
        return Response(NotificationSerializer(notification).data)


@extend_schema(tags=["Notifications"])
class RegisterDeviceView(APIView):
    """POST /api/v1/notifications/register-device/ — Register FCM token."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Register FCM device",
        description="Register a Firebase Cloud Messaging device token for push notifications.",
        request=RegisterDeviceSerializer,
    )
    def post(self, request):
        serializer = RegisterDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device_token = serializer.validated_data["device_token"]
        platform = serializer.validated_data["platform"]

        FCMDevice.objects.update_or_create(
            user=request.user,
            device_token=device_token,
            defaults={"platform": platform, "is_active": True},
        )

        return Response(
            {"message": "Device registered successfully."},
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Notifications"])
class EmergencyView(APIView):
    """POST /api/v1/notifications/emergency/ — Emergency alert to caregivers."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Send emergency alert",
        description="Patient presses emergency button. Alerts all linked caregivers "
        "and family contacts via push notification.",
        request=EmergencySerializer,
    )
    def post(self, request):
        serializer = EmergencySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data.get("message", "")
        latitude = serializer.validated_data.get("latitude")
        longitude = serializer.validated_data.get("longitude")

        patient = request.user
        location_info = ""
        if latitude and longitude:
            location_info = f" Location: {latitude}, {longitude}"

        from apps.bookings.models import Booking

        active_bookings = Booking.objects.filter(
            patient=patient,
            status__in=["CAREGIVER_ASSIGNED", "IN_PROGRESS"],
            caregiver__isnull=False,
        ).select_related("caregiver")

        notified_users = set()

        for booking in active_bookings:
            caregiver = booking.caregiver
            if caregiver.id not in notified_users:
                Notification.objects.create(
                    user=caregiver,
                    title="EMERGENCY ALERT",
                    body=f"Patient {patient.full_name} needs immediate help! {message}{location_info}",
                    notification_type=Notification.NotificationType.EMERGENCY,
                )
                notified_users.add(caregiver.id)

                from apps.notifications.tasks import send_push_notification

                send_push_notification.delay(
                    user_id=str(caregiver.id),
                    title="EMERGENCY ALERT",
                    body=f"Patient {patient.full_name} needs immediate help! {message}{location_info}",
                )

        return Response(
            {
                "message": "Emergency alert sent to all linked caregivers.",
                "notified_count": len(notified_users),
            },
            status=status.HTTP_200_OK,
        )
