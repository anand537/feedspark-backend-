from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt
from app.models import User

def role_required(roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_type = claims.get("user_type", None)

            if current_user.user_type not in roles:
                return jsonify({'message': 'Access denied'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
