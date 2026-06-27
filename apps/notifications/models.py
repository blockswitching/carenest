"""
Models for the notifications app.
Handles in-app notifications and FCM device registration.
"""

from django.conf import settings
from django.db import models

from core.models import BaseModel


class Notification(BaseModel):
    """In-app notification for users."""

    class NotificationType(models.TextChoices):
        BOOKING_UPDATE = "BOOKING_UPDATE", "Booking Update"
        REMINDER = "REMINDER", "Reminder"
        PAYMENT = "PAYMENT", "Payment"
        EMERGENCY = "EMERGENCY", "Emergency"
        GENERAL = "GENERAL", "General"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
    )
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = "notifications"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["is_read", "-created_at"]

    def __str__(self):
        return f"{self.title} -> {self.user.email}"


class FCMDevice(BaseModel):
    """Firebase Cloud Messaging device token registration."""

    class Platform(models.TextChoices):
        ANDROID = "ANDROID", "Android"
        IOS = "IOS", "iOS"
        WEB = "WEB", "Web"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fcm_devices",
    )
    device_token = models.CharField(max_length=500)
    platform = models.CharField(max_length=10, choices=Platform.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "fcm_devices"
        verbose_name = "FCM Device"
        verbose_name_plural = "FCM Devices"
        unique_together = ["user", "device_token"]

    def __str__(self):
        return f"{self.user.email} - {self.platform} ({self.device_token[:20]}...)"
