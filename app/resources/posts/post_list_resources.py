import math
from flask import request, current_app
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.services import get_post_feed_service # <-- Import the new service
from app.resources.posts._helper import serialize_post

class PostListResource(Resource):
    """
    API Resource for fetching a list of posts (e.g., a user's feed).
    """
    @jwt_required()
    def get(self):
        """
        Processes a GET request to fetch the current user's personalized feed.
        """
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, default=1, location='args')
        parser.add_argument('per_page', type=int, default=20, location='args')
        args = parser.parse_args()

        try:
            user_id = int(get_jwt_identity())

            # --- The resource now makes a single, clean call to the service layer ---
            feed_data = get_post_feed_service(
                session=db.session,
                user_id=user_id,
                page=args['page'],
                per_page=args['per_page']
            )
            
            # Serialize the posts from the data returned by the service
            feed_data['posts'] = [serialize_post(post) for post in feed_data['posts']]
            
            return feed_data, 200

        except Exception as e:
            current_app.logger.error(f"Error fetching user feed: {e}", exc_info=True)
            return {'message': 'An error occurred while fetching posts.'}, 500