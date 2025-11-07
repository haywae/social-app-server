import boto3
import uuid
from flask import current_app
from botocore.exceptions import ClientError
import logging
from werkzeug.datastructures import FileStorage

def get_s3_client():
    """Initializes and returns a Boto3 S3 client."""
    return boto3.client(
        "s3",
        aws_access_key_id=current_app.config["S3_KEY"],
        aws_secret_access_key=current_app.config["S3_SECRET"],
        region_name=current_app.config["S3_REGION"]
    )

def upload_file_to_s3(file: FileStorage, bucket_name: str, folder: str = "profile-pictures") -> str | None:
    """
    Uploads a file object to an S3 bucket and returns the public URL.

    :param file: The FileStorage object from the request.
    :param bucket_name: The target S3 bucket.
    :param folder: The subfolder within the bucket to store the file.
    :return: The public URL of the uploaded file, or None if upload fails.
    """
    # Generate a unique filename to prevent overwrites
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    object_name = f"{folder}/{unique_filename}"
    
    s3_client = get_s3_client()
    try:
        s3_client.upload_fileobj(
            file,
            bucket_name,
            object_name,
            ExtraArgs={'ContentType': file.content_type}
        )
        
        return object_name

    except ClientError as e:
        logging.error(f"S3 Upload Error: {e}")
        return None

def delete_file_from_s3(object_key: str, bucket_name: str) -> bool:
    """
    Deletes a file from an S3 bucket using its full URL.

    :param file_url: The full public URL of the file to delete.
    :param bucket_name: The S3 bucket where the file is stored.
    :return: True if deletion was successful, False otherwise.
    """
    if not object_key:
        return True # Nothing to delete

    try:
        s3_client = get_s3_client()
        s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        return True
    except (ClientError, IndexError) as e:
        logging.error(f"S3 Deletion Error for Key {object_key}: {e}")
        return False