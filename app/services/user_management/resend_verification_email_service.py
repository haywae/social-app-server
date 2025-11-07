from sqlalchemy.orm import Session
from app.models import User
from app.services.account_management.email_change_service import send_account_verification_email_service

# NOTE: This is currently unused, but it's kept here for potential future use.
def resend_verification_email(session: Session, email: str) -> None:
    """
    Handles the logic for resending a verification email to an unauthenticated user.
    """
    if email:
        email = email.strip()

    # 1. Find the user by their email address.
    user = User.get_by_identifier(session, identifier=email)

    # If no user is found, we don't raise an error to prevent user enumeration.
    # We also check if the user is already verified.
    if not user or user.is_email_verified:
        return

    # 2. If the user exists and is not verified, call the existing service.
    send_account_verification_email_service(session=session, user=user)