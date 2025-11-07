from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services  import (
    change_username_service,
)
from app.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.extensions import db
from app.resources.user_management._helper import serialize_user


class ChangeUsernameResource(Resource):
    """API Resource for changing the current user's username."""
    @jwt_required()

    def put(self):
        data = request.get_json()
        if not data or 'password' not in data or 'new_username' not in data:
            return {'message': 'Password and new username are required.'}, 400

        try:
            user_id = int(get_jwt_identity())
            user_data = change_username_service(
                session=db.session,
                user_id=user_id,
                password=data['password'],
                new_username=data['new_username']
            )

            db.session.commit()
            return {'message': 'Username updated successfully', 'user': serialize_user(user_data)}, 200

        except (InvalidCredentialsError, UserAlreadyExistsError, ValueError) as e:
            db.session.rollback()
            return {'message': str(e)}, 400
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error changing username: {e}", exc_info=True)
            return {'message': 'An unexpected error occurred.'}, 500
