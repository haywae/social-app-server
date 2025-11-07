from flask import request, current_app
from flask_restful import Resource
from itsdangerous import BadSignature

from app.extensions import db
from app.services import reset_user_password
from app.exceptions import UserNotFoundError, InvalidTokenError, TokenExpiredError

class ResetPasswordResource(Resource):
    """
    API Resource for resetting a user's password using a valid token.
    """
    def post(self, token: str):
        """
        Processes a POST request to set a new password.

        Args:
            token (str): The password reset token from the URL.

        Expects a JSON payload with the key "newPassword".

        Returns:
            - 200 OK: If the password was reset successfully.
            - 400 Bad Request: If the token is invalid or the new password is missing.
            - 404 Not Found: If the user associated with the token does not exist.
            - 410 Gone: If the token has expired.
            - 500 Internal Server Error: For unexpected server issues.
        """
        
        data = request.get_json()
        if not data or 'newPassword' not in data:
            return {'message': 'New password is required.'}, 400

        try:
            # Delegate all logic to the service layer.
            success = reset_user_password(
                session=db.session,
                token=token,
                new_password=data.get('newPassword')
            )
            
            if success:
                db.session.commit()
                return {'message': 'Password has been reset successfully.'}, 200

        # The API layer translates service errors into specific HTTP responses.
        except TokenExpiredError as e:
            db.session.rollback()
            return {'message': str(e)}, 410 # 410 Gone is more specific for expired links
        except (InvalidTokenError, ValueError, BadSignature) as e:
            db.session.rollback()
            return {'message': str(e)}, 400
        except UserNotFoundError as e:
            db.session.rollback()
            return {'message': str(e)}, 404
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f"An unexpected error occurred during password reset: {e}")
            return {'message': 'An unexpected error occurred.'}, 500
