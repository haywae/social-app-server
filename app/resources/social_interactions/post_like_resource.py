from flask import current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from uuid import UUID

from app.services import like_post_service, unlike_post_service
from app.exceptions import PostNotFoundError
from app.extensions import db


class PostLikeResource(Resource):
    """
    API Resource for handling liking and unliking a post.
    """
    @jwt_required()
    def post(self, public_id: UUID):
        """Processes a POST request to make the current user like a post."""
        try:
            # --- 1. GET THE REQUESTING USER'S ID ---
            user_id = int(get_jwt_identity())

            # --- 2. CALL THE SERVICE FUNCTION TO LIKE THE POST ---
            like_post_service(
                session=db.session,
                user_id=user_id,
                post_public_id=public_id
            )
            
            db.session.commit()
            return {'message': 'Post liked successfully.'}, 201

        except PostNotFoundError as e:
            db.session.rollback()
            return {'message': str(e)}, 404
        except ValueError as e: # Catches if the post is already liked
            db.session.rollback()
            return {'message': str(e)}, 400
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error liking post {public_id}: {e}", exc_info=True)
            return {'message': 'An error occurred.'}, 500

    @jwt_required()
    def delete(self, public_id: UUID):
        """Processes a DELETE request to make the current user unlike a post."""
        try:
            # --- 1. GET THE REQUESTING USER'S ID ---
            user_id = int(get_jwt_identity())

            # --- 2. CALL THE SERVICE FUNCTION TO UNLIKE THE POST ---
            unlike_post_service(
                session=db.session,
                user_id=user_id,
                post_public_id=public_id
            )
            
            db.session.commit()
            # A 204 response is standard for a successful DELETE and has no body.
            return '', 204

        except PostNotFoundError as e:
            db.session.rollback()
            return {'message': str(e)}, 404
        except ValueError as e: # Catches if the user hasn't liked the post
            db.session.rollback()
            return {'message': str(e)}, 400
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error unliking post {public_id}: {e}", exc_info=True)
            return {'message': 'An error occurred.'}, 500
