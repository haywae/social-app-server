from flask import request, current_app
from flask_restful import Resource
from app.services  import confirm_email_change_service
from app.exceptions import (
    UserNotFoundError, InvalidTokenError, TokenExpiredError
)
from app.extensions import db


class ConfirmEmailChangeResource(Resource):
    """API Resource for confirming an email change via a token."""
    def post(self):
        data = request.get_json()
        if not data or 'token' not in data:
            return {'message': 'Token is required.'}, 400

        try:
            confirm_email_change_service(session=db.session, token=data['token'])
            db.session.commit()

            return {'message': 'Your email address has been confirmed. A new verification link has been sent to your new email to activate your account.'}, 200

        except (TokenExpiredError, InvalidTokenError, ValueError) as e:
            db.session.rollback()
            return {'message': str(e)}, 400
        except UserNotFoundError as e:
             db.session.rollback()
             return {'message': str(e)}, 404
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error confirming email change: {e}", exc_info=True)
            return {'message': 'An unexpected error occurred.'}, 500

