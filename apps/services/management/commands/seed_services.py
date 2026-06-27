"""
Management command to seed service categories and services.
Usage: python manage.py seed_services
"""

from django.core.management.base import BaseCommand

from apps.services.models import Service, ServiceCategory

SEED_DATA = [
    {
        "name": "Home Nursing",
        "description": "Professional nursing care at your doorstep",
        "icon_name": "medical_services",
        "services": [
            {"name": "Injection & IV Drip", "base_price": 500, "duration_minutes": 30},
            {"name": "Wound Dressing", "base_price": 400, "duration_minutes": 30},
            {"name": "Catheter Care", "base_price": 600, "duration_minutes": 45},
            {"name": "Vital Monitoring", "base_price": 350, "duration_minutes": 20},
        ],
    },
    {
        "name": "Physiotherapy",
        "description": "Rehabilitation and physical therapy at home",
        "icon_name": "accessibility_new",
        "services": [
            {"name": "Post-Surgery Rehab", "base_price": 800, "duration_minutes": 60},
            {"name": "Stroke Recovery", "base_price": 900, "duration_minutes": 60},
            {"name": "Joint Pain Management", "base_price": 700, "duration_minutes": 45},
            {"name": "Spine Therapy", "base_price": 750, "duration_minutes": 45},
        ],
    },
    {
        "name": "Elder Care",
        "description": "Dedicated care and companionship for seniors",
        "icon_name": "elderly",
        "services": [
            {"name": "Daily Assistance (4 hrs)", "base_price": 600, "duration_minutes": 240},
            {"name": "24-Hour Care", "base_price": 2500, "duration_minutes": 1440},
            {"name": "Companionship Visit", "base_price": 400, "duration_minutes": 120},
        ],
    },
    {
        "name": "Post-Hospital Care",
        "description": "Recovery support after hospital discharge",
        "icon_name": "local_hospital",
        "services": [
            {"name": "Post-Surgical Care", "base_price": 1200, "duration_minutes": 120},
            {"name": "ICU Recovery Support", "base_price": 1500, "duration_minutes": 180},
            {"name": "Cancer Care Support", "base_price": 1400, "duration_minutes": 120},
        ],
    },
    {
        "name": "Lab Tests",
        "description": "Home sample collection for diagnostic tests",
        "icon_name": "science",
        "services": [
            {"name": "Blood Test (Home Collection)", "base_price": 300, "duration_minutes": 15},
            {"name": "Full Body Checkup", "base_price": 1500, "duration_minutes": 30},
            {"name": "COVID-19 RT-PCR", "base_price": 500, "duration_minutes": 15},
        ],
    },
    {
        "name": "Medicine Delivery",
        "description": "Doorstep delivery of prescribed medicines",
        "icon_name": "local_pharmacy",
        "services": [
            {"name": "Standard Delivery", "base_price": 50, "duration_minutes": 60},
            {"name": "Express Delivery", "base_price": 100, "duration_minutes": 30},
        ],
    },
]


class Command(BaseCommand):
    help = "Seed service categories and services with initial data"

    def handle(self, *args, **options):
        created_categories = 0
        created_services = 0

        for category_data in SEED_DATA:
            services_data = category_data.pop("services")
            category, created = ServiceCategory.objects.get_or_create(
                name=category_data["name"],
                defaults=category_data,
            )
            if created:
                created_categories += 1
                self.stdout.write(f"  Created category: {category.name}")
            else:
                self.stdout.write(f"  Category exists: {category.name}")

            for service_data in services_data:
                service, svc_created = Service.objects.get_or_create(
                    name=service_data["name"],
                    category=category,
                    defaults=service_data,
                )
                if svc_created:
                    created_services += 1

            # Restore for idempotency
            category_data["services"] = services_data

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! Created {created_categories} categories and {created_services} services."
            )
        )
