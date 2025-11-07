from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from app.models import User
from app.exceptions import UserNotFoundError

def get_user_details_service(session: Session, user_id: int) -> User:
    """
    Fetches a user by their ID, eagerly loading all relationships
    needed for full serialization (followers, following, posts).
    """
    query = (
        select(User)
        .options(
            joinedload(User.followers),
            joinedload(User.followed),
            joinedload(User.posts)
        )
        .where(User.id == user_id)
    )
    
    user = session.execute(query).unique().scalar_one_or_none()
    
    if not user:
        raise UserNotFoundError("User not found.")
        
    return user
