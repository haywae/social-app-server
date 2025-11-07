import re
from sqlalchemy.orm import Session
from datetime import date
from app.models import User
from app.exceptions import UserAlreadyExistsError, InvalidEmailFormatError
from app.services.account_management.email_change_service import send_account_verification_email_service
from utils.app_utils import validate_email, validate_password, PASSWORD_ERROR_STRING

def register_new_user(session: Session, username: str, email: str, 
    password: str, date_of_birth, country: str, display_name: str
) -> User:
    """
    Handles the business logic of registering a new user.
    1. Validates input.
    2. Checks for existing users.
    3. Creates the new user.
    """

    # 1. --- Input Sanitation ---
    if username:
        username = username.strip()
    if email:
        email = email.strip()
    if display_name:
        display_name = display_name.strip()

    # 2. --- Input Validation ---
    if not all([username, email, password, date_of_birth, country, display_name]):
        raise ValueError("Missing required fields for user registration.")
    
    # 3. --- Age Verification Logic ---
    today = date.today()
    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    if age < 18:
        raise ValueError("You must be at least 18 years old to register.")
    
    if not validate_email(email):
        raise InvalidEmailFormatError("Invalid email format.")
    
    if not validate_password(password):
        raise ValueError(PASSWORD_ERROR_STRING)

    # 2. --- Business Logic: Check for duplicates ---
    if User.get_by_identifier(session, identifier=username) or \
       User.get_by_identifier(session, identifier=email):
        raise UserAlreadyExistsError("A user with this username or email already exists.")
    
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")

        
    # 3. --- Orchestration: Call the model's core create method ---
    new_user = User.create_user(
        session=session,
        username=username,
        email=email,
        password=password,
        date_of_birth=date_of_birth,
        country=country,
        display_name=display_name
    )
    session.flush()  # Ensure the user is created before proceeding

    # 4. --- Send Verification Email ---
    send_account_verification_email_service(session=session, user=new_user)
    return new_user
