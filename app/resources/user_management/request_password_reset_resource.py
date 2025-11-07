from flask import request, current_app
from flask_restful import Resource

# Import the new service function and custom exceptions
from app.services import request_password_reset
from app.exceptions import InvalidEmailFormatError
from app.extensions import db



class RequestPasswordResetResource(Resource):
    """
    API Resource for handling password reset requests.
    """
    def post(self):
        """
        Processes a POST request to initiate a password reset.

        Expects a JSON payload with the key "email".
        
        Returns:
            - 200 OK: Always returns a generic success message, regardless of
              whether the email existed, to prevent user enumeration.
            - 400 Bad Request: If the email format is invalid.
            - 500 Internal Server Error: If the email fails to send.
        """
        data: dict = request.get_json()
        if not data or 'email' not in data:
            return {'message': 'Email is required.'}, 400

        try:
            # Delegate all logic to the service layer.
            request_password_reset(session=db.session, email=data.get('email'))
            
            # SECURITY: Always return a generic success message.
            return {'message': 'If an account with that email exists, a password reset link has been sent.'}, 200

        except InvalidEmailFormatError as e:
            return {'message': str(e)}, 400
        except Exception as e:
            # This will catch errors from the mail sending utility.
            current_app.logger.exception(f"Failed to process password reset request: {e}")
            return {'message': 'An error occurred while processing your request.'}, 500
