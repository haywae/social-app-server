from flask import request, current_app
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.services import get_posts_for_user_profile
from app.exceptions import UserNotFoundError
from app.resources.posts._helper import serialize_post
    

class UserPostListResource(Resource):
    """
    API Resource for fetching a paginated list of posts for a specific user. 
    """
    @jwt_required(optional=True)
    def get(self, username: str):
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, default=1, location='args')
        parser.add_argument('per_page', type=int, default=20, location='args')
        args = parser.parse_args()

        try:
            requesting_user_id = get_jwt_identity()
            if requesting_user_id:
                requesting_user_id = int(requesting_user_id)

            paginated_data = get_posts_for_user_profile(
                session=db.session,
                username=username,
                requesting_user_id=requesting_user_id,
                page=args['page'],
                per_page=args['per_page']
            )

            serialized_posts = [serialize_post(post) for post in paginated_data['posts']]
            paginated_data['posts'] = serialized_posts
            return paginated_data, 200

        except UserNotFoundError:
            return {'message': 'User not found'}, 404
        except Exception as e:
            current_app.logger.error(f"Error fetching posts for {username}: {e}", exc_info=True)
            return {'message': 'An error occurred while fetching user posts.'}, 500