from flask import current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from uuid import UUID

from app.services import get_post_by_public_id_service
from app.exceptions import PostNotFoundError, PermissionDeniedError
from app.extensions import db
from app.resources.posts._helper import serialize_post

class UserPostResource(Resource):
    """
    API Resource for fetching a single post by its public ID.
    """
    # Optional=True so the endpoint works for both logged-in and anonymous users.
    @jwt_required(optional=True)
    def get(self, public_id: UUID):
        """
        Processes a GET request to fetch a single post by its public ID.
        """
        try:
            user_id = get_jwt_identity()
            if user_id:
                user_id = int(user_id)

            # Delegate all business logic to the service layer.
            post = get_post_by_public_id_service(
                session=db.session,
                post_public_id=public_id,
                requesting_user_id=user_id
            )
            
            return serialize_post(post), 200

        except PermissionDeniedError as e:
            return {'message': str(e)}, 403
        except PostNotFoundError as e:
            return {'message': str(e)}, 404
        except Exception as e:
            current_app.logger.error(f"Error fetching post {public_id}: {e}", exc_info=True)
            return {'message': 'An error occurred while fetching the post.'}, 500