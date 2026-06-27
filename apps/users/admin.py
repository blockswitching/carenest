"""
Admin configuration for the users app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import CaregiverDocument, CaregiverProfile, PatientProfile, User, UserProfile


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"


class CaregiverProfileInline(admin.StackedInline):
    model = CaregiverProfile
    can_delete = False
    verbose_name_plural = "Caregiver Profile"
    fk_name = "user"
    extra = 0


class CaregiverDocumentInline(admin.TabularInline):
    model = CaregiverDocument
    extra = 0
    readonly_fields = ["verified_at"]


# ---------------------------------------------------------------------------
# User Admin
# ---------------------------------------------------------------------------


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for the User model."""

    list_display = ["email", "role", "is_active", "date_joined"]
    list_filter = ["role", "is_active", "is_staff"]
    search_fields = ["email", "first_name", "last_name", "profile__phone"]
    ordering = ["-date_joined"]
    list_per_page = 25
    show_full_result_count = False

    def get_inlines(self, request, obj=None):
        """Show CaregiverProfileInline only for CAREGIVER/NURSE users."""
        inlines = [UserProfileInline]
        if obj and obj.role in ["CAREGIVER", "NURSE"]:
            inlines.append(CaregiverProfileInline)
        return inlines

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important Dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


# ---------------------------------------------------------------------------
# Caregiver Profile Admin
# ---------------------------------------------------------------------------


@admin.action(description="Mark selected caregivers as verified")
def mark_as_verified(modeladmin, request, queryset):
    """Custom admin action to mark caregivers as verified."""
    updated = queryset.update(is_verified=True)
    modeladmin.message_user(request, f"{updated} caregiver(s) marked as verified.")


@admin.register(CaregiverProfile)
class CaregiverProfileAdmin(admin.ModelAdmin):
    """Admin for CaregiverProfile with document inline and verification action."""

    list_display = [
        "user",
        "specialization",
        "experience_years",
        "is_verified",
        "rating",
        "hourly_rate",
    ]
    list_filter = ["specialization", "is_verified", "user__profile__city"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
    readonly_fields = ["rating", "total_reviews"]
    inlines = [CaregiverDocumentInline]
    actions = [mark_as_verified]
    list_per_page = 25
    show_full_result_count = False


# ---------------------------------------------------------------------------
# Patient Profile Admin
# ---------------------------------------------------------------------------


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "blood_group", "emergency_contact_name", "insurance_number"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
    list_filter = ["blood_group"]
    list_per_page = 25


# ---------------------------------------------------------------------------
# Caregiver Document Admin
# ---------------------------------------------------------------------------


@admin.register(CaregiverDocument)
class CaregiverDocumentAdmin(admin.ModelAdmin):
    list_display = ["caregiver", "doc_type", "verified_at", "created_at"]
    list_filter = ["doc_type"]
    search_fields = ["caregiver__user__email"]
    list_per_page = 25

    actions = ["verify_documents"]

    @admin.action(description="Verify selected documents")
    def verify_documents(self, request, queryset):
        from django.utils import timezone

        updated = queryset.filter(verified_at__isnull=True).update(
            verified_at=timezone.now()
        )
        self.message_user(request, f"{updated} document(s) verified.")
