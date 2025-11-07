from flask_jwt_extended import set_access_cookies, set_refresh_cookies
from flask import current_app, Response

def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """ Set JWT cookies in the response with correct, persistent expiration. """

    # 1. Manually get the expiration timedelta objects from the app config.
    access_token_expires = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES')
    refresh_token_expires = current_app.config.get('JWT_REFRESH_TOKEN_EXPIRES')

    # 2. Convert the timedelta objects to total seconds for the 'max_age' parameter.
    access_max_age = int(access_token_expires.total_seconds()) if access_token_expires else None
    refresh_max_age = int(refresh_token_expires.total_seconds()) if refresh_token_expires else None

    # 3. Explicitly pass the calculated 'max_age' in seconds to BOTH functions.
    set_access_cookies(response, access_token, max_age=access_max_age)
    set_refresh_cookies(response, refresh_token, max_age=refresh_max_age)