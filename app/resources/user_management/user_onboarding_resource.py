from flask import request, current_app, jsonify, make_response
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.services import get_user_details_service, complete_user_onboarding
from app.resources.auth._helper import serialize_basic_user
from app.exceptions import UserNotFoundError

class OnboardingResource(Resource):
    """
    API Resource for completing new user onboarding.
    """
    @jwt_required()
    def post(self):
        """
        Processes a POST request to complete user profile
        (DOB, Country)e.
        """
        data = request.get_json()
        user_id = int(get_jwt_identity())
        
        if not data:
            return {'message': 'No input data provided'}, 400

        try:
            updated_user = complete_user_onboarding(
                session=db.session,
                user_id=user_id,
                onboarding_data=data
            )
            
            # Get the full, serialized user object to send back
            # This ensures the frontend state is fully updated
            user_with_details = get_user_details_service(session=db.session, user_id=updated_user.id)
            user_json = serialize_basic_user(user_with_details)

            db.session.commit()
            
            return make_response(jsonify({
                'message': 'Profile completed successfully.',
                'user': user_json
            }), 200)

        except (ValueError, UserNotFoundError) as e:
            db.session.rollback()
            return {'message': str(e)}, 400
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An unexpected error occurred during onboarding: {e}")
            return {'message': 'An unexpected error occurred.'}, 500