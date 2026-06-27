"""
URL patterns for the health_records app.
Mounted at /api/v1/
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    HealthRecordViewSet,
    HealthReportViewSet,
    MedicationReminderViewSet,
    PatientHealthHistoryView,
)

router = DefaultRouter()
router.register(r"health/records", HealthRecordViewSet, basename="health-record")
router.register(r"health/medications", MedicationReminderViewSet, basename="medication-reminder")
router.register(r"health/reports", HealthReportViewSet, basename="health-report")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "health/records/<uuid:patient_id>/history/",
        PatientHealthHistoryView.as_view(),
        name="patient-health-history",
    ),
]
