"""
Views for the services app.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Service, ServiceCategory
from .serializers import ServiceCategorySerializer, ServiceListSerializer


@extend_schema(tags=["Services"])
class ServiceListView(generics.ListAPIView):
    """
    GET /api/v1/services/
    List all active services with their category info.
    """

    serializer_class = ServiceListSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["category", "is_available"]
    search_fields = ["name", "description"]
    ordering_fields = ["base_price", "duration_minutes", "name"]

    @extend_schema(
        summary="List all services",
        description="Retrieve all active healthcare services with category information. "
        "Filter by category or availability.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Service.objects.filter(
            is_available=True, category__is_active=True
        ).select_related("category")


@extend_schema(tags=["Services"])
class ServiceCategoryListView(generics.ListAPIView):
    """
    GET /api/v1/services/categories/
    List all active service categories.
    """

    serializer_class = ServiceCategorySerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List service categories",
        description="Retrieve all active service categories with service counts.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return ServiceCategory.objects.filter(is_active=True)
