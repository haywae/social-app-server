import os
import redis
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_socketio import SocketIO
from .models import Base

IS_DEV = os.getenv('FLASK_ENV') == 'development'

db = SQLAlchemy(metadata=Base.metadata)
jwt = JWTManager()
mail = Mail()
migrate = Migrate()

if IS_DEV:
    socketio = SocketIO(logger=True, engineio_logger=True)
else:
    socketio = SocketIO()

# Get the Redis URL from environment variables, with a fallback for local development.
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")


# The decode_responses=True argument ensures that the values from Redis are automatically converted from bytes to strings.
redis_client = redis.StrictRedis.from_url(redis_url, decode_responses=True)

