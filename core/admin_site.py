"""
Custom AdminSite for CareNest with dashboard summary.
"""

from django.contrib import admin
from django.db.models import Sum
from django.utils import timezone


class CareNestAdminSite(admin.AdminSite):
    site_header = "CareForYou Healthcare Admin"
    site_title = "CareForYou Admin"
    index_title = "Platform Management"

    def index(self, request, extra_context=None):
        """Override index to add dashboard statistics."""
        from apps.bookings.models import Booking
        from apps.payments.models import Payment
        from apps.users.models import CaregiverProfile, User

        today = timezone.localdate()

        extra_context = extra_context or {}
        extra_context["dashboard"] = {
            "total_patients_today": User.objects.filter(
                role="PATIENT", date_joined__date=today
            ).count(),
            "pending_bookings": Booking.objects.filter(
                status="PENDING"
            ).count(),
            "unverified_caregivers": CaregiverProfile.objects.filter(
                is_verified=False, is_active=True
            ).count(),
            "revenue_today": Payment.objects.filter(
                status="PAID", paid_at__date=today
            ).aggregate(total=Sum("amount"))["total"]
            or 0,
        }

        return super().index(request, extra_context=extra_context)


# Instantiate custom admin site
carenest_admin = CareNestAdminSite(name="carenest_admin")
