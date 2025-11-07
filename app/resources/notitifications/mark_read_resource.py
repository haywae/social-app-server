from flask import current_app, request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import mark_all_notifications_as_read_service, mark_specific_notifications_as_read_service
from app.extensions import db



class MarkNotificationsAsReadResource(Resource):
    """
    API Resource for marking all of the user's notifications as read.
    """
    @jwt_required()
    def put(self):
        """
        Processes a PUT request to mark notifications as read.
        - If a body with 'notification_ids' is sent, marks those specific ones.
        - If no body is sent, marks all as read.
        """
        try:
            user_id = int(get_jwt_identity())
            data = request.get_json(silent=True) # silent=True prevents errors if body is empty

            if data and 'notification_ids' in data:
                # Case 1: Mark specific notifications as read
                notification_ids = data['notification_ids']
                result = mark_specific_notifications_as_read_service(
                    session=db.session,
                    user_id=user_id,
                    notification_public_ids=notification_ids
                )
            else:
                # Case 2: Mark all notifications as read (the original functionality)
                result = mark_all_notifications_as_read_service(
                    session=db.session,
                    user_id=user_id
                )
            
            db.session.commit()
            
            # Return the unread count, which will be 0
            return result, 200

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error marking notifications as read for user {user_id}: {e}", exc_info=True)
            return {'message': 'An error occurred.'}, 500