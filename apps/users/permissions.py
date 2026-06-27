"""
Custom permissions for the users app.
"""

from rest_framework.permissions import BasePermission


class IsCaregiverOwner(BasePermission):
    """
    Allow access only if the authenticated user owns the caregiver profile.
    Used for caregiver profile edits.
    """

    def has_object_permission(self, request, view, obj):
        # obj is CaregiverProfile
        return obj.user == request.user


class IsAdminUser(BasePermission):
    """
    Allow access only to admin users (role=ADMIN or is_staff=True).
    Used for document verification and admin-only actions.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.role == "ADMIN" or request.user.is_staff)
        )
