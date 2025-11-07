from flask import current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services import follow_user_service, unfollow_user_service
from app.exceptions import UserNotFoundError
from app.extensions import db

class FollowResource(Resource):
    """
    API Resource for handling follow and unfollow actions.
    """
    @jwt_required()
    def post(self, username: str):
        """Processes a POST request to make the current user follow another user."""
        try:
            # --- 1. GET THE REQUESTING USER'S ID ---
            follower_id = int(get_jwt_identity())
            
            # --- 2. CALL THE SERVICE FUNCTION TO FOLLOW THE USER ---
            follow_user_service(
                session=db.session,
                follower_id=follower_id,
                followed_username=username
            )
            
            db.session.commit()
            return {'message': f'You are now following {username}.'}, 201

        except UserNotFoundError as e:
            db.session.rollback()
            return {'message': str(e)}, 404
        except ValueError as e: # Catches self-follow or duplicate-follow errors
            db.session.rollback()
            return {'message': str(e)}, 400
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error following user {username}: {e}", exc_info=True)
            return {'message': 'An error occurred.'}, 500

    @jwt_required()
    def delete(self, username: str):
        """Processes a DELETE request to make the current user unfollow another user."""
        try:
            # --- 1. GET THE REQUESTING USER'S ID ---
            follower_id = int(get_jwt_identity())

            # --- 2. CALL THE SERVICE FUNCTION TO UNFOLLOW THE USER ---
            unfollow_user_service(
                session=db.session,
                follower_id=follower_id,
                followed_username=username
            )
            
            db.session.commit()
            return '', 204

        except UserNotFoundError as e:
            db.session.rollback()
            return {'message': str(e)}, 404
        except ValueError as e: # Catches if the user wasn't following them
            db.session.rollback()
            return {'message': str(e)}, 400
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error unfollowing user {username}: {e}", exc_info=True)
            return {'message': 'An error occurred.'}, 500
