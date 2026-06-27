"""
Models for the bookings app.
Handles the full booking lifecycle including status tracking and caregiver assignment.
"""

from django.conf import settings
from django.db import models

from core.models import BaseModel


class Booking(BaseModel):
    """A booking for a healthcare service."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CAREGIVER_ASSIGNED = "CAREGIVER_ASSIGNED", "Caregiver Assigned"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_bookings",
        limit_choices_to={"role": "PATIENT"},
    )
    caregiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="caregiver_bookings",
        limit_choices_to={"role__in": ["CAREGIVER", "NURSE"]},
    )
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6)
    patient_notes = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "bookings"
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Booking #{str(self.id)[:8]} - {self.patient.full_name} ({self.status})"


class BookingStatusHistory(BaseModel):
    """Tracks every status change on a booking."""

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="status_changes",
    )
    note = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "booking_status_history"
        verbose_name = "Booking Status History"
        verbose_name_plural = "Booking Status Histories"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.booking} : {self.old_status} -> {self.new_status}"


class CaregiverAssignment(BaseModel):
    """Tracks caregiver assignment and live tracking data for a booking."""

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="assignment",
    )
    caregiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignments",
        limit_choices_to={"role__in": ["CAREGIVER", "NURSE"]},
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    estimated_arrival = models.DateTimeField(null=True, blank=True)
    actual_arrival = models.DateTimeField(null=True, blank=True)
    tracking_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Live tracking data, e.g. {'lat': 12.97, 'lng': 77.59}",
    )

    class Meta:
        db_table = "caregiver_assignments"
        verbose_name = "Caregiver Assignment"
        verbose_name_plural = "Caregiver Assignments"

    def __str__(self):
        return f"Assignment: {self.caregiver.full_name} -> Booking #{str(self.booking.id)[:8]}"
