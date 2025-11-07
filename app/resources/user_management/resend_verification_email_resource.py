from flask_jwt_extended import get_jwt_identity, jwt_required
from app.models.user_model import User
from app.services import resend_verification_email
from flask import current_app
from flask_restful import Resource, reqparse
from app import db
from app.services.account_management.email_change_service import send_account_verification_email_service

class ResendVerificationEmailResource(Resource):
    """API Resource for resending a verification email to an unauthenticated user."""
    
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True, help='Email is required.')
        data = parser.parse_args()

        try:
            resend_verification_email(session=db.session, email=data['email'])
            
            # IMPORTANT: The generic success message prevents attackers from using this endpoint to check which emails
            # are registered on the platform (user enumeration).
            return {'message': 'If an account with that email exists and requires verification, a new link has been sent.'}, 200

        except Exception as e:
            current_app.logger.error(f"Error resending verification email: {e}", exc_info=True)
            return {'message': 'An unexpected error occurred.'}, 500



class ResendVerificationForAuthenticatedUserResource(Resource):
    """
    API Resource for a logged-in, unverified user to request a new verification email.
    """
    @jwt_required()
    def post(self):
        try:
            # 1. Get the user's ID from their login token.
            user_id = get_jwt_identity()
            user = db.session.get(User, int(user_id))

            # 2. Perform validation.
            if not user:
                return {'message': 'User not found.'}, 404
            
            if user.is_email_verified:
                return {'message': 'This account has already been verified.'}, 400

            # 3. Call the reusable service to send the email.
            send_account_verification_email_service(session=db.session, user=user)
            
            return {'message': 'A new verification link has been sent to your email.'}, 200

        except Exception as e:
            current_app.logger.error(f"Error resending verification email for authenticated user: {e}", exc_info=True)
            return {'message': 'An unexpected error occurred.'}, 500