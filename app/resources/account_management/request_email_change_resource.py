from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services  import request_email_change_service

from app.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.extensions import db

class RequestEmailChangeResource(Resource):
    """API Resource for initiating an email change."""
    @jwt_required()
    def post(self):
        data = request.get_json()
        if not data or 'password' not in data or 'new_email' not in data:
            return {'message': 'Password and new email are required.'}, 400

        try:
            user_id = int(get_jwt_identity())
            request_email_change_service(
                session=db.session,
                user_id=user_id,
                password=data['password'],
                new_email=data['new_email']
            )
            return {'message': 'A verification link has been sent to the new email address you provided.'}, 200
        except (InvalidCredentialsError, UserAlreadyExistsError, ValueError) as e:
            return {'message': str(e)}, 400
        except Exception as e:
            current_app.logger.error(f"Error requesting email change: {e}", exc_info=True)
            return {'message': 'An unexpected error occurred.'}, 500
