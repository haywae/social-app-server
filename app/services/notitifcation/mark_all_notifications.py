from sqlalchemy.orm import Session
from sqlalchemy import update
from app.models import Notification


def mark_all_notifications_as_read_service(session: Session, user_id: int) -> dict:
    """
    Marks all unread notifications for a specific user as read.
    Performs a bulk update for efficiency.
    """
    update_stmt = (
        update(Notification)
        .where(Notification.recipient_user_id == user_id)
        .where(Notification.is_read == False)
        .values(is_read=True)
    )
    session.execute(update_stmt)
    
    return {"unread_count": 0}