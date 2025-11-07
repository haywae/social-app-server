from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from sqlalchemy.orm import Session
from flask import current_app

from app.models import User
from app.exceptions import UserNotFoundError, InvalidTokenError, TokenExpiredError
from utils.app_utils import validate_password, PASSWORD_ERROR_STRING


def reset_user_password(session: Session, token: str, new_password: str) -> bool:
    """
    Handles the business logic for resetting a user's password.
    1. Validates the password reset token.
    2. Finds the user.
    3. Sets the new password.
    """
    if not new_password and not validate_password(new_password):
        raise ValueError(PASSWORD_ERROR_STRING)

    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    
    try:
        # --- Step 1: Load token WITHOUT max_age to get the contents ---
        # This checks the signature but doesn't fail yet if it's expired.
        # Helpful when a user tries to reuse a link
        user_id, old_hash_from_token = serializer.loads(token, salt='password-reset-salt')
        
        # --- Step 2: Find user and perform the "already used" check first ---
        user = User.get_by_id(session, user_id=user_id)

        if not user or old_hash_from_token != user.hashed_password:
            # If the user doesn't exist or the hash doesn't match, the token is invalid.
            raise InvalidTokenError("Invalid password reset link.")

        # --- Step 3: Now, validate the timestamp as a final check ---
        # If this fails, we know the token was valid but has expired.
        serializer.loads(token, salt='password-reset-salt', max_age=3600)

    except SignatureExpired:
        raise TokenExpiredError("Password reset link has expired.")
    except (BadTimeSignature, ValueError, TypeError):
        raise InvalidTokenError("Invalid password reset link.")

    # If all checks pass, set the new password.
    user.set_password(new_password)
    
    return True


