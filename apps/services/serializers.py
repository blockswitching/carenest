"""
Serializers for the services app.
"""

from rest_framework import serializers

from .models import Service, ServiceCategory


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for services."""

    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Service
        fields = [
            "id",
            "category",
            "category_name",
            "name",
            "description",
            "base_price",
            "duration_minutes",
            "is_available",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ServiceCategorySerializer(serializers.ModelSerializer):
    """Serializer for service categories."""

    service_count = serializers.ReadOnlyField()

    class Meta:
        model = ServiceCategory
        fields = [
            "id",
            "name",
            "description",
            "icon_name",
            "is_active",
            "service_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ServiceCategoryDetailSerializer(serializers.ModelSerializer):
    """Category serializer with nested services for list view."""

    services = ServiceSerializer(many=True, read_only=True, source="active_services")
    service_count = serializers.ReadOnlyField()

    class Meta:
        model = ServiceCategory
        fields = [
            "id",
            "name",
            "description",
            "icon_name",
            "is_active",
            "service_count",
            "services",
        ]

    def get_fields(self):
        fields = super().get_fields()
        return fields


class ServiceListSerializer(serializers.ModelSerializer):
    """Service serializer with category info for the flat service list."""

    category_name = serializers.CharField(source="category.name", read_only=True)
    category_id = serializers.UUIDField(source="category.id", read_only=True)

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "description",
            "base_price",
            "duration_minutes",
            "is_available",
            "category_id",
            "category_name",
        ]
