from .login_resource import LoginResource
from .logout_resource import LogoutResource
from .auth_check_resource import AuthCheckResource
from .refresh_token_resource import RefreshTokenResource
from .google_login_resource import GoogleLoginResource


#========================================================================================
# 1. Dictionaries are used for simple responses that wont be used within the code
# 2. make_response handles more complex responses that will be used after declaration
# 3. Flask SQL automatically handles session commits, rollbacks and close
#========================================================================================

#-----Associated resource[ AuthCheckResource, LoginResource, LogoutResource, RefreshTokenResource, RegisterResource, ResetPassword, RequestPasswordReset ]

__all__ = ['LoginResource', 'LogoutResource', 'AuthCheckResource', 'RefreshTokenResource', 'GoogleLoginResource']