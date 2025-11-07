from flask import request, current_app, make_response, jsonify
from flask_restful import Resource
from sqlalchemy.exc import SQLAlchemyError

from app.services import login_or_register_google_user 
from app.services import get_user_details_service
from app.exceptions import InvalidCredentialsError
from app.extensions import db
from app.resources.auth._helper import serialize_basic_user
from utils.app_utils.cookie_utils import set_auth_cookies

class GoogleLoginResource(Resource):
    """
    API Resource for handling user login via Google OAuth.
    Receives a one-time authorization code from the frontend,
    exchanges it with Google, finds or creates a user,
    and returns auth tokens and cookies.
    """
    def post(self):
        data: dict = request.get_json()
        code = data.get('code')
        
        if not code:
            return {'message': 'No authorization code provided'}, 400

        try:
            # 1. Call the service
            login_data = login_or_register_google_user(
                session=db.session,
                code=code
            )

            # 2. Get full user details (same as regular login)
            user_with_details = get_user_details_service(session=db.session, user_id=login_data['user'].id)
            user_json = serialize_basic_user(user_with_details)
            
            db.session.commit()

            # 3. Build the response body (same as regular login)
            response_body = {
                'message': 'Login Successful',
                'user': user_json,
                'csrf_access_token': login_data['csrf_access_token'],
                'csrf_refresh_token': login_data['csrf_refresh_token'],
                'access_token_exp': login_data['access_token_exp'],
            }
            
            # 4. Create response and set cookies (same as regular login)
            response = make_response(jsonify(response_body), 200)
            set_auth_cookies(
                response, 
                login_data['access_token'], 
                login_data['refresh_token']
            )
            return response

        except InvalidCredentialsError as e:
            db.session.rollback()
            return {'message': str(e)}, 401
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An unexpected error occurred during Google login: {e}")
            return {'message': 'An unexpected error occurred.'}, 500