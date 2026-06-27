"""
Signals for the bookings app.
Auto-creates BookingStatusHistory on every booking status change.
"""

from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Booking, BookingStatusHistory


@receiver(pre_save, sender=Booking)
def track_booking_status_change(sender, instance, **kwargs):
    """
    Create a BookingStatusHistory record whenever the booking status changes.
    Uses pre_save to capture old_status before the save happens.
    """
    if not instance.pk:
        # New booking — will be handled by post_save
        return

    try:
        old_instance = Booking.objects.get(pk=instance.pk)
    except Booking.DoesNotExist:
        return

    if old_instance.status != instance.status:
        # Store the change info on the instance for post_save to create the history
        instance._status_changed = True
        instance._old_status = old_instance.status
    else:
        instance._status_changed = False


from django.db.models.signals import post_save  # noqa: E402


@receiver(post_save, sender=Booking)
def create_status_history(sender, instance, created, **kwargs):
    """
    After save, create BookingStatusHistory if status changed or booking is new.
    """
    if created:
        # New booking — record initial status
        BookingStatusHistory.objects.create(
            booking=instance,
            old_status="",
            new_status=instance.status,
            changed_by=instance.patient,
            note="Booking created",
        )
    elif getattr(instance, "_status_changed", False):
        # Status changed on existing booking
        changed_by = getattr(instance, "_status_changed_by", None)
        note = getattr(instance, "_status_change_note", "")
        BookingStatusHistory.objects.create(
            booking=instance,
            old_status=instance._old_status,
            new_status=instance.status,
            changed_by=changed_by,
            note=note,
        )
