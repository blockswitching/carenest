"""
Views for the bookings app.
Role-based access:
  - Patient: create, view own, cancel own (PENDING/CONFIRMED only)
  - Caregiver: view assigned, update status (IN_PROGRESS/COMPLETED)
  - Admin: full access + assign caregiver
"""

from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.permissions import IsAdminUser

from .models import Booking, CaregiverAssignment
from .serializers import (
    AssignCaregiverSerializer,
    BookingCancelSerializer,
    BookingCreateSerializer,
    BookingListSerializer,
    BookingSerializer,
    TrackingSerializer,
    UpdateLocationSerializer,
    UpdateStatusSerializer,
)

User = get_user_model()


@extend_schema(tags=["Bookings"])
class BookingViewSet(viewsets.ModelViewSet):
    """ViewSet for bookings with role-based access control."""

    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "scheduled_date", "service", "city"]
    search_fields = ["patient__first_name", "caregiver__first_name", "city"]
    ordering_fields = ["scheduled_date", "created_at", "total_amount"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        queryset = Booking.objects.select_related(
            "patient", "caregiver", "service"
        ).prefetch_related("status_history", "assignment")

        if user.role == "ADMIN" or user.is_staff:
            return queryset
        elif user.role == "PATIENT":
            return queryset.filter(patient=user)
        elif user.role in ["CAREGIVER", "NURSE"]:
            return queryset.filter(caregiver=user)
        return Booking.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        if self.action == "list":
            return BookingListSerializer
        return BookingSerializer

    @extend_schema(
        summary="List bookings",
        description="Patients see own bookings, caregivers see assigned, admins see all.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create a booking",
        description="Patient creates a new service booking with address and schedule.",
        request=BookingCreateSerializer,
        responses={201: BookingSerializer},
    )
    def create(self, request, *args, **kwargs):
        if request.user.role != "PATIENT":
            return Response(
                {"detail": "Only patients can create bookings."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Get booking detail",
        description="Retrieve full booking details including status history and assignment.",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Cancel a booking",
        description="Patient cancels a booking. Only allowed for PENDING or CONFIRMED bookings.",
        request=BookingCancelSerializer,
        responses={200: BookingSerializer},
    )
    @action(detail=True, methods=["patch"], url_path="cancel")
    def cancel(self, request, pk=None):
        """Patient cancels a booking (only PENDING or CONFIRMED)."""
        booking = self.get_object()

        if booking.patient != request.user and not (
            request.user.role == "ADMIN" or request.user.is_staff
        ):
            return Response(
                {"detail": "You can only cancel your own bookings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if booking.status not in [Booking.Status.PENDING, Booking.Status.CONFIRMED]:
            return Response(
                {"detail": "Can only cancel bookings in PENDING or CONFIRMED status."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = BookingCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking._status_changed_by = request.user
        booking._status_change_note = serializer.validated_data.get("reason", "Cancelled by patient")
        booking.status = Booking.Status.CANCELLED
        booking.save()

        return Response(BookingSerializer(booking).data)

    @extend_schema(
        summary="Assign caregiver to booking",
        description="Admin assigns a caregiver to a pending/confirmed booking.",
        request=AssignCaregiverSerializer,
        responses={200: BookingSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="assign-caregiver",
        permission_classes=[IsAuthenticated, IsAdminUser],
    )
    def assign_caregiver(self, request, pk=None):
        """Admin assigns a caregiver to a booking."""
        booking = self.get_object()

        if booking.status not in [Booking.Status.PENDING, Booking.Status.CONFIRMED]:
            return Response(
                {"detail": "Can only assign caregiver to PENDING or CONFIRMED bookings."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AssignCaregiverSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        caregiver_id = serializer.validated_data["caregiver_id"]
        estimated_arrival = serializer.validated_data.get("estimated_arrival")

        caregiver = User.objects.get(id=caregiver_id)

        booking.caregiver = caregiver
        booking._status_changed_by = request.user
        booking._status_change_note = f"Caregiver {caregiver.full_name} assigned by admin"
        booking.status = Booking.Status.CAREGIVER_ASSIGNED
        booking.save()

        CaregiverAssignment.objects.update_or_create(
            booking=booking,
            defaults={"caregiver": caregiver, "estimated_arrival": estimated_arrival},
        )

        return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update booking status",
        description="Caregiver updates booking to IN_PROGRESS or COMPLETED.",
        request=UpdateStatusSerializer,
        responses={200: BookingSerializer},
    )
    @action(detail=True, methods=["patch"], url_path="update-status")
    def update_status(self, request, pk=None):
        """Caregiver updates booking status to IN_PROGRESS or COMPLETED."""
        booking = self.get_object()

        if booking.caregiver != request.user and not (
            request.user.role == "ADMIN" or request.user.is_staff
        ):
            return Response(
                {"detail": "Only the assigned caregiver can update status."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UpdateStatusSerializer(
            data=request.data, context={"booking": booking}
        )
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]
        note = serializer.validated_data.get("note", "")

        booking._status_changed_by = request.user
        booking._status_change_note = note
        booking.status = new_status
        booking.save()

        if new_status == Booking.Status.IN_PROGRESS:
            if hasattr(booking, "assignment"):
                booking.assignment.actual_arrival = timezone.now()
                booking.assignment.save(update_fields=["actual_arrival", "updated_at"])

        return Response(BookingSerializer(booking).data)

    @extend_schema(
        summary="Get live tracking",
        description="Get caregiver location/tracking data for a booking.",
        responses={200: TrackingSerializer},
    )
    @action(detail=True, methods=["get"], url_path="tracking")
    def tracking(self, request, pk=None):
        """Get caregiver live tracking data for a booking."""
        booking = self.get_object()

        if not hasattr(booking, "assignment"):
            return Response(
                {"detail": "No caregiver assigned to this booking yet."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TrackingSerializer(booking.assignment)
        return Response(serializer.data)

    @extend_schema(
        summary="Update caregiver location",
        description="Caregiver sends lat/lng for live tracking by the patient.",
        request=UpdateLocationSerializer,
    )
    @action(detail=True, methods=["patch"], url_path="update-location")
    def update_location(self, request, pk=None):
        """Caregiver updates their live location for a booking."""
        from .serializers import UpdateLocationSerializer

        booking = self.get_object()

        if booking.caregiver != request.user and not (
            request.user.role == "ADMIN" or request.user.is_staff
        ):
            return Response(
                {"detail": "Only the assigned caregiver can update location."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not hasattr(booking, "assignment"):
            return Response(
                {"detail": "No assignment found for this booking."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UpdateLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assignment = booking.assignment
        assignment.tracking_data = {
            "lat": str(serializer.validated_data["lat"]),
            "lng": str(serializer.validated_data["lng"]),
            "updated_at": timezone.now().isoformat(),
        }
        assignment.save(update_fields=["tracking_data", "updated_at"])

        return Response({"message": "Location updated.", "tracking_data": assignment.tracking_data})
