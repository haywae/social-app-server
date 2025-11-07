from flask import make_response, jsonify
from flask_jwt_extended import unset_jwt_cookies
from app.extensions import jwt
import logging

#------------------------------------------
# Custom error handlers for JWT operations
#------------------------------------------

@jwt.expired_token_loader
def my_expired_token_callback(jwt_header: dict, jwt_payload: dict) -> tuple:
    """
    Callback function executed when an expired JWT is encountered.
    It checks if the expired token was an access or refresh token and
    returns a specific error message. For expired refresh tokens, it also
    clears the client-side cookies.
    """
    token_type = jwt_payload.get("type", "access")
    
    if token_type == 'refresh':
        # If a refresh token expires, the user must log in again.
        response = make_response(jsonify({
            'message': 'Your refresh token has expired. Please log in again.',
            'error': 'refresh_token_expired',
            'type': 'refresh',
            'source': 'jwt'
        }), 401)
        unset_jwt_cookies(response)
        logging.warning("Expired refresh token presented.")
        return response
    
    logging.warning("Expired access token presented.")
    response_data = {
        'message': 'Access Token has expired',
        'error': 'access_token_expired',
        'type': 'access',
        'source': 'jwt'
    }
    return jsonify(response_data), 401

@jwt.invalid_token_loader
def my_invalid_token_callback(error_string: str) -> tuple:
    """
    Callback function for any token that is invalid (e.g., bad signature,
    malformed). This is a general catch-all for invalid tokens.
    """
    logging.error(f"Invalid token received: {error_string}")
    return {
        'message': 'The provided token is invalid.',
        'error': 'invalid_token',
        'type': 'unknown',
        'source': 'jwt'
    }, 401

@jwt.unauthorized_loader
def unauthorized_callback(error_string: str) -> tuple:
    """
    Callback function for requests to protected endpoints that are missing a JWT.
    """
    logging.warning(f"Unauthorized access attempt: {error_string}")
    return {
        'message': 'Authorization token is missing.',
        'error': 'authorization_required',
        'type': 'unknown',
        'source': 'jwt'
    }, 401

