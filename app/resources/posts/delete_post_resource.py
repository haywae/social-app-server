from flask import current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from uuid import UUID

from app.services import delete_post_service
from app.exceptions import PostNotFoundError, PermissionDeniedError
from app.extensions import db

class DeletePostResource(Resource):
    """
    API Resource for handling delete operation on a single post
    """
    @jwt_required()
    def delete(self, public_id: UUID):
        """
        Processes a DELETE request to remove a post.

        Args:
            public_id (UUID): The public ID of the post to delete, from the URL.

        Returns:
            - 204 No Content: If the post was deleted successfully.
            - 403 Forbidden: If the user does not have permission to delete the post.
            - 404 Not Found: If the post does not exist.
            - 500 Internal Server Error: For unexpected server issues.
        """
        try:
            user_id = int(get_jwt_identity())

            # Delegate all business logic to the service layer.
            success = delete_post_service(
                session=db.session,
                post_public_id=public_id,
                requesting_user_id=user_id
            )
            
            if success:
                db.session.commit()
                # A 204 response is standard for a successful DELETE and has no body.
                return '', 204

        except PermissionDeniedError as e:
            db.session.rollback()
            return {'message': str(e)}, 403
        except PostNotFoundError as e:
            db.session.rollback()
            return {'message': str(e)}, 404
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting post {public_id}: {e}", exc_info=True)
            return {'message': 'An error occurred while deleting the post.'}, 500
