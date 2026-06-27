"""
Models for the services app.
Defines healthcare service categories and services offered on the platform.
"""

from django.db import models

from core.models import BaseModel


class ServiceCategory(BaseModel):
    """Category for healthcare services."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon_name = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon identifier (e.g., Material icon name)",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "service_categories"
        verbose_name = "Service Category"
        verbose_name_plural = "Service Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def service_count(self):
        return self.services.filter(is_available=True).count()


class Service(BaseModel):
    """Healthcare service offered on the platform."""

    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name="services",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.PositiveIntegerField(
        help_text="Estimated duration of service in minutes"
    )
    is_available = models.BooleanField(default=True)

    class Meta:
        db_table = "services"
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} ({self.category.name})"
