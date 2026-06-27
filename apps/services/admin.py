"""
Admin configuration for the services app.
"""

from django.contrib import admin

from .models import Service, ServiceCategory


class ServiceInline(admin.TabularInline):
    """Inline for services within a category."""

    model = Service
    extra = 1
    fields = ["name", "base_price", "duration_minutes", "is_available"]


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    """Admin for ServiceCategory with inline services."""

    list_display = ["name", "service_count", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "description"]
    inlines = [ServiceInline]
    list_per_page = 25

    def service_count(self, obj):
        return obj.services.filter(is_available=True).count()

    service_count.short_description = "Active Services"


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "base_price", "duration_minutes", "is_available"]
    list_filter = ["category", "is_available"]
    search_fields = ["name", "description"]
    list_per_page = 25
