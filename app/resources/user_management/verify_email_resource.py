from flask import request, current_app
from flask_restful import Resource

from app.services import verify_email_with_token
from app.exceptions import UserNotFoundError, InvalidTokenError, TokenExpiredError
from app.extensions import db

class VerifyEmailResource(Resource):
    """
    API Resource for handling the final step of email verification.
    """
    def post(self):
        """
        Processes a POST request to verify an email using a token.
        """
        data = request.get_json()
        if not data or 'token' not in data:
            return {'message': 'Verification token is required.'}, 400

        try:
            # Delegate all logic to the service layer.
            verified_user = verify_email_with_token(
                session=db.session,
                token=data.get('token')
            )
            
            db.session.commit()
            
            return {'message': 'Your email has been successfully verified. You can now log in.'}, 200

        except (InvalidTokenError, TokenExpiredError, ValueError) as e:
            db.session.rollback()
            return {'message': str(e)}, 400
        except UserNotFoundError as e:
            db.session.rollback()
            return {'message': str(e)}, 404
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An unexpected error occurred during email verification: {e}", exc_info=True)
            return {'message': 'An unexpected error occurred.'}, 500
