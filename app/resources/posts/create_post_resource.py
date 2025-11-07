from flask import request, current_app
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services import create_post
from app.exceptions import UserNotFoundError
from app.extensions import db
from app.resources.posts._helper import serialize_post
from app.models import User
from utils.app_utils.decorators import require_active_user
from utils.model_utils.enums import PostType



class CreatePostResource(Resource):
    """
    API Resource for creating a new post.
    """
    @jwt_required()
    @require_active_user
    def post(self, current_user: User):
        """
        Processes a POST request to create a new post.

        Expects a JSON payload with keys like "content", "media_url", "tags", etc.

        Returns:
            - 201 Created: The newly created post object.
            - 400 Bad Request: If input data is invalid.
            - 500 Internal Server Error: For unexpected server issues.
        """
        
        data = request.get_json()
        if not data:
            return {'message': 'No input data provided'}, 400

        try:
            # 1. Get the postType from the request, defaulting to 'REGULAR'.
            post_type_str = data.get('postType', 'REGULAR').upper()

            # 2. Directly validate if the string is a valid enum member.
            if post_type_str not in PostType.__members__:
                return {'message': f"Invalid postType: '{post_type_str}'."}, 400

            # 3. If valid, safely convert the string to the PostType enum.
            post_type = PostType[post_type_str]

            # Delegate all business logic to the service layer.
            new_post = create_post(
                session=db.session,
                user_id=current_user.id,
                content=data.get('content'),
                media_url=data.get('media_url'),
                tag_names=data.get('tags', []),  # Expects a list of strings
                post_type=post_type
            )
            
            db.session.commit()
            
            return serialize_post(new_post), 201

        except (ValueError, UserNotFoundError) as e:
            db.session.rollback()
            return {'message': str(e)}, 400
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating post: {e}", exc_info=True)
            return {'message': 'An error occurred while creating the post.'}, 500
