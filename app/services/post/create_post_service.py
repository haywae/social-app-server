import re
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import Post, Hashtag, User, Notification
from app.exceptions import UserNotFoundError
from utils.model_utils.enums import PostType, PostVisibility
from utils.app_utils.regex_patterns import MENTION_REGEX
from app.extensions import socketio
from app.resources.notitifications.notification_list_resource import serialize_notification


def create_post(
    session: Session, 
    user_id: int, 
    content: str | None = None, 
    media_url: str | None = None, 
    tag_names: list[str] | None = None,
    post_type: PostType = PostType.REGULAR,
    **kwargs
) -> Post:
    """
    Handles the business logic for creating a new post and associating hashtags.

    This includes:
    1. Validating that the user exists.
    2. Creating the core Post object.
    3. Processing and associating any provided hashtags.
    """

    # 1. --- Validation ---
    # Ensure the user creating the post actually exists.
    user = session.get(User, user_id)
    if not user:
        raise UserNotFoundError("Cannot create a post for a non-existent user.")
    
    # 2. --- Handle Hashtags ---
    hashtag_objects = []
    if tag_names:
        unique_tag_names = set(tag_names)
        hashtag_objects = [Hashtag.find_or_create(session, name) for name in unique_tag_names]

    # 3. --- Parse Mentions ---
    mentioned_users = []
    if content: # Only parse if there is content
    # Regex now includes dots and hyphens
        mention_usernames = list(set(MENTION_REGEX.findall(content or "")))
        if mention_usernames:
            query = select(User).where(User.username.in_(mention_usernames))
            mentioned_users = session.execute(query).scalars().all()
    
    # 4. --- Create the Post ---
    new_post = Post.create(
        session=session,
        user_id=user_id,
        content=content,
        media_url=media_url,
        hashtags=hashtag_objects,
        mentioned_users=mentioned_users,
        visibility=kwargs.get("visibility", PostVisibility.PUBLIC),
        location_coords=kwargs.get("location_coords"),
        post_type=post_type
    )

    session.flush()

    # 5. --- Create Notifications for Mentions ---
    for mentioned_user in mentioned_users:
        if mentioned_user.id != user_id: # Don't notify on self-mention
            new_notification = Notification.create(
                session=session,
                recipient_user_id=mentioned_user.id,
                actor_user_id=user_id,
                action_type='mention',
                target_type='post',
                target_id=new_post.id
            )
    
            if new_notification:
                # A. Flush to get the notification's relationships ready
                session.flush()
                
                # B. Manually attach objects for the serializer to work
                # This mimics the logic in get_notifications_service
                new_notification.actor = user # The user who created the post
                new_notification.target_object = new_post # The post that was created
                
                # C. Serialize the notification
                serialized_data = serialize_notification(new_notification)
                
                # D. Emit the event ONLY to the mentioned user's personal room
                socketio.emit(
                    'new_notification',
                    serialized_data,
                    to=f"user_{mentioned_user.id}"
                )

    return new_post