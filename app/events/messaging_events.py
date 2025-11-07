from flask import request, current_app
from flask_socketio import emit, join_room, leave_room
import jwt as pyjwt
from sqlalchemy.orm import Session

# Import app components
from app.extensions import db, socketio # socketio instance is key
from app.models import User # Import models
from app.exceptions import (
    PermissionDeniedError,
    UserNotFoundError,
)

# Helper uses socketio.server session storage
def _get_user_id_from_sid(sid):
    """Safely retrieves the user_id stored via socketio.server.get_session."""
    try:
        # Use namespace='/' for default namespace handlers
        session_data = socketio.server.get_session(sid, namespace='/') or {}
        return session_data.get('user_id')
    except KeyError:
        current_app.logger.warning(f"SID {sid} not found in Socket.IO server session store during get.")
        return None

# ================================================
# ---> 1. HANDLES CONNECTION & AUTHENTICATION <---
# ================================================
@socketio.on('connect')
def handle_connect(auth=None):
    """
    Handles connection, verifies JWT (incl. signature!), checks user existence,
    and stores user ID via socketio.server.save_session.
    """
    # 1. Get the access token from the cookie
    # The default cookie name for flask-jwt-extended is 'access_token_cookie'
    access_token = request.cookies.get('access_token_cookie')
    if not access_token or not isinstance(access_token, str) or access_token.count('.') != 2:
        current_app.logger.warning("Socket connection: No token provided.")
        return False # Reject

    user_id = None # Define for logging scope
    try:
        secret = current_app.config['JWT_SECRET_KEY']
        token_data = pyjwt.decode(
            access_token, secret, algorithms=["HS256"],
            options={"verify_signature": True, "verify_exp": True}
        )
        user_identity = token_data['sub']
        user_id = int(user_identity)

        user = db.session.get(User, user_id)
        if not user:
            current_app.logger.warning(f"Socket connection: Authenticated User ID {user_id} not found in DB.")
            return False # Reject
        
        socketio.server.save_session(request.sid, {'user_id': user_id}, namespace='/')

        current_app.logger.info(f"User {user_id} connected via SocketIO with SID {request.sid}")
        join_room(f"user_{user_id}") # Join user-specific room
        return True 

    except (pyjwt.ExpiredSignatureError, pyjwt.InvalidTokenError, ValueError, KeyError) as e:
        key_info = f" accessing key '{e.args[0]}'" if isinstance(e, KeyError) else ""
        current_app.logger.error(f"Socket authentication failed ({type(e).__name__}{key_info}): {e}")
        db.session.rollback() 
        return False
    except Exception as e:
        current_app.logger.error(f"Socket connection failed (Unexpected): {type(e).__name__} - {e}", exc_info=True)
        db.session.rollback()
        return False

# ===============================
# ---> 2. HANDLES DISCONNECT <---
# ===============================
@socketio.on('disconnect')
def handle_disconnect(): 
    """ Handles client disconnection and optionally cleans up session map. """
    user_id = None # Define for logging scope
    sid = request.sid # Get sid before potential context loss
    try:
        user_id = _get_user_id_from_sid(sid) or 'Unknown user'
        current_app.logger.info(f"User {user_id} disconnected (SID={sid}).")
    except KeyError:
        # Session might already be gone
        current_app.logger.debug(f"Session not found for SID {sid} during disconnect (likely already gone).")
    except Exception as e:
        current_app.logger.error(f"Error during disconnect for SID {sid}: {e}", exc_info=True)