from sqlalchemy.orm import Session
from sqlalchemy import update
from app.models import Notification
from .get_unread_count_service import get_unread_notification_count_service
from uuid import UUID

def mark_specific_notifications_as_read_service(session: Session, user_id: int, notification_public_ids: list[str]) -> dict:
    """
    Marks a specific list of notifications as read for a user.
    Ensures a user can only mark their own notifications as read.
    """
    if not notification_public_ids:
        # If an empty list is sent, just return the current count
        current_count = get_unread_notification_count_service(session, user_id)
        return {"unread_count": current_count}

    valid_uuids = []
    for public_id in notification_public_ids:
        try:
            # Validate that the string is a valid UUID
            UUID(public_id)
            valid_uuids.append(public_id)
        except ValueError:
            # Silently ignore invalid UUID strings
            continue

    if not valid_uuids:
        current_count = get_unread_notification_count_service(session, user_id)
        return {"unread_count": current_count}

    update_stmt = (
        update(Notification)
        .where(Notification.recipient_user_id == user_id)
        .where(Notification.public_id.in_(valid_uuids))
        .where(Notification.is_read == False)
        .values(is_read=True)
    )
    session.execute(update_stmt)

    # After the update, calculate and return the new unread count
    new_unread_count = get_unread_notification_count_service(session, user_id)
    return {"unread_count": new_unread_count}
