from sqlalchemy.orm import Session
from app.models import Post, PostLike, Notification, User
from app.exceptions import PostNotFoundError, UserNotFoundError
from uuid import UUID

from app.extensions import socketio
from app.resources.notitifications.notification_list_resource import serialize_notification

def like_post_service(session: Session, user_id: int, post_public_id: UUID) -> bool:
    """
    Handles the business logic for a user liking a post.

    This includes:
    1. Finding the post.
    2. Checking if the user has already liked the post.
    3. Creating the PostLike record.
    4. Atomically incrementing the post's like_count.
    """

    # --- 1. Get the actor (the user liking the post) ---
    actor_user = session.get(User, user_id)
    if not actor_user:
        raise UserNotFoundError("User not found.")
    
    # --- 2. Find the Post ---
    post = session.query(Post).filter_by(public_id=post_public_id).first()
    if not post:
        raise PostNotFoundError("The post you are trying to like does not exist.")

    # --- 3. Check for Existing Like ---
    # The service layer enforces the business rule that a user cannot like a post twice.
    if PostLike.exists(session, user_id=user_id, post_id=post.id):
        raise ValueError("You have already liked this post.")

    # --- 4. Create the Like and Update Counter ---
    PostLike.create(session, user_id=user_id, post_id=post.id)
    post.like_count += 1

    # --- Create Notification (if not liking your own post) ---
    if user_id != post.user_id:
        new_notification = Notification.create(
            session=session,
            recipient_user_id=post.user_id,
            actor_user_id=user_id,
            action_type='like',
            target_type='post',
            target_id=post.id
        )
        # --- A. ADD THIS SOCKET LOGIC ---
        if new_notification:
            session.flush() # Flush to get notification ID
            
            # B. Manually attach objects for the serializer
            new_notification.actor = actor_user
            new_notification.target_object = post
            
            # C. Serialize the data
            serialized_data = serialize_notification(new_notification)
            
            # D. Emit to the post author's user room
            socketio.emit(
                'new_notification',
                serialized_data,
                to=f"user_{post.user_id}"
            )
    
    return True

def unlike_post_service(session: Session, user_id: int, post_public_id: UUID) -> bool:
    """
    Handles the business logic for a user unliking a post.
    """
    post = session.query(Post).filter_by(public_id=post_public_id).first()
    if not post:
        raise PostNotFoundError("The post you are trying to unlike does not exist.")

    # The model's delete method returns True if a like was actually deleted.
    was_deleted = PostLike.delete(session, user_id=user_id, post_id=post.id)
    
    if not was_deleted:
        raise ValueError("You have not liked this post.")

    # Decrement the counter only if a like was successfully removed.
    # Ensure the count does not go below zero.
    if post.like_count > 0:
        post.like_count -= 1
        
    return True
