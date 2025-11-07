from app.models import User

def serialize_user(user: User) -> dict:
    """
    Serializes a User SQLAlchemy object into a dictionary that matches the
    frontend's UserData interface.
    """
    if not user:
        return None

    # The User model has relationships like `followers` and `following`.
    # We can use Python's `len()` on these lists to get the counts.
    # This requires that the relationships were eagerly loaded for good performance.
    follower_count = len(user.followers) if hasattr(user, 'followers') else 0
    following_count = len(user.following) if hasattr(user, 'following') else 0
    post_count = len(user.posts) if hasattr(user, 'posts') else 0

    return {
        "id": str(user.public_id),
        "username": user.username,
        "displayName": user.display_name,
        "profilePictureUrl": user.profile_picture_url,
        "bio": user.bio,
        "followerCount": follower_count,
        "followingCount": following_count,
        "postCount": post_count,
        "joinedDate": user.created_at.isoformat() if user.created_at else None
    }
