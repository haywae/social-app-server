from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, update, func
from app.models import Notification, User, Post
import math


def get_notifications_service(session: Session, user_id: int, page: int, per_page: int) -> dict:
    """
    Handles the business logic for fetching a user's notifications.
    """
    # --- 1 & 2: Count and Pagination Logic (Unchanged) ---
    unread_count_query = (
        select(func.count(Notification.id))
        .where(Notification.recipient_user_id == user_id, Notification.is_read == False)
    )
    total_unread_before_fetch = session.execute(unread_count_query).scalar() or 0

    total_items_query = select(func.count(Notification.id)).where(Notification.recipient_user_id == user_id)
    total_items = session.execute(total_items_query).scalar() or 0
    total_pages = math.ceil(total_items / per_page) if per_page > 0 else 0

    # --- 3. Fetch Paginated Notifications (Unchanged) ---
    query = (
        select(Notification)
        .where(Notification.recipient_user_id == user_id)
        .options(joinedload(Notification.actor))
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    notifications = session.execute(query).scalars().all()

    # STEP A: Collect all target IDs in a single loop
    post_ids_to_fetch = []
    for n in notifications:
        if n.target_type == 'post' and n.target_id:
            post_ids_to_fetch.append(n.target_id)

    # STEP B: Fetch all target objects in bulk (to prevent N+1 queries)
    posts_by_id = {}
    if post_ids_to_fetch:
        posts = session.query(Post).filter(Post.id.in_(post_ids_to_fetch)).all()
        posts_by_id = {post.id: post for post in posts}


    # STEP C: Attach all objects in a single, final loop
    for n in notifications:
        if n.target_type == 'post':
            n.target_object = posts_by_id.get(n.target_id)

    # --- 5. Return All Data (Unchanged) ---
    return {
        "notifications": notifications,
        "unread_count": total_unread_before_fetch,
        "current_page": page,
        "total_pages": total_pages
    }
