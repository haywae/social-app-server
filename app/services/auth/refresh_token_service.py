from datetime import datetime, timezone
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt
from app.services.redis import add_token_to_blocklist, is_token_blocklisted
from app.exceptions import InvalidTokenError
from utils.app_utils.token_utils import TokenUtil
from app.extensions import redis_client
import json

GRACE_PERIOD_SECONDS = 10

def _get_grace_period_key(jti: str) -> str:
    """Returns the Redis key for the grace period cache."""
    return f"grace_jti:{jti}"

def refresh_user_tokens(user_id: str, current_refresh_jti: str) -> dict:
    """
    Handles the business logic for refreshing JWTs.
    1. Checks if the current refresh token has been revoked.
    2. Revokes the current refresh token by adding it to the blocklist.
    3. Creates a new access and refresh token.
    4. Returns a dictionary of the new token data.
    """

    # 1. --- Check for grace period ---
    grace_key = _get_grace_period_key(current_refresh_jti)
    cached_data = redis_client.get(grace_key)

    if cached_data:
        # This token was *just* refreshed. This is a race condition.
        # Return the *same* new token data to this "losing" tab.
        current_app.logger.info(f"Grace period hit for JTI: {current_refresh_jti}. Returning cached data.")
        return json.loads(cached_data)

    # 2. --- Security Check ---
    # Check if the JTI of the token used for this request is already blocklisted.
    if is_token_blocklisted(current_refresh_jti):
        # This is a critical security event. A revoked token is being reused.
        raise InvalidTokenError("The refresh token has been revoked.")
  
    # 3. --- Generate New Tokens ---
    new_access_token = create_access_token(identity=user_id)
    new_refresh_token = create_refresh_token(identity=user_id)

    # 4. --- Get New Token Data ---
    secret_key = current_app.config['JWT_SECRET_KEY']
    csrf_values = TokenUtil.generate_csrf_values(new_access_token, new_refresh_token)
    access_exp_dt = TokenUtil.get_token_expiry_unix(new_access_token, secret_key)
    refresh_exp_dt = TokenUtil.get_token_expiry_unix(new_refresh_token, secret_key)

    token_data = {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "csrf_access_token": csrf_values['csrf_access_token'],
        "csrf_refresh_token": csrf_values['csrf_refresh_token'],
        "access_token_exp": access_exp_dt,
        "refresh_token_exp": refresh_exp_dt
    }

    # --- 5. Set the grace period cache ---
    # Store the new token data in Redis for 10 seconds, keyed by the
    # JTI of the token that was *just used*.
    redis_client.set(grace_key, json.dumps(token_data), ex=GRACE_PERIOD_SECONDS)

    
    # --- 6. Revoke Current Token ---
    # Immediately add the JTI of the current refresh token to the blocklist to prevent reuse.
    # The expiration can be taken from the token itself.
    current_token_payload = get_jwt()
    expires_at = datetime.fromtimestamp(current_token_payload['exp'], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    expires_in_seconds = int((expires_at - now).total_seconds())
    add_token_to_blocklist(current_refresh_jti, max(1, expires_in_seconds))

    return token_data