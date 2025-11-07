import math
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models import User, Follower
from app.exceptions import UserNotFoundError

def get_user_connections_service(
    session: Session,
    target_username: str,
    connection_type: str,
    page: int,
    per_page: int) -> dict:
    
    # 1. Find the target user
    target_user = session.execute(
        select(User).where(User.username == target_username)
    ).scalar_one_or_none()

    if not target_user:
        raise UserNotFoundError("Profile not found.")

    # 2. Build the base query based on connection type
    if connection_type == 'followers':
        # Query for users who are following the target_user
        base_query = (
            select(User)
            .join(Follower, User.id == Follower.follower_id)
            .where(Follower.followed_id == target_user.id)
        )
    elif connection_type == 'following':
        # Query for users who are being followed by the target_user
        base_query = (
            select(User)
            .join(Follower, User.id == Follower.followed_id)
            .where(Follower.follower_id == target_user.id)
        )
    else:
        raise ValueError("Invalid connection type specified.")

    # 3. Get the total count for pagination
    # We create a subquery from the base to count from
    count_query = select(func.count()).select_from(base_query.subquery())
    total_items = session.execute(count_query).scalar() or 0
    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1

    # 4. Get the paginated list of users
    paginated_query = (
        base_query
        .order_by(User.username)
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    
    users = session.execute(paginated_query).scalars().all()

    return {
        "users": users,
        "totalPages": total_pages,
        "currentPage": page,
        "totalItems": total_items
    }