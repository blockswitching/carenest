"""
Views for the health_records app.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import HealthRecord, HealthReport, MedicationReminder
from .serializers import (
    HealthRecordCreateSerializer,
    HealthRecordSerializer,
    HealthReportSerializer,
    MedicationReminderSerializer,
)


@extend_schema(tags=["Health Records"])
class HealthRecordViewSet(viewsets.ModelViewSet):
    """
    GET/POST /api/v1/health/records/
    Patient or caregiver creates/views vitals.
    """

    permission_classes = [IsAuthenticated]
    filterset_fields = ["patient", "booking"]
    ordering_fields = ["recorded_at", "created_at"]
    ordering = ["-recorded_at"]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN" or user.is_staff:
            return HealthRecord.objects.all().select_related("patient", "recorded_by")
        elif user.role == "PATIENT":
            return HealthRecord.objects.filter(patient=user).select_related("recorded_by")
        elif user.role in ["CAREGIVER", "NURSE"]:
            return HealthRecord.objects.filter(recorded_by=user).select_related("patient")
        return HealthRecord.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return HealthRecordCreateSerializer
        return HealthRecordSerializer

    @extend_schema(summary="List health records", description="View vitals. Role-filtered.")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Record vitals", description="Patient or caregiver records vital signs.")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user
        kwargs = {}
        if user.role in ["CAREGIVER", "NURSE"]:
            kwargs["recorded_by"] = user
        elif user.role == "PATIENT":
            kwargs["patient"] = user
        serializer.save(**kwargs)


@extend_schema(tags=["Health Records"])
class PatientHealthHistoryView(generics.ListAPIView):
    """
    GET /api/v1/health/records/{patient_id}/history/
    Admin/caregiver can view a patient's full health history.
    """

    serializer_class = HealthRecordSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Patient health history",
        description="View full vital signs history for a patient. "
        "Accessible by admin, assigned caregivers, and the patient themselves.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        patient_id = self.kwargs["patient_id"]
        user = self.request.user

        if user.role == "ADMIN" or user.is_staff:
            return HealthRecord.objects.filter(patient_id=patient_id).select_related("patient", "recorded_by")

        if user.role in ["CAREGIVER", "NURSE"]:
            from apps.bookings.models import Booking

            has_assignment = Booking.objects.filter(
                patient_id=patient_id,
                caregiver=user,
                status__in=["CAREGIVER_ASSIGNED", "IN_PROGRESS", "COMPLETED"],
            ).exists()
            if has_assignment:
                return HealthRecord.objects.filter(patient_id=patient_id).select_related("patient", "recorded_by")

        if user.role == "PATIENT" and str(user.id) == str(patient_id):
            return HealthRecord.objects.filter(patient=user).select_related("recorded_by")

        return HealthRecord.objects.none()


@extend_schema(tags=["Health Records"])
class MedicationReminderViewSet(viewsets.ModelViewSet):
    """GET/POST /api/v1/health/medications/ — Medication reminder CRUD."""

    serializer_class = MedicationReminderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["patient", "is_active", "frequency"]
    ordering_fields = ["start_date", "reminder_time"]

    @extend_schema(summary="List medication reminders")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Create medication reminder")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN" or user.is_staff:
            return MedicationReminder.objects.all().select_related("patient")
        elif user.role == "PATIENT":
            return MedicationReminder.objects.filter(patient=user)
        return MedicationReminder.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role == "PATIENT":
            serializer.save(patient=self.request.user)
        else:
            serializer.save()


@extend_schema(tags=["Health Records"])
class HealthReportViewSet(viewsets.ModelViewSet):
    """GET/POST /api/v1/health/reports/ — Upload and list health reports."""

    serializer_class = HealthReportSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["patient"]
    search_fields = ["title"]
    ordering_fields = ["report_date", "created_at"]

    @extend_schema(summary="List health reports")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Upload health report", description="Upload a lab report, prescription, or medical document.")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN" or user.is_staff:
            return HealthReport.objects.all().select_related("patient", "uploaded_by")
        elif user.role == "PATIENT":
            return HealthReport.objects.filter(patient=user).select_related("uploaded_by")
        elif user.role in ["CAREGIVER", "NURSE"]:
            return HealthReport.objects.filter(uploaded_by=user).select_related("patient")
        return HealthReport.objects.none()

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
