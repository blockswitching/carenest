"""
Family dashboard view.
GET /api/v1/family/dashboard/ — linked patient's today's vitals, active bookings, medication due.
"""

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


@extend_schema(tags=["Bookings"])
class FamilyDashboardView(APIView):
    """
    GET /api/v1/family/dashboard/
    Returns a summary for the patient:
    - Today's vitals (latest health record)
    - Active bookings
    - Medications due today
    For caregivers: shows data for their assigned patients.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Family dashboard",
        description="Get patient's dashboard: today's vitals, active bookings, "
        "and medications due. Caregivers see data for their assigned patients.",
    )
    def get(self, request):
        user = request.user
        today = timezone.localdate()

        if user.role == "PATIENT":
            return Response(self._get_patient_dashboard(user, today))
        elif user.role in ["CAREGIVER", "NURSE"]:
            return Response(self._get_caregiver_dashboard(user, today))
        elif user.role == "ADMIN" or user.is_staff:
            # Admin can pass ?patient_id= query param
            patient_id = request.query_params.get("patient_id")
            if patient_id:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    patient = User.objects.get(id=patient_id, role="PATIENT")
                    return Response(self._get_patient_dashboard(patient, today))
                except User.DoesNotExist:
                    return Response({"detail": "Patient not found."}, status=404)
            return Response({"detail": "Provide ?patient_id= for admin dashboard."}, status=400)

        return Response({"detail": "Unauthorized role."}, status=403)

    def _get_patient_dashboard(self, patient, today):
        """Build dashboard data for a single patient."""
        from apps.bookings.models import Booking
        from apps.bookings.serializers import BookingListSerializer
        from apps.health_records.models import HealthRecord, MedicationReminder

        # Today's vitals (latest record)
        latest_vitals = HealthRecord.objects.filter(
            patient=patient, recorded_at__date=today
        ).order_by("-recorded_at").first()

        vitals_data = None
        if latest_vitals:
            vitals_data = {
                "blood_pressure": f"{latest_vitals.blood_pressure_systolic}/{latest_vitals.blood_pressure_diastolic}"
                if latest_vitals.blood_pressure_systolic
                else None,
                "heart_rate": str(latest_vitals.heart_rate) if latest_vitals.heart_rate else None,
                "temperature": str(latest_vitals.temperature) if latest_vitals.temperature else None,
                "spo2": str(latest_vitals.spo2) if latest_vitals.spo2 else None,
                "blood_sugar": str(latest_vitals.blood_sugar) if latest_vitals.blood_sugar else None,
                "weight": str(latest_vitals.weight) if latest_vitals.weight else None,
                "recorded_at": latest_vitals.recorded_at.isoformat(),
            }

        # Active bookings
        active_bookings = Booking.objects.filter(
            patient=patient,
            status__in=["PENDING", "CONFIRMED", "CAREGIVER_ASSIGNED", "IN_PROGRESS"],
        ).select_related("service", "caregiver").order_by("scheduled_date", "scheduled_time")[:5]

        # Medications due today
        medications_due = MedicationReminder.objects.filter(
            patient=patient,
            is_active=True,
            start_date__lte=today,
        ).filter(
            # Not expired
            end_date__isnull=True,
        ) | MedicationReminder.objects.filter(
            patient=patient,
            is_active=True,
            start_date__lte=today,
            end_date__gte=today,
        )

        medications_data = [
            {
                "id": str(med.id),
                "medicine_name": med.medicine_name,
                "dosage": med.dosage,
                "frequency": med.frequency,
                "reminder_time": med.reminder_time.isoformat(),
            }
            for med in medications_due.distinct()[:10]
        ]

        return {
            "patient_name": patient.full_name,
            "patient_id": str(patient.id),
            "today": today.isoformat(),
            "vitals_today": vitals_data,
            "active_bookings": BookingListSerializer(active_bookings, many=True).data,
            "medications_due": medications_data,
            "deep_link_base": "carenest://booking/",
        }

    def _get_caregiver_dashboard(self, caregiver, today):
        """Build dashboard for caregiver showing their assigned patients' data."""
        from apps.bookings.models import Booking
        from apps.bookings.serializers import BookingListSerializer

        # Active assignments for today
        today_bookings = Booking.objects.filter(
            caregiver=caregiver,
            status__in=["CAREGIVER_ASSIGNED", "IN_PROGRESS"],
            scheduled_date=today,
        ).select_related("patient", "service").order_by("scheduled_time")

        # All active assignments
        active_bookings = Booking.objects.filter(
            caregiver=caregiver,
            status__in=["CAREGIVER_ASSIGNED", "IN_PROGRESS"],
        ).select_related("patient", "service").order_by("scheduled_date", "scheduled_time")[:10]

        return {
            "caregiver_name": caregiver.full_name,
            "today": today.isoformat(),
            "today_bookings": BookingListSerializer(today_bookings, many=True).data,
            "active_bookings": BookingListSerializer(active_bookings, many=True).data,
            "total_today": today_bookings.count(),
        }
