from flask_restful import Api
from flask_jwt_extended.exceptions import JWTExtendedException  
from jwt.exceptions import (
    ExpiredSignatureError,
)

class CustomApi(Api):
    """ Inherits the Api Class from flask_restful and Redefines its default handle_error method """
    def handle_error(self, e):
        #------------ Checks if the returned error belongs to the jwtextended exception class and raises an exception ----------
        if isinstance(e, (
            JWTExtendedException, 
            ExpiredSignatureError,
        )):
            raise e
        #------------ If it's not an instance of jwtextended exception class it will call the default handle_error method -------
        return super().handle_error(e)