"""
URL patterns for the notifications app.
Mounted at /api/v1/
"""

from django.urls import path

from .views import (
    EmergencyView,
    MarkNotificationReadView,
    NotificationListView,
    RegisterDeviceView,
)

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path(
        "notifications/<uuid:pk>/read/",
        MarkNotificationReadView.as_view(),
        name="notification-read",
    ),
    path(
        "notifications/register-device/",
        RegisterDeviceView.as_view(),
        name="notification-register-device",
    ),
    path(
        "notifications/emergency/",
        EmergencyView.as_view(),
        name="notification-emergency",
    ),
]
