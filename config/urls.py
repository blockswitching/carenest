"""
URL configuration for CareNest project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from core.admin_site import carenest_admin

# Register all app admin classes with custom site
from apps.bookings.admin import *  # noqa: F401, F403
from apps.health_records.admin import *  # noqa: F401, F403
from apps.notifications.admin import *  # noqa: F401, F403
from apps.payments.admin import *  # noqa: F401, F403
from apps.services.admin import *  # noqa: F401, F403
from apps.users.admin import *  # noqa: F401, F403


def health_check(request):
    """API health check endpoint."""
    return JsonResponse({"status": "ok", "version": "1.0.0"})


urlpatterns = [
    # Admin (custom site with dashboard)
    path("admin/", admin.site.urls),
    # Authentication
    path("api/v1/auth/", include("apps.users.urls.auth_urls")),
    # API v1
    path("api/v1/", include("apps.users.urls.api_urls")),
    path("api/v1/", include("apps.services.urls")),
    path("api/v1/", include("apps.bookings.urls")),
    path("api/v1/", include("apps.health_records.urls")),
    path("api/v1/", include("apps.payments.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    # API Health Check
    path("api/health/", health_check, name="health-check"),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

# Admin branding (default admin site)
admin.site.site_header = "CareForYou Healthcare Admin"
admin.site.site_title = "CareForYou Admin"
admin.site.index_title = "Platform Management"

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug toolbar
    try:
        import debug_toolbar

        urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    except ImportError:
        pass
