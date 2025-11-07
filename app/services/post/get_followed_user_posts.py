import math
from sqlalchemy.orm import Session
from sqlalchemy import func, select, or_, and_, literal
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models import Post, Follower, PostLike
from utils.model_utils.enums import PostVisibility

def get_post_feed_service(session: Session, user_id: int, page: int, per_page: int) -> dict:
    """
    Handles all business logic for fetching a user's personalized post feed.
    """
    # 1. --- Subquery to check if the requester has liked each post ---
    is_liked_subquery = (
        select(literal(True))
        .where(and_(PostLike.post_id == Post.id, PostLike.user_id == user_id))
        .exists()
        .label("is_liked_by_requester")
    )

    # 2. --- Subquery to get IDs of users the requester follows ---
    followed_users_subquery = select(Follower.followed_id).where(Follower.follower_id == user_id).scalar_subquery()

    # 3. --- Define the conditions for the feed using the subquery ---
    final_filter = or_(
        # Condition 1: User's own posts (any visibility is allowed)
        Post.user_id == user_id,
        
        # Condition 2: Followed users' posts (public or followers-only)
        and_(
            Post.user_id.in_(followed_users_subquery),
            Post.visibility.in_([PostVisibility.PUBLIC, PostVisibility.FOLLOWERS_ONLY])
        )
    )
    
    # 4. --- Build the main query for posts ---
    base_query = select(Post, is_liked_subquery).where(final_filter)

    # 5. --- Calculate pagination ---
    count_query = select(func.count(Post.id)).select_from(Post).where(final_filter)
    total_items = session.execute(count_query).scalar() or 0
    total_pages = math.ceil(total_items / per_page) if per_page > 0 else 0

    # 6. --- Fetch the paginated posts ---
    posts_query = (
        base_query
        .options(joinedload(Post.user), joinedload(Post.hashtags))
        .order_by(Post.created_at.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    results = session.execute(posts_query).unique().all()
    
    posts = []
    for post, is_liked in results:
        post.is_liked_by_requester = is_liked
        post.comment_preview = []
        posts.append(post)

    return {
        "posts": posts,
        "totalPages": total_pages,
        "currentPage": page,
        "totalItems": total_items
    }

