class PostNotFoundError(Exception):
    """ Raised when the requested post is not found """
    def __init__(self, post_id):
        super().__init__(f"Post with ID {post_id} not found!")

class PermissionDeniedError(Exception):
    """ Raised when user does not have access to operation """
    def __init__(self, requesting_user_id):
        super().__init__(f"User with ID {requesting_user_id} does not have permission!")

class UserNotFoundError(Exception):
    """ Raised when the requested user is not found"""
    def __init__(self, user_id):
        super().__init__(f"User with ID {user_id} not found")