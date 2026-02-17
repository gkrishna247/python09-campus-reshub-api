from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re
import datetime

class CustomPasswordValidator:
    def validate(self, password, user=None):
        errors = []
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if not any(char.isupper() for char in password):
            errors.append("Password must contain at least one uppercase letter.")
        if not any(char.islower() for char in password):
            errors.append("Password must contain at least one lowercase letter.")
        if not any(char.isdigit() for char in password):
            errors.append("Password must contain at least one digit.")
        if not any(char in "!@#$%^&*()-_+=[]{}|;:,.<>?/~" for char in password):
            errors.append("Password must contain at least one special character.")
        
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Your password must contain at least 8 characters, "
            "one uppercase letter, one lowercase letter, one digit, "
            "and one special character."
        )

def validate_hourly_alignment(value):
    """
    Validate that a time value is aligned to the hour (minute=0, second=0).
    """
    if value.minute != 0 or value.second != 0:
        raise ValidationError("Time must be aligned to the hour (e.g., 08:00, 09:00).")
