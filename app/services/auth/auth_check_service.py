from app.models import User
from app.exceptions import UserNotFoundError
from sqlalchemy.orm import Session

def get_user_by_id(session: Session, user_id: int | None) -> User | None:
    """
    Finds a user by their internal ID. 
    If user_id is None, returns None.

    Raises:
        UserNotFoundError: If a user_id is provided but no user is found.

    Returns:
        The User object or None.
    """
    if user_id is None:
        return None
    
    user = User.get_by_id(session, user_id=user_id)
    if not user:
        raise UserNotFoundError("User not found.")
    return user
