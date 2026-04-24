from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt
from app.models import User

def role_required(roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current_user_id = get_jwt_identity()
            current_user = User.query.get(current_user_id)

            if not current_user or current_user.user_type not in roles:
                return jsonify({'message': 'Access denied'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
