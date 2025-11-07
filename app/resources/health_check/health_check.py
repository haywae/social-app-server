from flask import current_app
from flask_restful import Resource
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

def check_db_connection():
    """
    Checks the database connection by executing a simple query.
    Raises an exception if the connection fails.
    """
    db = current_app.extensions.get('sqlalchemy')
    db.session.execute(text("SELECT 1"))

#---------------------------------------------
# Health Check Endpoints
#---------------------------------------------
class ReadinessProbe(Resource):
    def get(self):
        try:
            # The probe is ready if it can connect to its dependencies.
            check_db_connection()
            return {'status': 'ready'}, 200
        except SQLAlchemyError as e:
            current_app.logger.error(f"Readiness probe failed (DB connection): {e}")
            return {'status': 'not ready'}, 503

class LivenessProbe(Resource):
    def get(self):
        try:
            # The app is alive if this code can execute.
            check_db_connection()
            return {'status': 'alive'}, 200
        except SQLAlchemyError as e:
            current_app.logger.error(f"Liveness probe failed: {e}")
            return {'status': 'not alive'}, 503