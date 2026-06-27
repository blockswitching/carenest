"""
URL patterns for the services app.
Mounted at /api/v1/
"""

from django.urls import path

from .views import ServiceCategoryListView, ServiceListView

urlpatterns = [
    path("services/", ServiceListView.as_view(), name="service-list"),
    path("services/categories/", ServiceCategoryListView.as_view(), name="service-category-list"),
]
