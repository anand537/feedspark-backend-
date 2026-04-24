import os

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_cors import CORS # Import get_jwt, jwt_required, etc.
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_redis import FlaskRedis


afg_db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
cors = CORS()
socketio = SocketIO()
# Use memory:// storage for development if REDIS_URL is not set
limiter = Limiter(
    key_func=get_remote_address, 
    storage_uri=os.environ.get("REDIS_URL") or "memory://"
)

# Supabase client removed - using SQLAlchemy with Supabase PostgreSQL directly


redis_client = FlaskRedis()

# New: FlaskRedis client for JWT blocklist
# It will use the JWT_REDIS_URL from config.py
jwt_redis_blocklist = FlaskRedis(config_prefix="JWT_REDIS")

# Callback function to check if a JWT has been revoked
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    token_in_redis = jwt_redis_blocklist.get(jti)
    return token_in_redis is not None