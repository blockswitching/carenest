"""
Serializers for the health_records app.
"""

from rest_framework import serializers

from .models import HealthRecord, HealthReport, MedicationReminder, WoundCareLog


class HealthRecordSerializer(serializers.ModelSerializer):
    """Serializer for health records (vitals)."""

    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    recorded_by_name = serializers.CharField(
        source="recorded_by.full_name", read_only=True, default=""
    )

    class Meta:
        model = HealthRecord
        fields = [
            "id",
            "patient",
            "patient_name",
            "booking",
            "recorded_by",
            "recorded_by_name",
            "blood_pressure_systolic",
            "blood_pressure_diastolic",
            "heart_rate",
            "blood_sugar",
            "temperature",
            "weight",
            "spo2",
            "notes",
            "recorded_at",
            "created_at",
        ]
        read_only_fields = ["id", "recorded_by", "created_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.role in ["CAREGIVER", "NURSE"]:
            validated_data["recorded_by"] = request.user
        return super().create(validated_data)


class HealthRecordCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a health record."""

    class Meta:
        model = HealthRecord
        fields = [
            "patient",
            "booking",
            "blood_pressure_systolic",
            "blood_pressure_diastolic",
            "heart_rate",
            "blood_sugar",
            "temperature",
            "weight",
            "spo2",
            "notes",
            "recorded_at",
        ]


class MedicationReminderSerializer(serializers.ModelSerializer):
    """Serializer for medication reminders."""

    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = MedicationReminder
        fields = [
            "id",
            "patient",
            "patient_name",
            "medicine_name",
            "dosage",
            "frequency",
            "start_date",
            "end_date",
            "reminder_time",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class WoundCareLogSerializer(serializers.ModelSerializer):
    """Serializer for wound care logs."""

    class Meta:
        model = WoundCareLog
        fields = [
            "id",
            "booking",
            "description",
            "photo",
            "severity",
            "next_visit_date",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class HealthReportSerializer(serializers.ModelSerializer):
    """Serializer for health reports."""

    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    uploaded_by_name = serializers.CharField(
        source="uploaded_by.full_name", read_only=True, default=""
    )

    class Meta:
        model = HealthReport
        fields = [
            "id",
            "patient",
            "patient_name",
            "title",
            "report_file",
            "uploaded_by",
            "uploaded_by_name",
            "report_date",
            "created_at",
        ]
        read_only_fields = ["id", "uploaded_by", "created_at"]

    def create(self, validated_data):
        validated_data["uploaded_by"] = self.context["request"].user
        return super().create(validated_data)
