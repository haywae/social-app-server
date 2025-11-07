# app/exceptions.py

class AppBaseException(Exception):
    """Base exception for this application."""
    def __init__(self, message="An application error occurred."):
        self.message = message
        super().__init__(self.message)



class PermissionDeniedError(AppBaseException):
    """Raised when a user attempts an action without the necessary permissions."""
    def __init__(self, message="Permission denied."):
        self.message = message
        super().__init__(self.message)


#-------- Users -------
class UserNotFoundError(AppBaseException):
    """Raised when a user is not found in the database."""
    def __init__(self, message="User not found."):
        self.message = message
        super().__init__(self.message)


class UserAlreadyExistsError(AppBaseException):
    """Raised when trying to create a user that already exists."""
    def __init__(self, message="A user with this username or email already exists."):
        self.message = message
        super().__init__(self.message)


class InvalidEmailFormatError(AppBaseException):
    """Raised when an email has an invalid format."""
    def __init__(self, message="Invalid email format provided."):
        self.message = message
        super().__init__(self.message)


class InvalidCredentialsError(AppBaseException):
    """Raised when login credentials (e.g., password) are incorrect."""
    def __init__(self, message="Invalid username/email or password."):
        self.message = message
        super().__init__(self.message)


#-------- Posts -------
class PostNotFoundError(AppBaseException):
    """Raised when a post is not found in the database."""
    def __init__(self, message="Post not found."):
        self.message = message
        super().__init__(self.message)


#-------- Token -------
class TokenError(AppBaseException):
    """Base exception for token-related errors."""
    def __init__(self, message="A token-related error occurred."):
        self.message = message
        super().__init__(self.message)

class TokenDecodeError(TokenError):
    """Raised when a token cannot be decoded for any reason."""
    def __init__(self, message="Error decoding token."):
        self.message = message
        super().__init__(self.message)

class InvalidTokenError(TokenDecodeError):
    """Raised specifically for tokens that are structurally invalid or have a bad signature."""
    def __init__(self, message="The provided token is invalid."):
        self.message = message
        super().__init__(self.message)

class TokenExpiredError(TokenDecodeError):
    """Raised specifically for tokens that have expired."""
    def __init__(self, message="The token has expired."):
        self.message = message
        super().__init__(self.message)

