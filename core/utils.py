"""
Shared utility functions for the CareNest project.
"""

import re
from datetime import date


def validate_indian_phone(phone: str) -> bool:
    """Validate Indian phone number format (+91XXXXXXXXXX or 10 digits)."""
    pattern = r"^(\+91)?[6-9]\d{9}$"
    return bool(re.match(pattern, phone))


def validate_pincode(pincode: str) -> bool:
    """Validate Indian PIN code (6 digits, first digit non-zero)."""
    pattern = r"^[1-9]\d{5}$"
    return bool(re.match(pattern, pincode))


def calculate_age(birth_date: date) -> int:
    """Calculate age from birth date."""
    today = date.today()
    return (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )


def generate_booking_id() -> str:
    """Generate a unique booking reference ID."""
    import uuid

    return f"CN-{uuid.uuid4().hex[:8].upper()}"
