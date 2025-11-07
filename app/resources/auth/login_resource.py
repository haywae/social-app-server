from flask import request, current_app, make_response, jsonify
from flask_restful import Resource
from sqlalchemy.exc import SQLAlchemyError

from app.services import login_user, get_user_details_service
from app.exceptions import InvalidCredentialsError
from app.extensions import db
from app.resources.auth._helper import serialize_basic_user
from utils.app_utils.cookie_utils import set_auth_cookies

class LoginResource(Resource):
    """
    API Resource for handling user login.
    This endpoint receives user credentials, passes them to the service layer
    for authentication and token generation, and sets the appropriate
    HTTP-only cookies in the response.
    """
    def post(self):
        """
        Processes a POST request to authenticate a user.

        Expects a JSON payload with the following keys:
        - loginIdentifier (str): The user's username or email.
        - password (str): The user's password.

        Returns:
            - 200 OK: If login is successful. The response body contains user info
              and CSRF tokens, while JWTs are set in secure cookies.
            - 401 Unauthorized: If the credentials are invalid.
            - 400 Bad Request: If the input data is missing.
            - 500 Internal Server Error: For unexpected server issues.
        """
        
        data: dict = request.get_json()
        if not data:
            return {'message': 'No input data provided'}, 400

        try:
            # The API layer calls the service layer to handle all business logic.
            login_data = login_user(
                session=db.session,
                login_identifier=data.get('loginIdentifier'),
                password=data.get('password')
            )

            user_with_details = get_user_details_service(session=db.session, user_id=login_data['user'].id)
            
            user_json = serialize_basic_user(user_with_details)
            
            db.session.commit()

            # The API layer prepares the JSON response body.
            response_body = {
                'message': 'Login Successful',
                'user': user_json,
                'csrf_access_token': login_data['csrf_access_token'],
                'csrf_refresh_token': login_data['csrf_refresh_token'],
                'access_token_exp': login_data['access_token_exp'],
            }
            
            # The API layer creates the response and sets the cookies.
            response = make_response(jsonify(response_body), 200)
            set_auth_cookies(
                response, 
                login_data['access_token'], 
                login_data['refresh_token']
            )
            return response

        # The API layer translates service errors into HTTP responses.
        except InvalidCredentialsError as e:
            db.session.rollback()
            return {'message': str(e)}, 401
        except ValueError as e:
            db.session.rollback()
            return {'message': str(e)}, 400
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An unexpected error occurred during login: {e}")
            return {'message': 'An unexpected error occurred.'}, 500
