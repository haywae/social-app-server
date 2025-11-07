from sqlalchemy.orm import Session
from flask import current_app
from werkzeug.datastructures import FileStorage
from app.models import User
from app.exceptions import UserNotFoundError
from app.services.media.s3_service import upload_file_to_s3, delete_file_from_s3

def update_profile_picture_service(session: Session, user_id: int, file: FileStorage) -> str:
    """
    Handles the business logic for updating a user's profile picture.

    1. Fetches the user.
    2. Gets the current profile picture URL to delete it after a successful upload.
    3. Uploads the new file to S3.
    4. Updates the user's profile_picture_url in the database.
    5. Deletes the old profile picture from S3.
    """
    user = session.get(User, user_id)
    if not user:
        raise UserNotFoundError("User not found.")

    # Store the old URL for deletion later
    old_picture_url = user.profile_picture_url
    bucket_name = current_app.config["S3_BUCKET"]
    
    # Upload the new picture to S3
    new_picture_url = upload_file_to_s3(file, bucket_name)
    if not new_picture_url:
        raise ConnectionError("Failed to upload profile picture to S3.")

    # Update the user model with the new URL
    user.profile_picture_url = new_picture_url
    
    # After a successful upload and DB update, delete the old picture from S3
    if old_picture_url:
        delete_file_from_s3(old_picture_url, bucket_name)

    return new_picture_url

def delete_profile_picture_service(session: Session, user_id: int) -> bool:
    """
    Handles the business logic for deleting a user's profile picture.

    1. Fetches the user.
    2. Deletes the picture file from S3 if it exists.
    3. Sets the user's profile_picture_url to None in the database.
    """
    user = session.get(User, user_id)
    if not user:
        raise UserNotFoundError("User not found.")
    
    # If there's no picture to delete, we can consider it a success.
    if not user.profile_picture_url:
        return True
    
    # Delete the file from S3
    bucket_name = current_app.config["S3_BUCKET"]
    success = delete_file_from_s3(user.profile_picture_url, bucket_name)
    
    if success:
        # If S3 deletion is successful, clear the URL in the database
        user.profile_picture_url = None
        return True
    
    return False
