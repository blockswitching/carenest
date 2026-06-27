"""
Views for the users app.
"""

from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import CaregiverDocument, CaregiverProfile
from .permissions import IsAdminUser, IsCaregiverOwner
from .serializers import (
    CaregiverDetailSerializer,
    CaregiverDocumentUploadSerializer,
    CaregiverListSerializer,
    CaregiverProfileUpdateSerializer,
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
    RegistrationSerializer,
    UserProfileUpdateSerializer,
    UserSerializer,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Auth Views
# ---------------------------------------------------------------------------


@extend_schema(
    tags=["Authentication"],
    summary="Register a new user",
    description="Create a new user account with email, password, name, and role selection. "
    "Phone number must be in Indian format (+91XXXXXXXXXX).",
    responses={201: UserSerializer},
)
class RegisterView(generics.CreateAPIView):
    """POST /api/v1/auth/register/ — Register a new user with role selection."""

    queryset = User.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "User registered successfully.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Authentication"],
    summary="Login with email and password",
    description="Authenticate with email/password and receive JWT access and refresh tokens.",
)
class LoginView(TokenObtainPairView):
    """POST /api/v1/auth/login/ — JWT login endpoint."""

    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


@extend_schema(
    tags=["Authentication"],
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access token.",
)
class RefreshTokenView(TokenRefreshView):
    """POST /api/v1/auth/token/refresh/ — Refresh an expired access token."""

    permission_classes = [AllowAny]


@extend_schema(
    tags=["Authentication"],
    summary="Logout",
    description="Blacklist the refresh token to invalidate the session.",
)
class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — Logout by blacklisting the refresh token."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Successfully logged out."},
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# User Profile Views
# ---------------------------------------------------------------------------


@extend_schema(tags=["Users"])
class UserMeView(generics.RetrieveUpdateAPIView):
    """
    GET/PUT /api/v1/users/me/
    Retrieve or update the authenticated user's profile.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileUpdateSerializer

    @extend_schema(summary="Get own profile", description="Retrieve the authenticated user's full profile.")
    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(summary="Update own profile", description="Update profile fields (name, phone, address, etc).")
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(summary="Partially update own profile")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_object(self):
        return self.request.user.profile

    def retrieve(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Caregiver Views
# ---------------------------------------------------------------------------


@extend_schema(tags=["Caregivers"])
class CaregiverViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Caregiver listing and detail endpoints.
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["specialization", "is_verified"]
    search_fields = ["user__first_name", "user__last_name", "bio"]
    ordering_fields = ["rating", "experience_years", "hourly_rate", "created_at"]
    ordering = ["-rating"]

    def get_queryset(self):
        queryset = CaregiverProfile.objects.filter(
            is_active=True
        ).select_related("user", "user__profile").prefetch_related("documents")

        city = self.request.query_params.get("city")
        if city:
            queryset = queryset.filter(user__profile__city__icontains=city)

        availability = self.request.query_params.get("availability")
        if availability:
            queryset = queryset.filter(availability_days__contains=availability.upper())

        if self.action == "list":
            queryset = queryset.filter(is_verified=True)

        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CaregiverDetailSerializer
        return CaregiverListSerializer

    @extend_schema(
        summary="List verified caregivers",
        description="List all verified caregivers. Filter by specialization, city, or availability day.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Get caregiver detail",
        description="Retrieve full caregiver profile including documents and reviews.",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Upload verification document",
        description="Upload a verification document (ID proof, certificate, or police clearance) for a caregiver.",
        request=CaregiverDocumentUploadSerializer,
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="upload-document",
        permission_classes=[IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_document(self, request, pk=None):
        """Upload a verification document for a caregiver."""
        caregiver_profile = self.get_object()

        if caregiver_profile.user != request.user:
            return Response(
                {"detail": "You can only upload documents for your own profile."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CaregiverDocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(caregiver=caregiver_profile)
        return Response(
            {"message": "Document uploaded successfully.", "document": serializer.data},
            status=status.HTTP_201_CREATED,
        )
