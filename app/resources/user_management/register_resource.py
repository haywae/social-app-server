from datetime import date
from flask import request, current_app
from flask_restful import Resource
from sqlalchemy.exc import SQLAlchemyError


from app.exceptions import InvalidEmailFormatError, UserAlreadyExistsError
from app.services import register_new_user
from app.extensions import db

class RegisterResource(Resource):
    """
    API Resource for handling new user registration.
    This endpoint receives user data, passes it to the service layer for validation
    and creation, and handles returning appropriate HTTP responses.
    """
    def post(self):
        """
        Processes a POST request to create a new user.

        Expects a JSON payload with the following keys:
        - username (str): The desired username.
        - email (str): The user's email address.
        - password (str): The user's password.
        - date_of_birth (str): The user's date of birth in 'YYYY-MM-DD' format.
        - country (str): The user's country.

        Returns:
            - 201 Created: If the user is created successfully.
            - 400 Bad Request: If the input data is missing, invalid, or if the
              username/email is already taken.
            - 500 Internal Server Error: For unexpected database or server issues.
        """
        
        data: dict = request.get_json()

        if not data:
            return {'message': 'No input data provided'}, 400
        try:
            # Required fields from the client request
            required_fields = ['username', 'email', 'password', 'dateOfBirth', 'country', 'displayName']
            if not all(field in data and data[field] for field in required_fields):
                raise ValueError("Missing required fields for user registration.")
            
            new_user = register_new_user(
                session=db.session,
                username=data.get('username'),
                email=data.get('email'),
                password=data.get('password'),
                date_of_birth=date.fromisoformat(data.get('dateOfBirth')),
                country=data.get('country'),
                display_name=data.get('displayName'),
            )
            db.session.commit()
            
            return {'message': f'User {new_user.username} created successfully, Please check your email to verify your account.'}, 201
        except (UserAlreadyExistsError, InvalidEmailFormatError, ValueError) as e:
            db.session.rollback()
            return {'message': str(e)}, 400
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during registration: {e}")
            return {'message': 'An internal database error occurred.'}, 500
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An unexpected error occurred during registration: {e}")
            return {'message': 'An unexpected error occurred.'}, 500
