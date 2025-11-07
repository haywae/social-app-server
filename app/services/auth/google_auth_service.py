from flask import current_app
from sqlalchemy.orm import Session
import requests
import google.oauth2.id_token
from google.auth.transport import requests as google_requests
from datetime import datetime
from flask_jwt_extended import create_access_token, create_refresh_token
from app.models import User
from app.exceptions import InvalidCredentialsError
from utils.app_utils import TokenUtil
from utils.model_utils import UserStatus

def login_or_register_google_user(session: Session, code: str) -> dict:
    """
    Handles the business logic of logging in or registering a user via Google.
    1. Exchanges the one-time 'code' for Google's tokens.
    2. Verifies the 'id_token' from Google to get user info.
    3. Finds the user by email or creates a new user if they don't exist.
    4. Generates and returns this app's own auth tokens (JWTs, CSRF).
    """
    try:
        # 1. --- Exchange code for tokens ---
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'code': code,
            'client_id': current_app.config['GOOGLE_CLIENT_ID'],
            'client_secret': current_app.config['GOOGLE_CLIENT_SECRET'],
            'redirect_uri': current_app.config['GOOGLE_REDIRECT_URI'], # Should be 'postmessage'
            'grant_type': 'authorization_code'
        }
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()  # Raise an exception for bad status codes
        
        google_tokens = token_response.json()
        id_token_jwt = google_tokens['id_token']
        
        # 2. --- Verify the ID Token ---
        id_info = google.oauth2.id_token.verify_oauth2_token(
            id_token_jwt, 
            google_requests.Request(), 
            current_app.config['GOOGLE_CLIENT_ID']
        )

        email = id_info['email']
        
        # 3. --- Find or Create User ---
        user = session.query(User).filter_by(email=email).first()

        if not user:
            # User doesn't exist, create a new one
            # You might want to generate a more unique username
            username = email.split('@')[0] 
            
            # Check if username is taken and append numbers if it is
            base_username = username
            counter = 1
            while session.query(User).filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1

            user = User(
                email=email,
                username=username,
                display_name=id_info.get('name', 'New User'),
                profile_picture_url=id_info.get('picture', None),
                google_id=id_info['sub'],
                is_email_verified=True,  # Email is verified by Google
                account_status=UserStatus.ACTIVE # Account status is active after being verified
            )
            # We don't set a password, they will log in via Google
            session.add(user)
            # We must flush to get the user.id for token creation
            session.flush() 
        
        # 4. --- Generate this app's tokens (copied from login_service.py) ---
        token_util = TokenUtil() 
        secret_key = current_app.config['JWT_SECRET_KEY'] 

        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        csrf_values = token_util.generate_csrf_values(access_token=access_token, refresh_token=refresh_token)

        access_exp_time = token_util.get_token_expiry_unix(access_token, secret_key=secret_key)
        
        # 5. --- Return all necessary data to the API layer ---
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "csrf_access_token": csrf_values['csrf_access_token'],
            "csrf_refresh_token": csrf_values['csrf_refresh_token'],
            "access_token_exp": access_exp_time,
        }

    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"Google token exchange failed: {e}")
        raise InvalidCredentialsError("Failed to authenticate with Google.")
    except ValueError as e:
        # This catches errors from id_token.verify_oauth2_token
        current_app.logger.error(f"Google ID token verification failed: {e}")
        raise InvalidCredentialsError("Invalid Google token.")
    except Exception as e:
        current_app.logger.error(f"Unexpected Google auth error: {e}")
        raise