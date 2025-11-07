from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature, BadSignature
from flask import current_app
import os

from sqlalchemy.orm import Session
from app.models import User
from app.exceptions import (
    UserNotFoundError, InvalidCredentialsError, InvalidEmailFormatError,
    UserAlreadyExistsError, TokenExpiredError, InvalidTokenError
)
from utils.app_utils.email_utils import send_verification_email 
from utils.app_utils import validate_email


def request_email_change_service(session: Session, user_id: int, password: str, new_email: str) -> None:
    """
    Handles the first step of changing a user's email address.
    """
    # 1. --- Input Sanitation ---
    # Sanitize the new email address before any validation.
    if new_email:
        new_email = new_email.strip()
    
    # 2. --- Find User & Authenticate ---
    user = session.get(User, user_id)
    if not user:
        raise UserNotFoundError()

    if not user.check_password(password):
        raise InvalidCredentialsError("The password you entered is incorrect.")
    
    # 3. --- Input Validation ---
    if not new_email or not validate_email(new_email):
        raise InvalidEmailFormatError("Invalid email format provided.")

    if new_email.lower() == user.email.lower():
        raise ValueError("The new email address cannot be the same as the current one.")

    # 4. --- Business Logic: Check for duplicates ---
    existing_user = User.get_by_identifier(session, identifier=new_email)
    if existing_user:
        raise UserAlreadyExistsError("This email address is already in use by another account.")

    # 5. --- Generate Token and Send Email ---
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token_payload = {'user_id': user.id, 'new_email': new_email}
    token = serializer.dumps(token_payload, salt='email-change-salt')
    
    client_domain = os.getenv('CLIENT_DOMAIN', 'http://localhost:3000')
    verification_url = f"{client_domain}/confirm-email-change?token={token}"
    
    send_verification_email(
        recipient_email=new_email, 
        verification_url=verification_url,
        subject="Confirm Your New Email Address",
        template_path="confirm_new_email.html"
    )


def confirm_email_change_service(session: Session, token: str) -> User:
    """
    Handles the second step of changing an email address.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    
    try:
        payload = serializer.loads(token, salt='email-change-salt', max_age=3600)
        user_id = payload['user_id']
        new_email = payload['new_email']
    except SignatureExpired:
        raise TokenExpiredError("The email confirmation link has expired.")
    except (BadSignature, KeyError):
        raise InvalidTokenError("The email confirmation link is invalid.")

    user = session.get(User, user_id)
    if not user:
        raise UserNotFoundError()

    user.email = new_email
    user.is_email_verified = False

    send_account_verification_email_service(session=session, user=user)
    return user



def send_account_verification_email_service(session: Session, user: User) -> None:
    """
    Generates a standard verification token and sends it via the email utility.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    
    # Get the user's ID in the token payload
    token_payload = {'user_id': user.id}
    token = serializer.dumps(token_payload, salt='account-verification-salt')
    
    # Construct the URL for the frontend verification page
    client_domain = os.getenv('CLIENT_DOMAIN', 'http://localhost:5173')
    verification_url = f"{client_domain}/verify-email?token={token}"
    
    # Call existing utility with the correct parameters
    send_verification_email(
        recipient_email=user.email, 
        verification_url=verification_url,
        subject="Please Verify Your Email Address",
        template_path="verify_account_email.html" 
    )