"""
Base models for the CareNest project.
All app models should inherit from BaseModel.
"""

import uuid

from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model with UUID primary key and timestamp fields.
    All project models should inherit from this.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def soft_delete(self):
        """Soft delete by setting is_active to False."""
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])

    def restore(self):
        """Restore a soft-deleted record."""
        self.is_active = True
        self.save(update_fields=["is_active", "updated_at"])


class ActiveManager(models.Manager):
    """Manager that returns only active records."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
