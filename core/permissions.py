"""
Custom permissions for the CareNest project.
"""

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allow access only to admin users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class IsPatient(BasePermission):
    """Allow access only to patient users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "PATIENT"
        )


class IsCaregiver(BasePermission):
    """Allow access only to caregiver users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "CAREGIVER"
        )


class IsNurse(BasePermission):
    """Allow access only to nurse users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "NURSE"
        )


class IsCareProvider(BasePermission):
    """Allow access to caregivers and nurses."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["CAREGIVER", "NURSE"]
        )


class IsOwnerOrAdmin(BasePermission):
    """Allow access only to the owner of the object or admin."""

    def has_object_permission(self, request, view, obj):
        if request.user.role == "ADMIN":
            return True
        # Check for common owner field names
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "patient"):
            return obj.patient == request.user
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        return False
