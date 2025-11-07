from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.datastructures import FileStorage

from app.services import delete_profile_picture_service, update_profile_picture_service
from app.exceptions import UserNotFoundError
from app.extensions import db

class ProfilePictureResource(Resource):
    """
    API Resource for updating the user's profile picture.
    """
    @jwt_required()
    def post(self):
        """Processes a POST request to upload a new profile picture."""

        # Check if the post request has the profile picture key
        if 'profile_picture' not in request.files:
            return {'message': 'No file part in the request.'}, 400
        
        file: FileStorage = request.files['profile_picture']
        
        # If user does not select a file, the browser submits an empty file without a filename
        if file.filename == '':
            return {'message': 'No selected file.'}, 400

        try:
            user_id = int(get_jwt_identity())
            
            # Delegate business logic to the service layer
            new_url = update_profile_picture_service(
                session=db.session,
                user_id=user_id,
                file=file
            )
            
            db.session.commit()
            
            return {'message': 'Profile picture updated successfully', 'profile_picture_url': new_url}, 200

        except UserNotFoundError as e:
            db.session.rollback()
            return {'message': str(e)}, 404
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error uploading profile picture: {e}", exc_info=True)
            return {'message': 'An error occurred during file upload.'}, 500
        
    @jwt_required()
    def delete(self):
        """Processes a DELETE request to remove the user's profile picture."""
        try:
            user_id = int(get_jwt_identity())
            
            # Delegate business logic to the service layer
            success = delete_profile_picture_service(
                session=db.session,
                user_id=user_id
            )

            if not success:
                 # The service returns False if S3 deletion fails
                raise ConnectionError("Failed to delete picture from cloud storage.")

            db.session.commit()
            return {'message': 'Profile picture deleted successfully'}, 200
        
        except UserNotFoundError as e:
            db.session.rollback()
            return {'message': str(e)}, 404
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting profile picture: {e}", exc_info=True)
            return {'message': 'An error occurred while deleting the profile picture.'}, 500






