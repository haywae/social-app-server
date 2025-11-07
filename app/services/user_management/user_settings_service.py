from sqlalchemy.orm import Session
from app.models import User
from app.exceptions import UserNotFoundError, InvalidCredentialsError

# This service layer contains the business logic for updating user settings.

def update_user_settings_service(session: Session, user_id: int, settings_data: dict) -> User:
    """
    Handles the business logic for updating a user's settings.

    This includes:
    1. Finding the user.
    2. Validating and updating allowed profile fields.
    3. Updating notification preferences.
    """
    # 1. --- Find the User ---
    user = session.get(User, user_id)
    if not user:
        raise UserNotFoundError("User not found.")

    # 2. --- Define and Update Allowed Fields ---
    # The service layer defines which fields are safe for a user to update.
    allowed_profile_fields = {
        "display_name", 
        "bio", 
        "profile_picture_url", 
        "country"
    }

    fields_to_strip = {"display_name", "bio", "profile_picture_url"}

    profile_update_data = {}
    for key in allowed_profile_fields:
        if key in settings_data:
            value = settings_data[key]
            
            # Sanitize the input if it's a string and in our stripping list
            if key in fields_to_strip and isinstance(value, str):
                value = value.strip()

            profile_update_data[key] = value

    if profile_update_data:
        # Delegate the actual update to the lean model method.
        User.update(session, user_id=user_id, **profile_update_data)

    # 3. --- Update Notification Preferences (JSONB field) ---
    # The service layer handles the logic for updating the JSONB field directly.
    if 'notification_preferences' in settings_data:
        # This will overwrite the entire field with the new settings from the client.
        user.notification_preferences = settings_data['notification_preferences']
        
    return user

def delete_user_service(session: Session, user_id: int, password: str) -> bool:
    """
    Handles the business logic for deleting a user's account.

    This includes:
    1. Finding the user.
    2. Verifying their password as a security measure.
    3. Deleting the user record.
    """
    user = session.get(User, user_id)
    if not user:
        raise UserNotFoundError("User not found.")

    # Security Check: Verify the user's password before allowing deletion.
    if not user.check_password(password):
        raise InvalidCredentialsError("Incorrect password.")

    # Delegate the final deletion to the lean model method.
    return User.delete(session, user_id=user_id)

