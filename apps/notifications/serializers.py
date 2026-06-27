"""
Serializers for the notifications app.
"""

from rest_framework import serializers

from .models import FCMDevice, Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""

    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "body",
            "notification_type",
            "is_read",
            "created_at",
        ]
        read_only_fields = fields


class RegisterDeviceSerializer(serializers.Serializer):
    """Serializer for registering an FCM device token."""

    device_token = serializers.CharField(max_length=500)
    platform = serializers.ChoiceField(choices=FCMDevice.Platform.choices)


class EmergencySerializer(serializers.Serializer):
    """Serializer for the emergency button."""

    message = serializers.CharField(
        required=False,
        allow_blank=True,
        default="Emergency! Patient needs immediate assistance.",
    )
    latitude = serializers.DecimalField(
        max_digits=10, decimal_places=7, required=False, allow_null=True
    )
    longitude = serializers.DecimalField(
        max_digits=10, decimal_places=7, required=False, allow_null=True
    )
