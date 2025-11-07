from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from uuid import UUID

from app.services.post import update_post_service
from app.exceptions import PostNotFoundError, PermissionDeniedError
from app.extensions import db
from app.resources.posts._helper import serialize_post


class UpdatePostResource(Resource):
    """
    API Resource for handling update operation on a single post
    """
    @jwt_required()
    def put(self, public_id: UUID):
        """
        Processes a PUT request to update a post.

        Args:
            public_id (UUID): The public ID of the post to update.

        Returns:
            - 200 OK: The updated post object.
            - 400 Bad Request: If the input data is invalid.
            - 403 Forbidden: If the user does not have permission.
            - 404 Not Found: If the post does not exist.
        """
        data = request.get_json()
        if not data:
            return {'message': 'No input data provided'}, 400

        try:
            user_id = int(get_jwt_identity())
            updated_post = update_post_service(
                session=db.session,
                post_public_id=public_id,
                requesting_user_id=user_id,
                update_data=data
            )
            db.session.commit()
            return serialize_post(updated_post), 200

        except (ValueError, PermissionDeniedError) as e:
            db.session.rollback()
            return {'message': str(e)}, 403
        except PostNotFoundError as e:
            db.session.rollback()
            return {'message': str(e)}, 404
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating post {public_id}: {e}", exc_info=True)
            return {'message': 'An error occurred while updating the post.'}, 500
