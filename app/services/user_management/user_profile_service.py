from sqlalchemy.orm import Session
from sqlalchemy import func, select, desc, or_, and_, exists
from app.models import User, Post, Follower
from app.exceptions import UserNotFoundError
from utils.model_utils.enums import PostVisibility

# This service layer contains the business logic for fetching user profile data.

def get_user_profile_by_username(session: Session, username: str, requesting_user_id: int | None = None) -> dict:
    """
    Handles the business logic for fetching a user's core profile data.
    This version is optimized to be fast and does NOT fetch the full post list.
    Returns a dictionary with the user's profile data, follower count, following count, and post count.
    Raises UserNotFoundError if the user does not exist.
    """
    # 1. --- Find the User ---
    # We use the case-insensitive identifier search for flexibility.
    user = User.get_by_identifier(session, identifier=username)
    if not user:
        raise UserNotFoundError("User not found.")

    # 2. --- Get Follower and Following Counts ---
    follower_count_query = select(func.count(Follower.follower_id)).where(Follower.followed_id == user.id)
    follower_count = session.execute(follower_count_query).scalar()

    following_count_query = select(func.count(Follower.followed_id)).where(Follower.follower_id == user.id)
    following_count = session.execute(following_count_query).scalar()

    # 3. --- Get the User's Posts count ---
    posts_count_query = select(func.count(Post.id)).where(Post.user_id == user.id)
    
    # 4. --- Handle Post Visibility ---
    visibility_conditions = [Post.visibility == PostVisibility.PUBLIC]
    if requesting_user_id:
        if requesting_user_id == user.id: # The user is viewing their own profile
            visibility_conditions.append(Post.visibility.in_([PostVisibility.FOLLOWERS_ONLY, PostVisibility.PRIVATE]))
        else: # A different user is viewing the profile
            is_follower_subquery = select(exists().where(
                and_(Follower.follower_id == requesting_user_id, Follower.followed_id == user.id)
            )).scalar_subquery()
            visibility_conditions.append(and_(Post.visibility == PostVisibility.FOLLOWERS_ONLY, is_follower_subquery))

    posts_count_query = posts_count_query.where(or_(*visibility_conditions))
    posts_count = session.execute(posts_count_query).scalar()

    # 5. --- CHECK 'isFollowing' STATUS ---
    is_following = False
    if requesting_user_id and requesting_user_id != user.id:
        is_following_query = select(exists().where(
            and_(Follower.follower_id == requesting_user_id, Follower.followed_id == user.id)
        ))
        is_following = session.execute(is_following_query).scalar()

    # 6. --- Assemble the Profile Data ---
    # The service layer returns a dictionary of all the data the API layer will need.
    return {
        "user": user,
        "post_count": posts_count or 0,
        "follower_count": follower_count or 0,
        "following_count": following_count or 0,
        "is_following": is_following
    }
