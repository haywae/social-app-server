from app.models import User


def serialize_basic_user(user: User) -> dict:
    """
    Serializes a User object into a dictionary with only the essential
    info needed for the global auth state.
    """
    hasPassword = False
    if user.hashed_password is not None:
        hasPassword = True
    return {
        "id": str(user.public_id),
        "username": user.username,
        "displayName": user.display_name,
        "profilePictureUrl": user.profile_picture_url,
        "isEmailVerified": user.is_email_verified,
        "country": user.country, 
        "dateOfBirth": user.date_of_birth.isoformat() if user.date_of_birth else None,
        "hasPassword": hasPassword
    }