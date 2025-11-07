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
    # 1. --- Build the subquery to check if the user has liked each post ---
    is_liked_subquery = (
        select(literal(True))
        .where(PostLike.post_id == Post.id)
        .where(PostLike.user_id == user_id)
        .exists().label("is_liked_by_requester")
    )

    # 2. --- Build the main query for posts ---
    visibility_condition = (Post.visibility == PostVisibility.PUBLIC)
    
    base_query = select(Post, is_liked_subquery).where(
        visibility_condition
    )
    # 3. --- Calculate pagination ---
    count_query = select(func.count(Post.id)).where(visibility_condition)
    total_items = session.execute(count_query).scalar() or 0
    total_pages = math.ceil(total_items / per_page) if per_page > 0 else 0

    # 4. --- Fetch the paginated posts ---
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

    # 5. --- Fetch comment previews for the posts ---

    return {
        "posts": posts,
        "totalPages": total_pages,
        "currentPage": page,
        "totalItems": total_items
    }