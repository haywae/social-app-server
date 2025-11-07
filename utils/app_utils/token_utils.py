import jwt
from flask_jwt_extended import get_csrf_token
from datetime import datetime, timezone
import logging
from app.exceptions import TokenDecodeError

logger = logging.getLogger(__name__)

class TokenUtil:
    """A stateless utility class for handling JWT and CSRF token operations."""

    @staticmethod
    def decode_token(token: str, secret_key: str) -> dict:
        """
        Decodes a JWT token.
        Parameters:
            token (str): The JWT token to decode.
        Returns:
            dict: The decoded token payload.
        Raises TokenDecodeError for any decoding issues.
        """
        try:
            return jwt.decode(token, secret_key, algorithms=['HS256'])
        except jwt.ExpiredSignatureError as e:
            logger.warning("Token expired.")
            raise TokenDecodeError("Token has expired.") from e
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token error: {e}")
            raise TokenDecodeError("Invalid token.") from e
        except Exception as e:
            logger.error(f"Unexpected token error: {e}")
            raise TokenDecodeError("Unexpected error during token decoding.") from e

    @staticmethod
    def get_token_expiry_datetime(token: str, secret_key: str) -> datetime:
        """
            Decodes a token and returns its expiration time as a timezone-aware datetime object.
            Parameters:
                token (str): The JWT token to decode.
                secret_key (str): The secret key used to decode the token.
            Returns:
                datetime: The expiration time of the token as a timezone-aware datetime object.
            Raises TokenDecodeError if the token is invalid or missing the 'exp' claim.
        """
        decoded_token = TokenUtil.decode_token(token, secret_key)
        try:
            exp_timestamp = decoded_token['exp']
            return datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        except KeyError as e:
            raise TokenDecodeError("Token is missing the 'exp' claim.") from e
        except (TypeError, ValueError) as e:
            raise TokenDecodeError(f"Invalid expiration timestamp in token: {exp_timestamp}") from e
    
    @staticmethod
    def get_token_expiry_unix(token: str, secret_key: str) -> int:
        """
            Decodes a token and returns its expiration time as a Unix timestamp.
            Parameters:
                token (str): The JWT token to decode.
                secret_key (str): The secret key used to decode the token.
            Returns:
                int: The expiration time of the token as a Unix timestamp.
            Raises TokenDecodeError if the token is invalid or missing the 'exp' claim.
        """
        decoded_token = TokenUtil.decode_token(token, secret_key)
        try:
            return decoded_token['exp']
        except KeyError as e:
            raise TokenDecodeError("Token is missing the 'exp' claim.") from e

    @staticmethod
    def get_token_jti(token: str, secret_key: str) -> str:
        """
            Decodes a token and returns its JTI (JWT ID).
            Parameters:
                token (str): The JWT token to decode.
                secret_key (str): The secret key used to decode the token.
            Returns:
                str: The JTI of the token.
            Raises TokenDecodeError if the token is invalid or missing the 'jti' claim.
        """
        decoded_token = TokenUtil.decode_token(token, secret_key)
        try:
            return decoded_token['jti']
        except KeyError as e:
            raise TokenDecodeError("Token is missing the 'jti' claim.") from e

    @staticmethod
    def generate_csrf_values(access_token: str, refresh_token: str) -> dict:
        """
            Extracts CSRF tokens from the given JWTs.
            Uses Flask-JWT-Extended's get_csrf_token function to generate CSRF tokens.
            Parameters:
                access_token (str): The JWT access token.
                refresh_token (str): The JWT refresh token.
            Returns:
                dict: A dictionary containing 'csrf_access_token' and 'csrf_refresh_token'.
            Raises TokenDecodeError if CSRF token generation fails.
        """
        try:
            csrf_access = get_csrf_token(access_token)
            csrf_refresh = get_csrf_token(refresh_token)
            return {
                "csrf_access_token": csrf_access,
                "csrf_refresh_token": csrf_refresh
            }
        except Exception as e:
            logger.error(f"Error generating CSRF tokens: {e}")
            raise TokenDecodeError("Could not generate CSRF tokens.") from e
