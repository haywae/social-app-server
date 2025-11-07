from sqlalchemy.orm import Session
from app.models import User
from app.exceptions import UserNotFoundError
from utils.app_utils import validate_password, PASSWORD_ERROR_STRING
import logging

def create_password(session: Session, user_id: int, new_password: str) -> bool:
    """
    Handles the business logic for creating a password for an
    OAuth-only user who does not have one.
    
    This includes:
    1. Finding the user.
    2. Verifying they do NOT already have a password.
    3. Setting the new password.
    """
    user = session.get(User, user_id)
    if not user:
        raise UserNotFoundError("User not found.")

    # Security Check 1: Ensure the user does not already have a password.
    if user.hashed_password is not None:
        logging.warning(f"User {user_id} attempted to use create-password endpoint but already has a password.")
        raise ValueError("A password is already set for this account. Please use the 'Change Password' feature.")

    # Security Check 2:
    if not validate_password(new_password):
        raise ValueError(PASSWORD_ERROR_STRING)


    # Set the new password
    user.set_password(new_password)
    
    return True