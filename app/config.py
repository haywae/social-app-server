import os

#---------Configurations for the flask app---------
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-jwt-secret-key')

    #-----------SQL Alchemy Configurations---------
    SQLALCHEMY_DATABASE_URI = os.getenv('PROJECT_DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- SENDGRID CONFIGURATION OR ANOTHER EMAIL SENDING SERVICE ---
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER') 
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')

    #----------Client Domain----------
    CLIENT_DOMAIN = os.getenv('CLIENT_DOMAIN')

    #---------- S3 Bucket----------
    S3_BUCKET = os.getenv("S3_BUCKET_NAME")
    S3_KEY = os.getenv("AWS_ACCESS_KEY_ID")
    S3_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY")
    S3_REGION = os.getenv("AWS_REGION", "us-east-1")

    # ---------Google OAuth Configurations---------
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')

    MESSAGE_QUEUE = os.getenv('REDIS_URL', 'redis://localhost:6379')