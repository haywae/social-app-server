from sqlalchemy import select, literal, exists, and_
from sqlalchemy.orm import Session, joinedload
from app.models import Post, Hashtag, User, Follower, PostLike # Import PostLike
from app.exceptions import PostNotFoundError, PermissionDeniedError
from uuid import UUID
from utils.model_utils.enums import PostVisibility

def get_post_by_public_id_service(session: Session, post_public_id: UUID, requesting_user_id: int | None) -> Post:
    """
    Handles fetching a single post, including whether the current user has liked it.
    """
    # --- QUERY LOGIC ---

    # Define the fields to select. We always want the Post object.
    query_fields = [Post]

    # If a user is logged in, create a subquery to check if they've liked the post.
    if requesting_user_id:
        is_liked_subquery = (
            select(literal(True))
            .where(PostLike.post_id == Post.id)
            .where(PostLike.user_id == requesting_user_id)
            .exists()
        )
        query_fields.append(is_liked_subquery.label("is_liked_by_requester"))

    # Build the main query using the selected fields.
    query = (
        select(*query_fields)
        .options(joinedload(Post.user), joinedload(Post.hashtags))
        .filter(Post.public_id == post_public_id)
    )
    
    # Execute the query to get a single result row.
    result_row = session.execute(query).first()
    
    if not result_row:
        raise PostNotFoundError("Post not found.")

    # Process the result: extract the post and attach the 'is_liked' status.
    post = result_row[0]
    if requesting_user_id:
        post.is_liked_by_requester = result_row.is_liked_by_requester
    

    # The visibility check logic remains unchanged and now operates on the post object.
    if post.visibility == PostVisibility.PUBLIC:
        return post

    if requesting_user_id is None:
        raise PermissionDeniedError("You must be logged in to view this post.")
        
    if post.user_id == requesting_user_id:
        return post
        
    if post.visibility == PostVisibility.FOLLOWERS_ONLY:
        is_follower = session.query(
            exists().where(
                and_(Follower.follower_id == requesting_user_id, Follower.followed_id == post.user_id)
            )
        ).scalar()
        
        if is_follower:
            return post

    raise PermissionDeniedError("You do not have permission to view this post.")