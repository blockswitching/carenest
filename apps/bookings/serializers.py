"""
Serializers for the bookings app.
"""

from rest_framework import serializers

from .models import Booking, BookingStatusHistory, CaregiverAssignment


class BookingStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for booking status history entries."""

    changed_by_name = serializers.CharField(
        source="changed_by.full_name", read_only=True, default=""
    )

    class Meta:
        model = BookingStatusHistory
        fields = [
            "id",
            "old_status",
            "new_status",
            "changed_by",
            "changed_by_name",
            "note",
            "timestamp",
        ]
        read_only_fields = fields


class CaregiverAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for caregiver assignment info."""

    caregiver_name = serializers.CharField(source="caregiver.full_name", read_only=True)

    class Meta:
        model = CaregiverAssignment
        fields = [
            "id",
            "caregiver",
            "caregiver_name",
            "assigned_at",
            "estimated_arrival",
            "actual_arrival",
            "tracking_data",
        ]
        read_only_fields = ["id", "assigned_at"]


class BookingSerializer(serializers.ModelSerializer):
    """Full booking serializer for detail and list views."""

    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    caregiver_name = serializers.CharField(
        source="caregiver.full_name", read_only=True, default=""
    )
    service_name = serializers.CharField(source="service.name", read_only=True)
    status_history = BookingStatusHistorySerializer(many=True, read_only=True)
    assignment = CaregiverAssignmentSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "patient",
            "patient_name",
            "caregiver",
            "caregiver_name",
            "service",
            "service_name",
            "status",
            "scheduled_date",
            "scheduled_time",
            "address",
            "city",
            "pincode",
            "patient_notes",
            "total_amount",
            "assignment",
            "status_history",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "patient",
            "caregiver",
            "status",
            "created_at",
            "updated_at",
        ]


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for patient creating a new booking."""

    class Meta:
        model = Booking
        fields = [
            "service",
            "scheduled_date",
            "scheduled_time",
            "address",
            "city",
            "pincode",
            "patient_notes",
            "total_amount",
        ]

    def create(self, validated_data):
        validated_data["patient"] = self.context["request"].user
        return super().create(validated_data)


class BookingListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for booking list views."""

    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    caregiver_name = serializers.CharField(
        source="caregiver.full_name", read_only=True, default=""
    )
    service_name = serializers.CharField(source="service.name", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "patient_name",
            "caregiver_name",
            "service_name",
            "status",
            "scheduled_date",
            "scheduled_time",
            "city",
            "total_amount",
            "created_at",
        ]


class BookingCancelSerializer(serializers.Serializer):
    """Serializer for cancelling a booking."""

    reason = serializers.CharField(required=False, allow_blank=True, default="")


class AssignCaregiverSerializer(serializers.Serializer):
    """Serializer for admin assigning a caregiver to a booking."""

    caregiver_id = serializers.UUIDField()
    estimated_arrival = serializers.DateTimeField(required=False, allow_null=True)

    def validate_caregiver_id(self, value):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            User.objects.get(id=value, role__in=["CAREGIVER", "NURSE"])
        except User.DoesNotExist:
            raise serializers.ValidationError("Caregiver not found or not a valid caregiver.")
        return value


class UpdateStatusSerializer(serializers.Serializer):
    """Serializer for caregiver updating booking status."""

    status = serializers.ChoiceField(
        choices=[Booking.Status.IN_PROGRESS, Booking.Status.COMPLETED]
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_status(self, value):
        booking = self.context.get("booking")
        if not booking:
            return value

        valid_transitions = {
            Booking.Status.CAREGIVER_ASSIGNED: [Booking.Status.IN_PROGRESS],
            Booking.Status.IN_PROGRESS: [Booking.Status.COMPLETED],
        }
        allowed = valid_transitions.get(booking.status, [])
        if value not in allowed:
            raise serializers.ValidationError(
                f"Cannot transition from '{booking.status}' to '{value}'."
            )
        return value


class UpdateLocationSerializer(serializers.Serializer):
    """Serializer for caregiver updating live location."""

    lat = serializers.DecimalField(max_digits=10, decimal_places=7)
    lng = serializers.DecimalField(max_digits=10, decimal_places=7)


class TrackingSerializer(serializers.ModelSerializer):
    """Serializer for live tracking data."""

    caregiver_name = serializers.CharField(source="caregiver.full_name", read_only=True)

    class Meta:
        model = CaregiverAssignment
        fields = [
            "caregiver_name",
            "assigned_at",
            "estimated_arrival",
            "actual_arrival",
            "tracking_data",
        ]
