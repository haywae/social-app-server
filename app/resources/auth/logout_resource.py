from flask import make_response, jsonify, current_app
from flask_restful import Resource
from flask_jwt_extended import unset_jwt_cookies, jwt_required, get_jwt
from datetime import timezone, datetime
from app.services import add_token_to_blocklist



class LogoutResource(Resource):
    """
    API Resource for handling user logout.
    This endpoint invalidates the user's JWT by adding it to a server-side
    blocklist and clears the client-side cookies.
    """
    @jwt_required()
    def post(self):
        try:
            # 1. Get the current token's unique ID (JTI) and expiration
            token = get_jwt()
            jti = token['jti']

            # Calculate the remaining time until the token naturally expires
            expires_at = datetime.fromtimestamp(token['exp'], tz=timezone.utc)
            now = datetime.now(timezone.utc)
            expires_in_seconds = int((expires_at - now).total_seconds())
            
            # 2. Delegate the business logic (blocklisting) to the service layer
            
            # Only blocklist if the token hasn't already expired
            # Max(1, ...) ensures the expiration is always a positive integer.
            add_token_to_blocklist(jti, max(1, expires_in_seconds))

            # 3. Handle the API layer task of creating the response
            response_data = {'message': 'Logout successful'}
            response = make_response(jsonify(response_data), 200)

            # 4. Handle the API layer task of clearing cookies
            unset_jwt_cookies(response)
            
            return response
            
        except Exception as e:
            current_app.logger.error(f"Logout error: {e}")
            return {'message': 'Logout failed', 'error': str(e)}, 500
