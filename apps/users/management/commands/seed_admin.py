"""
Management command to create a superuser from environment variables.
Usage: python manage.py seed_admin
"""

from decouple import config
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Create a superuser from ADMIN_EMAIL and ADMIN_PASSWORD env vars"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            help="Admin email (overrides ADMIN_EMAIL env var)",
        )
        parser.add_argument(
            "--password",
            type=str,
            help="Admin password (overrides ADMIN_PASSWORD env var)",
        )

    def handle(self, *args, **options):
        email = options.get("email") or config("ADMIN_EMAIL", default="admin@carenest.in")
        password = options.get("password") or config("ADMIN_PASSWORD", default="admin123!")
        first_name = config("ADMIN_FIRST_NAME", default="Admin")
        last_name = config("ADMIN_LAST_NAME", default="CareNest")

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"User '{email}' already exists. Skipping."))
            return

        user = User.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        self.stdout.write(
            self.style.SUCCESS(f"Superuser created: {user.email} (role: {user.role})")
        )
