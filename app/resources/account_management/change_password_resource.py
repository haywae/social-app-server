from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services  import (
    change_password_service,
)
from app.exceptions import (
    UserNotFoundError, InvalidCredentialsError
)
from app.extensions import db



class ChangePasswordResource(Resource):
    """
    API Resource for an authenticated user to change their own password.
    """
    @jwt_required()
    def put(self):
        """
        Processes a PUT request to update the user's password.
        """
        data = request.get_json()
        if not data or 'old_password' not in data or 'new_password' not in data:
            return {'message': 'Both old and new passwords are required.'}, 400

        try:
            user_id = int(get_jwt_identity())
            
            # Delegate all business logic to the service layer
            success = change_password_service(
                session=db.session,
                user_id=user_id,
                old_password=data['old_password'],
                new_password=data['new_password']
            )
            
            if success:
                db.session.commit()
                return {'message': 'Password updated successfully.'}, 200

        except (InvalidCredentialsError, ValueError) as e:
            db.session.rollback()
            # 401 for bad credentials, 400 for other validation errors
            status_code = 401 if isinstance(e, InvalidCredentialsError) else 400
            return {'message': str(e)}, status_code
        except UserNotFoundError as e:
            db.session.rollback()
            return {'message': str(e)}, 404
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error changing password for user {user_id}: {e}", exc_info=True)
            return {'message': 'An unexpected error occurred.'}, 500
