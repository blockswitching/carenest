"""
Models for the health_records app.
Manages patient vitals, medication reminders, wound care logs, and health reports.
"""

from django.conf import settings
from django.db import models

from core.models import BaseModel


class HealthRecord(BaseModel):
    """Patient vital signs recorded during a visit or check-up."""

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="health_records",
        limit_choices_to={"role": "PATIENT"},
    )
    booking = models.ForeignKey(
        "bookings.Booking",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="health_records",
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="recorded_health_records",
        limit_choices_to={"role__in": ["CAREGIVER", "NURSE"]},
    )

    # Vitals
    blood_pressure_systolic = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    heart_rate = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    blood_sugar = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True, help_text="mg/dL"
    )
    temperature = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True, help_text="Fahrenheit"
    )
    weight = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, help_text="kg"
    )
    spo2 = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True, help_text="SpO2 %"
    )

    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField()

    class Meta:
        db_table = "health_records"
        verbose_name = "Health Record"
        verbose_name_plural = "Health Records"
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"Vitals - {self.patient.full_name} ({self.recorded_at:%Y-%m-%d %H:%M})"


class MedicationReminder(BaseModel):
    """Scheduled medication reminders for patients."""

    class Frequency(models.TextChoices):
        DAILY = "DAILY", "Once Daily"
        TWICE = "TWICE", "Twice Daily"
        THRICE = "THRICE", "Thrice Daily"
        WEEKLY = "WEEKLY", "Weekly"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="medication_reminders",
        limit_choices_to={"role": "PATIENT"},
    )
    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100, help_text="e.g. 500mg, 1 tablet")
    frequency = models.CharField(max_length=10, choices=Frequency.choices)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    reminder_time = models.TimeField(help_text="Primary reminder time")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "medication_reminders"
        verbose_name = "Medication Reminder"
        verbose_name_plural = "Medication Reminders"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.medicine_name} - {self.patient.full_name}"


class WoundCareLog(BaseModel):
    """Log wound care progress during visits."""

    class Severity(models.TextChoices):
        MILD = "MILD", "Mild"
        MODERATE = "MODERATE", "Moderate"
        SEVERE = "SEVERE", "Severe"
        CRITICAL = "CRITICAL", "Critical"

    booking = models.ForeignKey(
        "bookings.Booking",
        on_delete=models.CASCADE,
        related_name="wound_care_logs",
    )
    description = models.TextField()
    photo = models.ImageField(upload_to="wound_care/%Y/%m/", blank=True, null=True)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    next_visit_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "wound_care_logs"
        verbose_name = "Wound Care Log"
        verbose_name_plural = "Wound Care Logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Wound Log - {self.severity} ({self.created_at:%Y-%m-%d})"


class HealthReport(BaseModel):
    """Uploaded health reports and documents."""

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="health_reports",
        limit_choices_to={"role": "PATIENT"},
    )
    title = models.CharField(max_length=200)
    report_file = models.FileField(upload_to="health_reports/%Y/%m/")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_reports",
    )
    report_date = models.DateField()

    class Meta:
        db_table = "health_reports"
        verbose_name = "Health Report"
        verbose_name_plural = "Health Reports"
        ordering = ["-report_date"]

    def __str__(self):
        return f"{self.title} - {self.patient.full_name}"
