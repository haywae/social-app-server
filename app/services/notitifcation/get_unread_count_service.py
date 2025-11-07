from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models import Notification

def get_unread_notification_count_service(session: Session, user_id: int) -> int:
    """Calculates the total number of unread notifications for a user."""
    unread_count_query = (
        select(func.count(Notification.id))
        .where(Notification.recipient_user_id == user_id)
        .where(Notification.is_read == False)
    )
    return session.execute(unread_count_query).scalar() or 0