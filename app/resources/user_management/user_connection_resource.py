from flask import request
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import Session
from app.extensions import db
from app.services import get_user_connections_service
from app.exceptions import UserNotFoundError
from app.models import User, Follower

def serialize_user_for_list(session: Session, user: User, requesting_user_id: int | None) -> dict:
    """Serializes a User object for list displays."""
    
    is_self = requesting_user_id is not None and user.id == requesting_user_id
    is_following = False
    
    # Check if the *requesting* user is following the user in the list
    if requesting_user_id and not is_self:
        is_following = session.query(Follower).filter_by(
            follower_id=requesting_user_id,
            followed_id=user.id
        ).first() is not None

    return {
        "username": user.username,
        "authorName": user.display_name, # Match your Post prop names
        "authorAvatarUrl": user.profile_picture_url, # Match your Post prop names
        "bio": user.bio,
        "isFollowing": is_following,
        "isSelf": is_self
    }


class FollowerListResource(Resource):
    @jwt_required(optional=True)
    def get(self, username: str):
        """
        Get a paginated list of users who follow the target user.
        """
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, default=1, location='args')
        parser.add_argument('per_page', type=int, default=20, location='args')
        args = parser.parse_args()
        
        requesting_user_id = get_jwt_identity()
        if requesting_user_id:
            requesting_user_id = int(requesting_user_id)
        
        try:
            data = get_user_connections_service(
                session=db.session,
                target_username=username,
                connection_type='followers',
                page=args['page'],
                per_page=args['per_page']
            )
            
            data['users'] = [
                serialize_user_for_list(db.session, user, requesting_user_id) 
                for user in data['users']
            ]
            return data, 200
        except UserNotFoundError as e:
            return {'message': str(e)}, 404
        except Exception as e:
            return {'message': str(e)}, 500

class FollowingListResource(Resource):
    @jwt_required(optional=True)
    def get(self, username: str):
        """
        Get a paginated list of users the target user is following.
        """
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, default=1, location='args')
        parser.add_argument('per_page', type=int, default=20, location='args')
        args = parser.parse_args()
        
        requesting_user_id = get_jwt_identity()
        if requesting_user_id:
            requesting_user_id = int(requesting_user_id)

        try:
            data = get_user_connections_service(
                session=db.session,
                target_username=username,
                connection_type='following',
                page=args['page'],
                per_page=args['per_page']
            )
            
            data['users'] = [
                serialize_user_for_list(db.session, user, requesting_user_id) 
                for user in data['users']
            ]
            return data, 200
        except UserNotFoundError as e:
            return {'message': str(e)}, 404
        except Exception as e:
            return {'message': str(e)}, 500