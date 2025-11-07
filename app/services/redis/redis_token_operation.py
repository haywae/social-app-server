from app.extensions import redis_client
import logging
from redis.exceptions import ConnectionError

logger = logging.getLogger(__name__)

def add_token_to_blocklist(jti: str, expires_in_seconds: int):
    """
    Adds a token's JTI to the Redis blocklist to revoke it.
    The token is set to expire automatically from Redis.
    
    Arguments:
        jti: The unique identifier of the JWT.
        expires_in_seconds: The remaining lifetime of the token in seconds.
    
    Returns:
        None: If the operation is successful.

    """
    try:
        # Using 'setex' sets the key with an expiration time in seconds.
        redis_client.setex(jti, expires_in_seconds, "revoked")
        logger.info(f"Token {jti} added to blocklist.")
    except ConnectionError as e:
        # If Redis is down, we log the error but do not crash the application.
        # The token will simply not be blocklisted, which is an acceptable failure mode.
        logger.error(f"Failed to add token {jti} to Redis blocklist: {e}")

def is_token_blocklisted(jti: str) -> bool:
    """
    Checks if a token's JTI is in the Redis blocklist.

    Arguments:
        jti: The unique identifier of the JWT.

    Returns:
        True if the token is blocklisted, False otherwise.
    """
    try:
        return redis_client.get(jti) is not None
    except ConnectionError as e:
        # If Redis is down, we cannot confirm the token is valid.
        logger.error(f"CRITICAL: Could not connect to Redis. Blocklist check is disabled: {e}")
        return False