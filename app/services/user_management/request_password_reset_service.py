import re
import os
from urllib.parse import quote
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.orm import Session
from flask import current_app

from app.models import User
from app.exceptions import InvalidEmailFormatError
from utils.app_utils.email_utils import send_password_reset_email
from utils.app_utils import validate_email

# This service layer orchestrates the password reset process.

def request_password_reset(session: Session, email: str):
    """
    Handles the business logic for a password reset request.
    1. Validates the email format.
    2. Finds the user (but does not fail if not found, for security).
    3. If user exists, generates a token and triggers an email.
    """

    if email:
        email = email.strip()

    # 1. --- Input Validation ---
    if not email or not validate_email(email):
        raise InvalidEmailFormatError("Invalid email format provided.")

    # 2. --- Find User ---
    user = User.get_by_identifier(session, identifier=email)

    # 3. --- Generate Token and Send Email (if user exists) ---
    # SECURITY: To prevent user enumeration, we don't raise an error if the user
    # is not found. The function simply completes without sending an email.
    if user:
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token_data = (user.id, user.hashed_password)
        token = serializer.dumps(token_data, salt='password-reset-salt')
        
        client_domain = os.getenv('CLIENT_DOMAIN', 'http://localhost:5173')
        reset_url = f"{client_domain}/reset-password?token={quote(token)}"
        
        # 4. --- Delegate Email Sending ---
        # The service layer calls the dedicated email utility.
        send_password_reset_email(recipient_email=user.email, reset_url=reset_url)

    # The function returns nothing; success is implied if no exceptions are raised.
    return True

