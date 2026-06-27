"""
Admin configuration for the notifications app.
"""

from django.contrib import admin

from .models import FCMDevice, Notification


@admin.action(description="Send test notification to selected users")
def send_test_notification(modeladmin, request, queryset):
    """Send a test push notification to the users of selected notifications."""
    from apps.notifications.tasks import send_push_notification

    sent = 0
    for notification in queryset.select_related("user"):
        send_push_notification.delay(
            user_id=str(notification.user_id),
            title="Test Notification",
            body="This is a test notification from CareNest Admin.",
        )
        sent += 1
    modeladmin.message_user(request, f"Test notification queued for {sent} user(s).")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "notification_type", "is_read", "created_at"]
    list_filter = ["notification_type", "is_read"]
    search_fields = ["title", "body", "user__email"]
    date_hierarchy = "created_at"
    actions = [send_test_notification]
    list_per_page = 25
    show_full_result_count = False


@admin.register(FCMDevice)
class FCMDeviceAdmin(admin.ModelAdmin):
    list_display = ["user", "platform", "is_active", "created_at"]
    list_filter = ["platform", "is_active"]
    search_fields = ["user__email", "device_token"]
    list_per_page = 25
