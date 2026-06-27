"""
URL patterns for the bookings app.
Mounted at /api/v1/
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .family_views import FamilyDashboardView
from .views import BookingViewSet

router = DefaultRouter()
router.register(r"bookings", BookingViewSet, basename="booking")

urlpatterns = [
    path("", include(router.urls)),
    path("family/dashboard/", FamilyDashboardView.as_view(), name="family-dashboard"),
]
