"""
Custom User model and profile models for CareNest.
Uses AbstractBaseUser with role-based access control.
"""

import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from core.models import BaseModel


class UserManager(BaseUserManager):
    """Custom manager for the User model."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user."""
        if not email:
            raise ValueError("The Email field is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with email as the unique identifier
    and role-based access control.
    """

    class Role(models.TextChoices):
        PATIENT = "PATIENT", "Patient"
        CAREGIVER = "CAREGIVER", "Caregiver"
        NURSE = "NURSE", "Nurse"
        ADMIN = "ADMIN", "Admin"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    email = models.EmailField(unique=True, max_length=255)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PATIENT,
    )

    # Status fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Timestamps
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT

    @property
    def is_caregiver(self):
        return self.role == self.Role.CAREGIVER

    @property
    def is_nurse(self):
        return self.role == self.Role.NURSE

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN


class UserProfile(BaseModel):
    """
    Profile information shared by all users.
    Auto-created via signal when a User is created.
    """

    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=6, blank=True)
    profile_photo = models.ImageField(
        upload_to="profile_photos/", blank=True, null=True
    )
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        blank=True,
    )

    class Meta:
        db_table = "user_profiles"
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"Profile - {self.user.full_name}"


class PatientProfile(BaseModel):
    """Additional profile fields specific to patients."""

    class BloodGroup(models.TextChoices):
        A_POSITIVE = "A+", "A+"
        A_NEGATIVE = "A-", "A-"
        B_POSITIVE = "B+", "B+"
        B_NEGATIVE = "B-", "B-"
        AB_POSITIVE = "AB+", "AB+"
        AB_NEGATIVE = "AB-", "AB-"
        O_POSITIVE = "O+", "O+"
        O_NEGATIVE = "O-", "O-"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile",
        limit_choices_to={"role": "PATIENT"},
    )
    blood_group = models.CharField(
        max_length=5,
        choices=BloodGroup.choices,
        blank=True,
    )
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    medical_history = models.TextField(blank=True)
    insurance_number = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "patient_profiles"
        verbose_name = "Patient Profile"
        verbose_name_plural = "Patient Profiles"

    def __str__(self):
        return f"Patient Profile - {self.user.full_name}"


class CaregiverProfile(BaseModel):
    """Additional profile fields specific to caregivers/nurses."""

    class Specialization(models.TextChoices):
        NURSE = "NURSE", "Nurse"
        PHYSIO = "PHYSIO", "Physiotherapist"
        ATTENDANT = "ATTENDANT", "Attendant"
        ELDER_CARE = "ELDER_CARE", "Elder Care"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="caregiver_profile",
        limit_choices_to={"role__in": ["CAREGIVER", "NURSE"]},
    )
    specialization = models.CharField(
        max_length=20,
        choices=Specialization.choices,
    )
    experience_years = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        help_text="Average rating from 0 to 5",
    )
    total_reviews = models.PositiveIntegerField(default=0)
    availability_days = models.JSONField(
        default=list,
        blank=True,
        help_text="List of available days, e.g. ['MON','TUE','WED']",
    )
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
    )

    class Meta:
        db_table = "caregiver_profiles"
        verbose_name = "Caregiver Profile"
        verbose_name_plural = "Caregiver Profiles"

    def __str__(self):
        return f"Caregiver Profile - {self.user.full_name} ({self.specialization})"


class CaregiverDocument(BaseModel):
    """Verification documents uploaded by caregivers."""

    class DocType(models.TextChoices):
        ID_PROOF = "ID_PROOF", "ID Proof"
        CERTIFICATE = "CERTIFICATE", "Certificate"
        POLICE_CLEARANCE = "POLICE_CLEARANCE", "Police Clearance"

    caregiver = models.ForeignKey(
        CaregiverProfile,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    doc_type = models.CharField(
        max_length=20,
        choices=DocType.choices,
    )
    document = models.FileField(upload_to="caregiver_documents/%Y/%m/")
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "caregiver_documents"
        verbose_name = "Caregiver Document"
        verbose_name_plural = "Caregiver Documents"

    def __str__(self):
        return f"{self.get_doc_type_display()} - {self.caregiver.user.full_name}"

    @property
    def is_verified(self):
        return self.verified_at is not None
