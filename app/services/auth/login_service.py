from flask import current_app
from datetime import datetime
from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy.orm import Session
from app.models import User
from app.exceptions import InvalidCredentialsError
from utils.app_utils import TokenUtil


def login_user(session: Session, login_identifier: str, password: str) -> dict:
    """
    Handles the business logic of logging in a user.
    1. Finds the user by username or email.
    2. Validates the password.
    3. Generates and stores JWT tokens.
    4. Returns a dictionary of user and token data.
    """
    if not login_identifier or not password:
        raise ValueError("Login identifier and password are required.")

    # 1. --- Find User and Validate Password ---
    user = User.get_by_identifier(session, identifier=login_identifier)
    if not user or not user.check_password(password):
        raise InvalidCredentialsError("Invalid username/email or password.")

    # 2. --- Generate Tokens and Token Info ---
    token_util = TokenUtil() 
    secret_key = current_app.config['JWT_SECRET_KEY'] 

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    csrf_values = token_util.generate_csrf_values(access_token=access_token, refresh_token=refresh_token)

    access_exp_time = token_util.get_token_expiry_unix(access_token, secret_key=secret_key)
    refresh_exp_time = token_util.get_token_expiry_unix(refresh_token, secret_key=secret_key)
    refresh_token_jti = token_util.get_token_jti(refresh_token, secret_key=secret_key)

    # 4. --- Return all necessary data to the API layer ---
    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "csrf_access_token": csrf_values['csrf_access_token'],
        "csrf_refresh_token": csrf_values['csrf_refresh_token'],
        "access_token_exp": access_exp_time,
        "refresh_token_exp": refresh_exp_time
    }
