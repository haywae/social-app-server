from flask import current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services import get_user_by_id, get_user_details_service
from app.resources.auth._helper import serialize_basic_user
from app.exceptions import UserNotFoundError
from app.extensions import db

class AuthCheckResource(Resource):
    """
    API Resource to verify a user's authentication status via a valid JWT.
    """
    @jwt_required()
    def get(self):
        """
        Processes a GET request to check the current user's authentication. \n
        Uses the identity from the JWT to fetch user details.
        Returns:
            - 200 OK: If the token is valid and the user exists.
            - 404 Not Found: If the user from the token no longer exists.
            - 500 Internal Server Error: For unexpected server issues.
        """
        try:
            # 1. Get the identity from the JWT.
            user_id_str = get_jwt_identity()
            if not user_id_str:
                return {'message': 'Token is missing identity.'}, 400
            user_id = int(user_id_str)

            # 2. Use the user_details_service to get the full, eagerly loaded user.
            user_with_details = get_user_details_service(session=db.session, user_id=user_id)

            # 3. Use the serializer to create the perfect JSON object for the frontend.
            user_json = serialize_basic_user(user_with_details)
            
            # 4. Format the successful API response.
            return {
                'message': 'Authentication successful',
                'user': user_json,
            }, 200

        except UserNotFoundError as e:
            return {'message': str(e)}, 404
        except Exception as e:
            current_app.logger.error(f'Unexpected error during authentication check: {e}', exc_info=True)
            return {'message': 'An unexpected error occurred'}, 500
