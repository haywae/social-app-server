from flask import request, current_app, make_response, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, unset_jwt_cookies

from app.services import update_user_settings_service, delete_user_service
from app.exceptions import UserNotFoundError, InvalidCredentialsError
from app.extensions import db
from app.models import User # Needed for get() method

# Helper function to serialize the settings data for the frontend.
def serialize_user_settings(user: User) -> dict:
    return {
        "displayName": user.display_name,
        "bio": user.bio,
        "avatarUrl": user.profile_picture_url,
        "country": user.country,
        "notificationPreferences": user.notification_preferences or {} # Default to empty dict
    }

class UserSettingsResource(Resource):
    """
    API Resource for fetching and updating the current user's settings.
    """
    @jwt_required()
    def get(self):
        """Processes a GET request to fetch the current user's settings."""
        try:
            user_id = int(get_jwt_identity())
            user = db.session.get(User, user_id)
            if not user:
                return {'message': 'User not found'}, 404
            
            return serialize_user_settings(user), 200
        except Exception as e:
            current_app.logger.error(f"Error fetching settings: {e}", exc_info=True)
            return {'message': 'An error occurred while fetching settings.'}, 500


    @jwt_required()
    def put(self):
        """Processes a PUT request to update the user's settings."""
        data = request.get_json()
        if not data:
            return {'message': 'No input data provided'}, 400

        try:
            user_id = int(get_jwt_identity())

            # Map frontend camelCase keys to
            # backend snake_case model keys
            JSON_TO_MODEL_MAP = {
                "displayName": "display_name",
                "bio": "bio",
                "avatarUrl": "profile_picture_url",
                "country": "country"
            }

            service_data = {}

            # 1. Transform and filter profile fields
            for json_key, model_key in JSON_TO_MODEL_MAP.items():
                if json_key in data:
                    service_data[model_key] = data[json_key]

            # 2. Pass through non-mapped fields like JSONB objects
            if "notification_preferences" in data:
                service_data["notification_preferences"] = data["notification_preferences"]
            
            # Delegate all business logic to the service layer.
            updated_user = update_user_settings_service(
                session=db.session,
                user_id=user_id,
                settings_data=service_data
            )
            
            db.session.commit()
            
            return {'message': 'Settings updated successfully', 'settings': serialize_user_settings(updated_user)}, 200

        except UserNotFoundError as e:
            db.session.rollback()
            return {'message': str(e)}, 404
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating settings: {e}", exc_info=True)
            return {'message': 'An error occurred while updating settings.'}, 500


    @jwt_required()
    def delete(self):
        """
        Processes a DELETE request to remove the current user's account.
        """
        data = request.get_json()
        if not data or 'password' not in data:
            return {'message': 'Password is required to delete your account.'}, 400

        try:
            user_id = int(get_jwt_identity())
            
            success = delete_user_service(
                session=db.session,
                user_id=user_id,
                password=data.get('password')
            )
            
            if success:
                db.session.commit()
                response = make_response(jsonify({'message': 'Your account has been successfully deleted.'}), 200)
                unset_jwt_cookies(response)
                return response
        except InvalidCredentialsError as e:
            db.session.rollback()
            return {'message': str(e)}, 401
        except UserNotFoundError as e:
            db.session.rollback()
            return {'message': str(e)}, 404
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting user {user_id}: {e}", exc_info=True)
            return {'message': 'An error occurred while deleting your account.'}, 500
