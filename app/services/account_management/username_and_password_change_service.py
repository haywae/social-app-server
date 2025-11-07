from sqlalchemy.orm import Session
from app.models import User
from app.exceptions import (
    UserNotFoundError, InvalidCredentialsError, 
    UserAlreadyExistsError
)
from utils.app_utils import validate_password, PASSWORD_ERROR_STRING

def change_username_service(session: Session, user_id: int, password: str, new_username: str) -> User:
    """
    Handles the business logic for changing a user's username.
    """
    # --- 1. Input Sanitation ---
    if new_username:
        new_username = new_username.strip()
    
    # --- 2. Find User & Authenticate ---
    user = session.get(User, user_id)
    if not user:
        raise UserNotFoundError()

    if not user.check_password(password):
        raise InvalidCredentialsError("The password you entered is incorrect.")
    
    # --- 3. Validation ---
    if not new_username:
        raise ValueError("New username cannot be empty.")

    if new_username.lower() == user.username.lower():
        raise ValueError("The new username cannot be the same as the current one.")
    
    existing_user = User.get_by_identifier(session, identifier=new_username)
    if existing_user:
        raise UserAlreadyExistsError("This username is already taken.")

    user.username = new_username
    return user

def change_password_service(session: Session, user_id: int, old_password: str, new_password: str) -> bool:
    """
    Handles the business logic for changing a logged-in user's password.

    This includes:
    1. Finding the user.
    2. Verifying their current (old) password.
    3. Setting the new password.
    """
    user = session.get(User, user_id)
    if not user:
        raise UserNotFoundError("User not found.")

    # Security Check 1: Verify the user's current password.
    if not user.check_password(old_password):
        raise InvalidCredentialsError("The current password you entered is incorrect.")

    # Security Check 2: Ensure the new password is not the same as the old one.
    if old_password == new_password:
        raise ValueError("The new password cannot be the same as the old password.")
    
    # Security Check 3: Password Complexity Validation
    if not validate_password(new_password):
        raise ValueError(PASSWORD_ERROR_STRING)

    # Delegate the final password update to the secure model method.
    user.set_password(new_password)
    
    return True