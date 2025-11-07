from functools import wraps
from flask_jwt_extended import get_jwt_identity
from app.models import User
from utils.model_utils.enums import UserStatus
from app.extensions import db

def require_active_user(fn):
    """
    A decorator to ensure that the user making the request has an 'ACTIVE'
    account status.
    Decorated funtion doesnt need to check JWT identity anymore, it can get the current_user
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # 1. Get the user ID from the JWT token.
        user_id = get_jwt_identity()
        if not user_id:
            return {'message': 'Authentication required.'}, 401
            
        # 2. Fetch the full user object from the database.
        current_user = db.session.get(User, int(user_id))
        if not current_user:
            return {'message': 'User not found.'}, 404

        # 3. Check the account status.
        if current_user.account_status != UserStatus.ACTIVE:
            return {'message': 'Please verify your email to perform this action.'}, 403 # Forbidden

        # 4. If the check passes, run the original resource method.
        return fn(*args, current_user=current_user, **kwargs)
    return wrapper