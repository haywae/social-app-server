# This service layer contains the business logic for follow/unfollow actions.

from sqlalchemy.orm import Session
from app.models import User, Follower, Notification
from app.exceptions import UserNotFoundError
from app.extensions import socketio
from app.resources.notitifications.notification_list_resource import serialize_notification

def follow_user_service(session: Session, follower_id: int, followed_username: str):
    """
    Handles the business logic for making one user follow another.

    This includes:
    1. Finding the user to be followed.
    2. Creating the Follower relationship.
    3. Creating a notification for the followed user.
    """
    # --- 1. Get the actor (the user doing the following) ---
    actor_user = session.get(User, follower_id)
    if not actor_user:
        raise UserNotFoundError("Your user account was not found.")
    
    # --- 2. Find the target user ---
    user_to_follow = User.get_by_identifier(session, identifier=followed_username)
    if not user_to_follow:
        raise UserNotFoundError("The user you are trying to follow does not exist.")

    # --- 3. Create the Follow relationship ---
    # - The Follower.create_follow model method already handles self-following and duplicate follow checks
    # - It raises a ValueError if necessary.
    Follower.create_follow(
        session=session,
        follower_id=follower_id,
        followed_id=user_to_follow.id
    )

    # --- 4. Create a Notification ---
    # This is a key side effect of the follow action.
    new_notification=Notification.create(
        session=session,
        recipient_user_id=user_to_follow.id,
        actor_user_id=follower_id,
        action_type='follow',
        target_type='user',
        target_id=follower_id # The target/subject is the user who initiated the follow
    )

    # --- 5. ADD THIS SOCKET LOGIC ---
    if new_notification:
        session.flush() # Flush to get notification ID
        
        # B. Manually attach actor for the serializer
        # (The serializer doesn't need a target_object for 'follow' actions)
        new_notification.actor = actor_user
        
        # C. Serialize the data
        serialized_data = serialize_notification(new_notification)
        
        # D. Emit to the specific user's room
        socketio.emit(
            'new_notification',
            serialized_data,
            to=f"user_{user_to_follow.id}"
        )
    
    return True

def unfollow_user_service(session: Session, follower_id: int, followed_username: str):
    """
    Handles the business logic for making one user unfollow another.
    """
    user_to_unfollow = User.get_by_identifier(session, identifier=followed_username)
    if not user_to_unfollow:
        raise UserNotFoundError("The user you are trying to unfollow does not exist.")

    # The Follower.delete_follow method handles deleting the relationship.
    was_deleted = Follower.delete_follow(
        session=session,
        follower_id=follower_id,
        followed_id=user_to_unfollow.id
    )
    
    if not was_deleted:
        # This provides clear feedback if the user wasn't following them in the first place.
        raise ValueError("You are not currently following this user.")
        
    # Note: We typically don't delete the original "follow" notification.
    
    return True
