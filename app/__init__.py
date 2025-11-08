from datetime import timedelta
import os
from flask import Flask, request
from flask_cors import CORS
from .config import Config
from .extensions import db, jwt, mail, migrate, socketio
from .resources import initialize_routes
from . import events

def create_app(config_object=None):
    app = Flask(__name__)

    if config_object:
        app.config.from_object(config_object)
    else:
        app.config.from_object(Config)

    IS_DEV = app.config['DEBUG'] or os.getenv('FLASK_ENV') == 'development'

    client_url = os.getenv('CLIENT_DOMAIN', 'http://localhost:5173')

    # CORS guest list now includes both the client and the API itself (for tools like Swagger)
    origins = [
        "https://social-app-client-civg.onrender.com",
        "https://www.social-app-client-civg.onrender.com",
        "http://127.0.0.1:5173",
        client_url,
    ]
    
    #-----Allows cross-origin resources sharing-----
    CORS(app, supports_credentials=True, origins=origins) #-----Allows CORS for the specified origins----

    #-----Configures JWT for auth-----
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_TOKEN_LOCATION'] = ['cookies'] #-----Specifies that JWTs will be stored in cookies-----
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=7)
    app.config['JWT_COOKIE_CSRF_PROTECT'] = True #-----Enables CSRF protection for cookies. It validatesa cookie against its X-CSRF counterpart-----
    app.config['JWT_CSRF_IN_COOKIES'] = False #-----Tells Flask-JWT-Extended not to set the CSRF token in cookies.-----
    app.config['JWT_COOKIE_HTTPONLY'] = True #-----Prevents client-side JavaScript from accessing JWT cookies.----- 
    
    if IS_DEV:

        # Setting 'None' lets the browser use "localhost", which
        # will work for both http://localhost:5000 and ws://localhost:5000
        app.config['JWT_COOKIE_DOMAIN'] = None 
        app.config['JWT_COOKIE_SECURE'] = False # Allow over HTTP
        app.config['JWT_COOKIE_SAMESITE'] = 'Lax'  #-----Controls whether cookies are sent with cross-site requests-----
    else:
        app.config['JWT_COOKIE_DOMAIN'] = '.onrender.com'
        app.config['JWT_COOKIE_SECURE'] = True # Force HTTPS
        app.config['JWT_COOKIE_SAMESITE'] = 'None'  #-----Controls whether cookies are sent with cross-site requests-----


    #-----Initialize flask extensions-----
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    socketio.init_app(app, message_queue=app.config['MESSAGE_QUEUE'], cors_allowed_origins=origins)

    #-----Create the established routes-----
    initialize_routes(app)

    return app