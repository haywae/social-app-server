from sqlalchemy.orm import Session
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from flask import current_app

from app.models import User
from app.exceptions import UserNotFoundError, InvalidTokenError, TokenExpiredError
from utils.model_utils import UserStatus 

def verify_email_with_token(session: Session, token: str, max_age: int = 86400) -> User:
    """
    Handles the business logic for verifying a user's email via a token.
    
    1. Validates the token's signature and expiration.
    2. Finds the user associated with the token.
    3. Activates the user's account.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    
    # 1. --- Validate Token ---
    try:
        # The token is valid for 24 hours (86400 seconds)
        payload = serializer.loads(token, salt='account-verification-salt', max_age=max_age)
        user_id = payload['user_id']
    except SignatureExpired:
        raise TokenExpiredError("The verification link has expired. Please request a new one.")
    except (BadTimeSignature, KeyError):
        raise InvalidTokenError("The verification link is invalid or has been tampered with.")

    # 2. --- Find User ---
    user = User.get_by_id(session, user_id)
    if not user:
        # This is a rare edge case, but important to handle.
        raise UserNotFoundError("The user associated with this verification link could not be found.")

    if user.is_email_verified:
        raise ValueError("This email address has already been verified.")

    # 3. --- Activate User Account ---
    # This is the step that updates the database columns.
    user.is_email_verified = True
    user.account_status = UserStatus.ACTIVE
    
    return user
