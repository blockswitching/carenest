"""
User API URL patterns.
Mounted at /api/v1/
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.users.views import CaregiverViewSet, UserMeView

router = DefaultRouter()
router.register(r"caregivers", CaregiverViewSet, basename="caregiver")

urlpatterns = [
    path("users/me/", UserMeView.as_view(), name="user-me"),
    path("", include(router.urls)),
]
