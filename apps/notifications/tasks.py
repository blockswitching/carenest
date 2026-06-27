"""
Celery tasks for the notifications app.
- send_push_notification: Send FCM push notification to a user
- send_medication_reminder: Scheduled via Celery Beat at reminder_time
- send_booking_reminder: 1 hour before scheduled_date
"""

import logging

import requests
from celery import shared_task
from decouple import config
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="notifications.send_push_notification")
def send_push_notification(user_id, title, body):
    """
    Send a push notification to a user via Firebase Cloud Messaging.
    Sends to all active devices registered for the user.
    """
    from apps.notifications.models import FCMDevice

    devices = FCMDevice.objects.filter(user_id=user_id, is_active=True)
    server_key = config("FIREBASE_SERVER_KEY", default="")

    if not server_key:
        logger.warning("FIREBASE_SERVER_KEY not configured. Skipping push notification.")
        return

    headers = {
        "Authorization": f"key={server_key}",
        "Content-Type": "application/json",
    }

    sent_count = 0
    for device in devices:
        payload = {
            "to": device.device_token,
            "notification": {
                "title": title,
                "body": body,
            },
            "data": {
                "title": title,
                "body": body,
            },
        }

        try:
            response = requests.post(
                "https://fcm.googleapis.com/fcm/send",
                json=payload,
                headers=headers,
                timeout=10,
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("failure", 0) > 0:
                    # Token may be invalid, deactivate device
                    device.is_active = False
                    device.save(update_fields=["is_active", "updated_at"])
                    logger.info(f"Deactivated invalid FCM token for user {user_id}")
                else:
                    sent_count += 1
            else:
                logger.error(
                    f"FCM request failed: {response.status_code} - {response.text}"
                )
        except requests.RequestException as e:
            logger.error(f"FCM request error: {e}")

    logger.info(f"Push notification sent to {sent_count}/{devices.count()} devices for user {user_id}")
    return sent_count


@shared_task(name="notifications.send_medication_reminder")
def send_medication_reminder():
    """
    Send medication reminders to patients.
    Should be scheduled via Celery Beat to run every 15 minutes.
    Checks for reminders due within the current 15-minute window.
    """
    from apps.health_records.models import MedicationReminder
    from apps.notifications.models import Notification

    now = timezone.localtime()
    current_time = now.time()
    today = now.date()

    # Find active reminders for current time window (±7 minutes)
    from datetime import timedelta, datetime, time

    window_start = (datetime.combine(today, current_time) - timedelta(minutes=7)).time()
    window_end = (datetime.combine(today, current_time) + timedelta(minutes=7)).time()

    reminders = MedicationReminder.objects.filter(
        is_active=True,
        is_active_record=True,
        start_date__lte=today,
        reminder_time__gte=window_start,
        reminder_time__lte=window_end,
    ).select_related("patient")

    # Filter out expired reminders
    reminders = reminders.filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
    )

    sent_count = 0
    for reminder in reminders:
        title = f"💊 Medication Reminder: {reminder.medicine_name}"
        body = f"Time to take {reminder.medicine_name} ({reminder.dosage})"

        # Create in-app notification
        Notification.objects.create(
            user=reminder.patient,
            title=title,
            body=body,
            notification_type=Notification.NotificationType.REMINDER,
        )

        # Send push notification
        send_push_notification.delay(
            user_id=str(reminder.patient_id),
            title=title,
            body=body,
        )
        sent_count += 1

    logger.info(f"Sent {sent_count} medication reminders")
    return sent_count


@shared_task(name="notifications.send_booking_reminder")
def send_booking_reminder():
    """
    Send reminders 1 hour before scheduled booking time.
    Should be scheduled via Celery Beat to run every 15 minutes.
    """
    from datetime import timedelta, datetime

    from apps.bookings.models import Booking
    from apps.notifications.models import Notification

    now = timezone.localtime()
    one_hour_later = now + timedelta(hours=1)

    # Find bookings starting within the next hour (±7 minute window)
    target_date = one_hour_later.date()
    target_time_start = (one_hour_later - timedelta(minutes=7)).time()
    target_time_end = (one_hour_later + timedelta(minutes=7)).time()

    bookings = Booking.objects.filter(
        scheduled_date=target_date,
        scheduled_time__gte=target_time_start,
        scheduled_time__lte=target_time_end,
        status__in=["CONFIRMED", "CAREGIVER_ASSIGNED"],
        is_active=True,
    ).select_related("patient", "caregiver", "service")

    sent_count = 0
    for booking in bookings:
        # Notify patient
        patient_title = "📅 Booking Reminder"
        patient_body = (
            f"Your {booking.service.name} appointment is in 1 hour "
            f"at {booking.scheduled_time.strftime('%I:%M %p')}."
        )

        Notification.objects.create(
            user=booking.patient,
            title=patient_title,
            body=patient_body,
            notification_type=Notification.NotificationType.REMINDER,
        )
        send_push_notification.delay(
            user_id=str(booking.patient_id),
            title=patient_title,
            body=patient_body,
        )

        # Notify caregiver if assigned
        if booking.caregiver:
            caregiver_title = "📅 Upcoming Service"
            caregiver_body = (
                f"You have a {booking.service.name} appointment with "
                f"{booking.patient.full_name} in 1 hour at {booking.scheduled_time.strftime('%I:%M %p')}."
            )

            Notification.objects.create(
                user=booking.caregiver,
                title=caregiver_title,
                body=caregiver_body,
                notification_type=Notification.NotificationType.REMINDER,
            )
            send_push_notification.delay(
                user_id=str(booking.caregiver_id),
                title=caregiver_title,
                body=caregiver_body,
            )

        sent_count += 1

    logger.info(f"Sent booking reminders for {sent_count} bookings")
    return sent_count
