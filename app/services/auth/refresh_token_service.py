from datetime import datetime, timezone
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt
from app.services.redis import add_token_to_blocklist, is_token_blocklisted
from app.exceptions import InvalidTokenError
from utils.app_utils.token_utils import TokenUtil

def refresh_user_tokens(user_id: str, current_refresh_jti: str) -> dict:
    """
    Handles the business logic for refreshing JWTs.
    1. Checks if the current refresh token has been revoked.
    2. Revokes the current refresh token by adding it to the blocklist.
    3. Creates a new access and refresh token.
    4. Returns a dictionary of the new token data.
    """
    # 1. --- Security Check ---
    # Check if the JTI of the token used for this request is already blocklisted.
    if is_token_blocklisted(current_refresh_jti):
        # This is a critical security event. A revoked token is being reused.
        raise InvalidTokenError("The refresh token has been revoked.")

    # 2. --- Revoke Current Token ---
    # Immediately add the JTI of the current refresh token to the blocklist to prevent reuse.
    # The expiration can be taken from the token itself.
    current_token_payload = get_jwt()
    expires_at = datetime.fromtimestamp(current_token_payload['exp'], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    expires_in_seconds = int((expires_at - now).total_seconds())
    add_token_to_blocklist(current_refresh_jti, max(1, expires_in_seconds))
        
    # 3. --- Generate New Tokens ---
    new_access_token = create_access_token(identity=user_id)
    new_refresh_token = create_refresh_token(identity=user_id)

    # 4. --- Get New Token Data ---
    secret_key = current_app.config['JWT_SECRET_KEY']
    csrf_values = TokenUtil.generate_csrf_values(new_access_token, new_refresh_token)
    access_exp_dt = TokenUtil.get_token_expiry_unix(new_access_token, secret_key)
    refresh_exp_dt = TokenUtil.get_token_expiry_unix(new_refresh_token, secret_key)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "csrf_access_token": csrf_values['csrf_access_token'],
        "csrf_refresh_token": csrf_values['csrf_refresh_token'],
        "access_token_exp": access_exp_dt,
        "refresh_token_exp": refresh_exp_dt
    }
