"""
Admin configuration for the bookings app.
"""

import csv

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.http import HttpResponse

from .models import Booking, BookingStatusHistory, CaregiverAssignment

User = get_user_model()


class BookingStatusHistoryInline(admin.TabularInline):
    """Read-only inline showing status change history."""

    model = BookingStatusHistory
    extra = 0
    readonly_fields = ["old_status", "new_status", "changed_by", "note", "timestamp"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class CaregiverAssignmentInline(admin.StackedInline):
    model = CaregiverAssignment
    extra = 0
    readonly_fields = ["assigned_at"]


# ---------------------------------------------------------------------------
# Admin Actions
# ---------------------------------------------------------------------------


@admin.action(description="Export selected bookings to CSV")
def export_bookings_csv(modeladmin, request, queryset):
    """Export selected bookings as a CSV file."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="bookings_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "ID", "Patient", "Caregiver", "Service", "Status",
        "Scheduled Date", "Scheduled Time", "City", "Total Amount", "Created At",
    ])

    for booking in queryset.select_related("patient", "caregiver", "service"):
        writer.writerow([
            str(booking.id),
            booking.patient.full_name,
            booking.caregiver.full_name if booking.caregiver else "Unassigned",
            booking.service.name,
            booking.status,
            booking.scheduled_date,
            booking.scheduled_time,
            booking.city,
            booking.total_amount,
            booking.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    return response


@admin.action(description="Mark selected bookings as completed")
def mark_bookings_completed(modeladmin, request, queryset):
    """Mark selected bookings as completed."""
    eligible = queryset.filter(status__in=["CAREGIVER_ASSIGNED", "IN_PROGRESS"])
    count = 0
    for booking in eligible:
        booking._status_changed_by = request.user
        booking._status_change_note = "Marked completed by admin"
        booking.status = Booking.Status.COMPLETED
        booking.save()
        count += 1
    modeladmin.message_user(request, f"{count} booking(s) marked as completed.")


@admin.action(description="Assign available caregiver (auto-match by city)")
def assign_available_caregiver(modeladmin, request, queryset):
    """Auto-match a verified caregiver by city."""
    from apps.users.models import CaregiverProfile

    assigned_count = 0
    for booking in queryset.filter(
        caregiver__isnull=True,
        status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED],
    ):
        matching = CaregiverProfile.objects.filter(
            is_verified=True,
            is_active=True,
            user__profile__city__iexact=booking.city,
        ).select_related("user")

        if matching.exists():
            caregiver = matching.first().user
            booking.caregiver = caregiver
            booking._status_changed_by = request.user
            booking._status_change_note = f"Auto-assigned: {caregiver.full_name}"
            booking.status = Booking.Status.CAREGIVER_ASSIGNED
            booking.save()

            CaregiverAssignment.objects.update_or_create(
                booking=booking, defaults={"caregiver": caregiver}
            )
            assigned_count += 1

    modeladmin.message_user(
        request, f"Successfully assigned caregivers to {assigned_count} booking(s)."
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin for Booking with status history inline and multiple actions."""

    list_display = [
        "id",
        "patient",
        "service",
        "status",
        "scheduled_date",
        "caregiver",
        "total_amount",
    ]
    list_filter = ["status", "service__category", "scheduled_date"]
    search_fields = [
        "id",
        "patient__email",
        "patient__first_name",
        "caregiver__email",
        "caregiver__first_name",
        "city",
    ]
    autocomplete_fields = ["patient", "caregiver", "service"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "scheduled_date"
    inlines = [CaregiverAssignmentInline, BookingStatusHistoryInline]
    actions = [export_bookings_csv, mark_bookings_completed, assign_available_caregiver]
    list_per_page = 25
    show_full_result_count = False


@admin.register(BookingStatusHistory)
class BookingStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ["booking", "old_status", "new_status", "changed_by", "timestamp"]
    list_filter = ["new_status"]
    search_fields = ["booking__id"]
    readonly_fields = ["booking", "old_status", "new_status", "changed_by", "note", "timestamp"]
    list_per_page = 25


@admin.register(CaregiverAssignment)
class CaregiverAssignmentAdmin(admin.ModelAdmin):
    list_display = ["booking", "caregiver", "assigned_at", "estimated_arrival", "actual_arrival"]
    search_fields = ["caregiver__email", "caregiver__first_name"]
    readonly_fields = ["assigned_at"]
    list_per_page = 25
