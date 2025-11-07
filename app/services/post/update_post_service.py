import re
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Post, User, Notification
from app.exceptions import PermissionDeniedError, PostNotFoundError
from uuid import UUID
from app.models import Hashtag
from utils.app_utils.regex_patterns import MENTION_REGEX
from app.extensions import socketio
from app.resources.notitifications.notification_list_resource import serialize_notification



def update_post_service(
    session: Session, 
    post_public_id: UUID, 
    requesting_user_id: int, 
    update_data: dict
) -> Post:
    """
    Handles the business logic for updating a post.

    This includes:
    1. Finding the post by its public ID.
    2. Calling the model's update method, which enforces ownership.
    3. Updating associated hashtags.
    """

    requesting_user = session.get(User, requesting_user_id)
    if not requesting_user:
        # This should theoretically not happen if they are authenticated
        raise PermissionDeniedError("Requesting user not found.")
    
    # 1. Find the post by its public ID
    post_to_update = session.query(Post).filter_by(public_id=post_public_id).first()
    if not post_to_update:
        raise PostNotFoundError("Post not found.")
    
    # 2. Check edit time limit
    current_time = datetime.now(timezone.utc)
    post_age = current_time - post_to_update.created_at
    
    # If the post is older than one hour, raise a permission error.
    if post_age > timedelta(hours=1):
        raise PermissionDeniedError("Posts cannot be edited after one hour.")
    
    # 3. Get old mention IDs (to prevent re-notifying)
    old_mention_ids = {user.id for user in post_to_update.mentioned_users}

    # 4. Handle Hashtag translation
    # The client sends 'hashtags' as a list of strings
    hashtag_names = update_data.pop('hashtags', None)
    if hashtag_names is not None: # An empty list [] is a valid update
        unique_tag_names = set(hashtag_names)
        hashtag_objects = [Hashtag.find_or_create(session, name) for name in unique_tag_names]
        # Put the list of *objects* back into update_data
        update_data['hashtags'] = hashtag_objects

    # 5. Handle Mentions translation (based on new content)
    if 'content' in update_data:
        new_content = update_data['content']
        # Regex to find @username, @user.name, @user-name
        mention_usernames = list(set(MENTION_REGEX.findall(new_content or "")))
        mentioned_users = []
        if mention_usernames:
            query = select(User).where(User.username.in_(mention_usernames))
            mentioned_users = session.execute(query).scalars().all()

        update_data['mentioned_users'] = mentioned_users

    # 6. Delegate the core update to the model's method
    updated_post = Post.update(
        session=session,
        post_id=post_to_update.id,
        requesting_user_id=requesting_user_id,
        **update_data
    )
        
    # 7. --- Create Notifications for *New* Mentions ---
    # Check if 'mentioned_users' was part of this update
    if 'mentioned_users' in update_data:
        new_mentioned_users = update_data['mentioned_users']
        for user in new_mentioned_users:
            # Don't notify self-mentions
            # Don't notify users who were *already* mentioned
            if user.id != requesting_user_id and user.id not in old_mention_ids:
                new_notification = Notification.create(
                    session=session,
                    recipient_user_id=user.id,
                    actor_user_id=requesting_user_id,
                    action_type='mention',
                    target_type='post',
                    target_id=updated_post.id
                )

                # --- 3. ADD THIS SOCKET LOGIC ---
                if new_notification:
                    session.flush() # Flush to get notification ID
                    
                    # B. Manually attach objects for the serializer
                    new_notification.actor = requesting_user
                    new_notification.target_object = updated_post
                    
                    # C. Serialize the data
                    serialized_data = serialize_notification(new_notification)
                    
                    # D. Emit to the specific user's room
                    socketio.emit(
                        'new_notification',
                        serialized_data,
                        to=f"user_{user.id}"
                    )

    return updated_post
