from flask import make_response, jsonify, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, unset_jwt_cookies
from flasgger import swag_from

# Import the new service function and custom exceptions
from app.services.auth import refresh_user_tokens
from app.exceptions import InvalidTokenError
from app.resources._docs_text import refresh_token_text
from utils.app_utils.cookie_utils import set_auth_cookies

class RefreshTokenResource(Resource):
    """
    API Resource for refreshing JWTs using a valid refresh token.
    """

    @jwt_required(refresh=True)
    @swag_from(refresh_token_text)
    def post(self):
        """
        Processes a POST request to generate a new access and refresh token.
        
        Returns:
            - 200 OK: If token refresh is successful. New tokens are set in cookies.
            - 401 Unauthorized: If the refresh token is invalid or has been revoked.
            - 500 Internal Server Error: For unexpected server issues.
        """
        try:
            # 1. Get identity and JTI from the incoming refresh token.
            user_id = get_jwt_identity()
            current_jti = get_jwt()['jti']
            # 2. Delegate all logic to the service layer.
            token_data = refresh_user_tokens(user_id=user_id, current_refresh_jti=current_jti)

            # 3. Prepare the JSON response body.
            response_body = {
                'message': 'Token Refreshed',
                'access_token_exp': token_data['access_token_exp'],
                'csrf_access_token': token_data['csrf_access_token'],
                'csrf_refresh_token': token_data['csrf_refresh_token'],
            }
            
            # 4. Create the response and set the new tokens in cookies.
            response = make_response(jsonify(response_body), 200)
            set_auth_cookies(
                response, 
                token_data['access_token'], 
                token_data['refresh_token']
            )
            return response

        except InvalidTokenError as e:
            response = make_response(jsonify({'message': str(e)}), 401)
            unset_jwt_cookies(response)
            return response

        except Exception as e:
            current_app.logger.error(f"Token refresh error: {e}", exc_info=True)
            return {'message': 'Failed to refresh token'}, 500
