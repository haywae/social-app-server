import math
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, select, or_, and_, exists, literal
from app.models import User, Post, Follower, PostLike # --- Import PostLike
from app.exceptions import UserNotFoundError
from utils.model_utils.enums import PostVisibility

def get_posts_for_user_profile(session: Session, username: str, requesting_user_id: int | None, page: int, per_page: int) -> dict:
    """
    Fetches a paginated list of posts for a specific user's profile, respecting visibility
    and including the 'is_liked' status for the requesting user.
    """
    target_user = User.get_by_identifier(session, identifier=username)
    if not target_user:
        raise UserNotFoundError("User not found.")

    # --- 1. DEFINE THE 'is_liked' SUBQUERY (IF USER IS LOGGED IN) ---
    query_fields = [Post]
    if requesting_user_id:
        is_liked_subquery = (
            select(literal(True))
            .where(PostLike.post_id == Post.id)
            .where(PostLike.user_id == requesting_user_id)
            .exists()
            .label("is_liked_by_requester")
        )
        query_fields.append(is_liked_subquery)

    # --- 2. UPDATE THE BASE QUERY TO SELECT THE NEW FIELD ---
    base_query = select(*query_fields).where(Post.user_id == target_user.id)
    
    # Your visibility logic remains the same.
    visibility_conditions = [Post.visibility == PostVisibility.PUBLIC]
    if requesting_user_id:
        if requesting_user_id == target_user.id:
            visibility_conditions.append(Post.visibility.in_([PostVisibility.FOLLOWERS_ONLY, PostVisibility.PRIVATE]))
        else:
            is_follower_subquery = select(exists().where(
                and_(Follower.follower_id == requesting_user_id, Follower.followed_id == target_user.id)
            )).scalar_subquery()
            visibility_conditions.append(and_(Post.visibility == PostVisibility.FOLLOWERS_ONLY, is_follower_subquery))
    
    base_query = base_query.where(or_(*visibility_conditions))

    # The count query remains the same.
    count_query = select(func.count()).select_from(base_query.subquery())
    total_items = session.execute(count_query).scalar() or 0
    total_pages = math.ceil(total_items / per_page) if per_page > 0 else 0

    # --- 3. ADD EAGER LOADING TO THE FINAL QUERY ---
    posts_query = (
        base_query
        .options(joinedload(Post.user), joinedload(Post.hashtags)) # Performance optimization
        .order_by(Post.created_at.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    
    # --- 4. PROCESS THE RESULTS (TUPLES) INSTEAD OF SCALARS ---
    results = session.execute(posts_query).unique().all()
    
    posts = []
    for row in results:
        post = row[0]
        # Attach the 'is_liked' boolean if the user is logged in
        if requesting_user_id:
            post.is_liked_by_requester = row.is_liked_by_requester
        posts.append(post)

    return {
        "posts": posts,
        "totalPages": total_pages,
        "currentPage": page,
        "totalItems": total_items
    }