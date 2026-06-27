"""
Serializers for the users app.
"""

import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CaregiverDocument, CaregiverProfile, PatientProfile, UserProfile

User = get_user_model()


# ---------------------------------------------------------------------------
# Auth Serializers
# ---------------------------------------------------------------------------


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer that includes user role in the token."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["role"] = user.role
        token["full_name"] = user.full_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with role selection.
    Validates Indian phone number format (+91XXXXXXXXXX).
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone",
            "role",
        ]

    def validate_phone(self, value):
        """Validate Indian phone number format: +91 followed by 10 digits starting with 6-9."""
        if not value:
            return value
        pattern = r"^\+91[6-9]\d{9}$"
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Phone number must be in Indian format: +91XXXXXXXXXX "
                "(10 digits starting with 6-9)."
            )
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        phone = validated_data.pop("phone", "")
        user = User.objects.create_user(**validated_data)
        # Update the auto-created UserProfile with phone if provided
        if phone:
            user.profile.phone = phone
            user.profile.save(update_fields=["phone", "updated_at"])
        return user


class LogoutSerializer(serializers.Serializer):
    """Serializer for logout (token blacklisting)."""

    refresh = serializers.CharField(required=True)

    def validate_refresh(self, value):
        try:
            self.token = RefreshToken(value)
        except Exception:
            raise serializers.ValidationError("Invalid or expired refresh token.")
        return value

    def save(self, **kwargs):
        self.token.blacklist()


# ---------------------------------------------------------------------------
# User & Profile Serializers
# ---------------------------------------------------------------------------


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile (nested inside UserSerializer)."""

    class Meta:
        model = UserProfile
        fields = [
            "phone",
            "address",
            "city",
            "state",
            "pincode",
            "profile_photo",
            "date_of_birth",
            "gender",
        ]


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details including nested profile."""

    full_name = serializers.ReadOnlyField()
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "is_active",
            "date_joined",
            "profile",
        ]
        read_only_fields = ["id", "email", "role", "is_active", "date_joined"]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile (GET/PUT /api/v1/users/me/)."""

    # User fields (flat)
    first_name = serializers.CharField(source="user.first_name", required=False)
    last_name = serializers.CharField(source="user.last_name", required=False)
    email = serializers.EmailField(source="user.email", read_only=True)
    role = serializers.CharField(source="user.role", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "email",
            "first_name",
            "last_name",
            "role",
            "phone",
            "address",
            "city",
            "state",
            "pincode",
            "profile_photo",
            "date_of_birth",
            "gender",
        ]

    def validate_phone(self, value):
        """Validate Indian phone number format."""
        if not value:
            return value
        pattern = r"^\+91[6-9]\d{9}$"
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Phone number must be in Indian format: +91XXXXXXXXXX."
            )
        return value

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        # Update User fields
        user = instance.user
        if "first_name" in user_data:
            user.first_name = user_data["first_name"]
        if "last_name" in user_data:
            user.last_name = user_data["last_name"]
        user.save()
        # Update UserProfile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ---------------------------------------------------------------------------
# Patient Profile Serializer
# ---------------------------------------------------------------------------


class PatientProfileSerializer(serializers.ModelSerializer):
    """Serializer for patient-specific profile data."""

    class Meta:
        model = PatientProfile
        fields = [
            "id",
            "blood_group",
            "emergency_contact_name",
            "emergency_contact_phone",
            "medical_history",
            "insurance_number",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ---------------------------------------------------------------------------
# Caregiver Serializers
# ---------------------------------------------------------------------------


class CaregiverDocumentSerializer(serializers.ModelSerializer):
    """Serializer for caregiver verification documents."""

    is_verified = serializers.ReadOnlyField()

    class Meta:
        model = CaregiverDocument
        fields = [
            "id",
            "doc_type",
            "document",
            "verified_at",
            "is_verified",
            "created_at",
        ]
        read_only_fields = ["id", "verified_at", "created_at"]


class CaregiverListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing verified caregivers."""

    full_name = serializers.CharField(source="user.full_name", read_only=True)
    city = serializers.CharField(source="user.profile.city", read_only=True)
    profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = CaregiverProfile
        fields = [
            "id",
            "full_name",
            "city",
            "profile_photo",
            "specialization",
            "experience_years",
            "rating",
            "total_reviews",
            "hourly_rate",
            "availability_days",
            "is_verified",
        ]

    def get_profile_photo(self, obj):
        photo = obj.user.profile.profile_photo
        if not photo:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(photo.url)
        return photo.url


class CaregiverDetailSerializer(serializers.ModelSerializer):
    """Full serializer for caregiver detail view including documents."""

    full_name = serializers.CharField(source="user.full_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    city = serializers.CharField(source="user.profile.city", read_only=True)
    state = serializers.CharField(source="user.profile.state", read_only=True)
    profile_photo = serializers.ImageField(
        source="user.profile.profile_photo", read_only=True
    )
    phone = serializers.CharField(source="user.profile.phone", read_only=True)
    documents = CaregiverDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = CaregiverProfile
        fields = [
            "id",
            "full_name",
            "email",
            "phone",
            "city",
            "state",
            "profile_photo",
            "specialization",
            "experience_years",
            "bio",
            "is_verified",
            "rating",
            "total_reviews",
            "availability_days",
            "hourly_rate",
            "documents",
            "created_at",
            "updated_at",
        ]


class CaregiverProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for caregivers to update their own profile."""

    class Meta:
        model = CaregiverProfile
        fields = [
            "specialization",
            "experience_years",
            "bio",
            "availability_days",
            "hourly_rate",
        ]


class CaregiverDocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading a caregiver verification document."""

    class Meta:
        model = CaregiverDocument
        fields = ["doc_type", "document"]
