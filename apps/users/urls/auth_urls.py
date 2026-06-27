"""
Authentication URL patterns.
Mounted at /api/v1/auth/
"""

from django.urls import path

from apps.users.views import LoginView, LogoutView, RefreshTokenView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("token/refresh/", RefreshTokenView.as_view(), name="auth-token-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
]
