"""
Admin configuration for the health_records app.
"""

from django.contrib import admin

from .models import HealthRecord, HealthReport, MedicationReminder, WoundCareLog


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = [
        "patient",
        "blood_pressure_systolic",
        "blood_pressure_diastolic",
        "heart_rate",
        "spo2",
        "temperature",
        "recorded_at",
    ]
    list_filter = ["recorded_at"]
    search_fields = ["patient__email", "patient__first_name", "patient__last_name"]
    date_hierarchy = "recorded_at"


@admin.register(MedicationReminder)
class MedicationReminderAdmin(admin.ModelAdmin):
    list_display = [
        "patient",
        "medicine_name",
        "dosage",
        "frequency",
        "reminder_time",
        "is_active",
    ]
    list_filter = ["is_active", "frequency", "patient"]
    search_fields = ["patient__email", "patient__first_name", "medicine_name"]


@admin.register(WoundCareLog)
class WoundCareLogAdmin(admin.ModelAdmin):
    list_display = ["booking", "severity", "next_visit_date", "created_at"]
    list_filter = ["severity"]
    search_fields = ["description"]


@admin.register(HealthReport)
class HealthReportAdmin(admin.ModelAdmin):
    list_display = ["title", "patient", "uploaded_by", "report_date", "created_at"]
    list_filter = ["report_date"]
    search_fields = ["title", "patient__email", "patient__first_name"]
