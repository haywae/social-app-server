from sqlalchemy.orm import Session
from datetime import date

from app.models import User
from app.exceptions import UserNotFoundError


def complete_user_onboarding(session: Session, user_id: int, onboarding_data: dict) -> User:
    """
    Completes the onboarding for a new user by adding missing
    required data (DOB, country).
    Peculiar to google sign ins
    """
    user = session.get(User, user_id)
    if not user:
        raise UserNotFoundError("User not found.")

    dob_str = onboarding_data.get('dateOfBirth')
    country = onboarding_data.get('country')

    if not all([dob_str, country]):
        raise ValueError("Date of birth and country are required.")

    date_of_birth = date.fromisoformat(dob_str)

    # ---> Age Verification Logic (from register_service) <---
    today = date.today()
    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    if age < 18:
        raise ValueError("You must be at least 18 years old to register.")

    # ---> Update the User Record <---
    user.date_of_birth = date_of_birth
    user.country = country
    
    # Return the updated user
    return user