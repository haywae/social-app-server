import re
from password_strength import PasswordPolicy

# --- PASSWORD POLICY ---
# Define your single source of truth for password rules.
password_policy = PasswordPolicy.from_names(
    length=8,
    uppercase=1,
    numbers=1,
    special=1
)

PASSWORD_ERROR_STRING = """
    Password must be at least 8 characters long and contain at least one uppercase letter, one 
    lowercase letter, one number, and one special character.
"""

email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# --- PASSWORD VALIDATION FUNCTION ---
def validate_password(password: str) -> bool:
    """
    Tests a password against the global password policy.
    Returns True if valid, False if invalid.
    """
    return not password_policy.test(password)

# --- EMAIL VALIDATION FUNCTION ---
def validate_email(email: str) -> bool:
    """
    Tests an email against the global regex pattern.
    Returns True if valid, False if invalid.
    """
    return email_pattern.match(email) is not None