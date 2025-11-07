from flask import current_app
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import User, Notification
from app.services import get_notifications_service
from app.extensions import db


# Helper function to serialize the notification data for the frontend.
def serialize_notification(notification: Notification) -> dict:
    # Create the nested 'fromUser' object
    from_user = None
    if notification.actor:
        from_user = {
            "username": notification.actor.username,
            "displayName": notification.actor.display_name,
            "avatarUrl": notification.actor.profile_picture_url,
            "isDeleted": False
        }
    else:
        # "Ghost User" placeholder for deleted users
        from_user = {
            "username": "deleted_user",
            "displayName": "A deleted user",
            "avatarUrl": None,  # Frontend will use DEFAULT_AVATAR_URL
            "isDeleted": True
        }
    
    # Create the nested 'post' object if the target is a post
    post_data = None
    
    # This handles notifications where the Post is the direct target (e.g., post like)
    if notification.target_type == 'post' and hasattr(notification, 'target_object') and notification.target_object:
        post = notification.target_object
        post_data = {
            "id": str(post.public_id),
            # Truncate content for the notification preview
            "content": (post.content[:75] + '...') if post.content and len(post.content) > 75 else post.content
        }

    return {
        "id": str(notification.public_id),
        "type": notification.action_type,
        "isRead": notification.is_read,   
        "createdAt": notification.created_at.isoformat(),
        "fromUser": from_user,
        "post": post_data, 
    }

class NotificationListResource(Resource):
    """
    API Resource for fetching the current user's notifications.
    """
    @jwt_required()
    def get(self):
        """
        Processes a GET request to fetch a paginated list of notifications.
        """
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, default=1, location='args')
        parser.add_argument('per_page', type=int, default=20, location='args')
        args = parser.parse_args()

        try:
            user_id = int(get_jwt_identity())

            # The service returns a dictionary with notifications and the unread count
            service_data = get_notifications_service(
                session=db.session,
                user_id=user_id,
                page=args['page'],
                per_page=args['per_page']
            )
            
            db.session.commit()
            
            # Serialize the list of notification objects
            serialized_notifications = [serialize_notification(n) for n in service_data['notifications']]
            
            # Assemble the final response with the top-level 'unreadCount'
            return {
                'notifications': serialized_notifications,
                'unreadCount': service_data['unread_count'],
                'currentPage': service_data['current_page'],
                'totalPages': service_data['total_pages']
            }, 200

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error fetching notifications: {e}", exc_info=True)
            return {'message': 'An error occurred while fetching notifications.'}, 500
