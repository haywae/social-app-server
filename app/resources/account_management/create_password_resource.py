from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.exceptions import UserNotFoundError
from app.services import create_password

class CreatePasswordResource(Resource):
    """
    API Resource for an authenticated OAuth-only user to create
    their first internal password.
    """
    @jwt_required()
    def post(self):
        """
        Processes a POST request to create and set a user's password.
        """
        data = request.get_json()
        if not data or 'new_password' not in data:
            return {'message': 'The new_password field is required.'}, 400

        try:
            user_id = int(get_jwt_identity())
            new_password = data['new_password']

            # Delegate all business logic to the service layer
            success = create_password(
                session=db.session,
                user_id=user_id,
                new_password=new_password
            )
            
            if success:
                db.session.commit()
                # 201 Created is semantically correct for creating a new password
                return {'message': 'Password created successfully.'}, 201

        except ValueError as e:
            # Catches "password already set" or "password too weak"
            db.session.rollback()
            return {'message': str(e)}, 400
        except UserNotFoundError as e:
            db.session.rollback()
            return {'message': str(e)}, 404
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating password for user {user_id}: {e}", exc_info=True)
            return {'message': 'An unexpected error occurred.'}, 500