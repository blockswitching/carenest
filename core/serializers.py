"""
Shared serializer utilities for the CareNest project.
"""

from rest_framework import serializers


class AbsoluteImageField(serializers.ImageField):
    """
    ImageField that always returns absolute URLs.
    Ensures mobile clients get full URLs instead of relative paths.
    """

    def to_representation(self, value):
        if not value:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(value.url)
        return value.url


class AbsoluteFileField(serializers.FileField):
    """
    FileField that always returns absolute URLs.
    """

    def to_representation(self, value):
        if not value:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(value.url)
        return value.url
