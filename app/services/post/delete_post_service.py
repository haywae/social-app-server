from sqlalchemy.orm import Session
from app.models import Post
from app.exceptions import PostNotFoundError, PermissionDeniedError
from uuid import UUID

# This service layer contains the business logic for deleting a post.

def delete_post_service(session: Session, post_public_id: UUID, requesting_user_id: int) -> bool:
    """
    Handles the business logic for deleting a post.

    This includes:
    1. Finding the post by its public ID.
    2. Calling the model's delete method, which enforces ownership.
    """
    # 1. --- Find the Post by its Public ID ---
    # The service layer is responsible for translating the external public_id
    # into the internal integer id that the model methods use.
    post_to_delete = session.query(Post).filter_by(public_id=post_public_id).first()

    if not post_to_delete:
        raise PostNotFoundError("Post not found.")

    # 2. --- Delegate to the Model's Delete Method ---
    # The Post.delete method already contains the necessary permission check
    # to ensure the requesting user is the owner of the post.
    try:
        # We pass the internal integer ID to the model method.
        was_deleted = Post.delete(
            session=session, 
            post_id=post_to_delete.id, 
            requesting_user_id=requesting_user_id
        )
        return was_deleted
    except PermissionDeniedError:
        # Re-raise the specific error to be handled by the API layer.
        raise

