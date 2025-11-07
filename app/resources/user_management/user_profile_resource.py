from flask import current_app
from flask_restful import Resource
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.models import User


from app.services.user_management import get_user_profile_by_username
from app.exceptions import UserNotFoundError
from app.extensions import db

# Helper function to serialize the profile data for the frontend.
def serialize_profile(profile_data: dict) -> dict:
    user: User = profile_data["user"]

    return {
        "id": str(user.public_id),
        "username": user.username,
        "displayName": user.display_name,
        "avatarUrl": user.profile_picture_url,
        "bio": user.bio,
        "followerCount": profile_data["follower_count"],
        "followingCount": profile_data["following_count"],
        "postCount": profile_data["post_count"],
        "joinedDate": user.created_at.isoformat(),
        "isFollowing": profile_data["is_following"]
    }

class UserProfileResource(Resource):
    """
    API Resource for fetching a user's profile information.
    """
    # optional=True so the endpoint works for both logged-in and anonymous users.
    @jwt_required(optional=True)
    def get(self, username: str):
        """
        Processes a GET request to fetch a user's profile by their username.
        """
        try:
            # Get the ID of the user making the request, if they are logged in.
            requesting_user_id = get_jwt_identity()
            if requesting_user_id:
                requesting_user_id = int(requesting_user_id)

            # Delegate the business logic to the service layer.
            profile_data = get_user_profile_by_username(
                session=db.session,
                username=username,
                requesting_user_id=requesting_user_id
            )
            
            # Serialize the data for the frontend and return.
            return serialize_profile(profile_data), 200

        except UserNotFoundError:
            return {'message': 'User not found'}, 404
        except Exception as e:
            current_app.logger.error(f"Error fetching profile for {username}: {e}", exc_info=True)
            return {'message': 'An error occurred while fetching the user profile.'}, 500
