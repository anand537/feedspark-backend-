from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.decorators import role_required
from app.utils.email_utils import send_welcome_email
from app.extensions import afg_db
from app.models import User
from app.utils.validation import validate_password
import secrets
import string
import json

users_api = Blueprint('users_api', __name__, url_prefix='/users')

@users_api.route('/', methods=['GET'])
@jwt_required()
def get_users():
    """Get users based on role permissions"""
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)
    
    if not current_user:
        return jsonify({'message': 'User not found'}), 404

    query = User.query
    
    if current_user.role == 'admin':
        role_filter = request.args.get('role')
        if role_filter:
            query = query.filter_by(role=role_filter)
    elif current_user.role == 'mentor':
        # Mentors can see students (for chat/feedback)
        query = query.filter_by(role='student')
    elif current_user.role == 'student':
        # Students can see mentors (for chat)
        query = query.filter_by(role='mentor')
    else:
        return jsonify({'message': 'Access denied'}), 403

    users = query.all()
    return jsonify([{
        'id': str(u.id),
        'name': u.name,
        'email': u.email,
        'role': u.role,
        'created_at': u.created_at.isoformat() if u.created_at else None
    } for u in users])

@users_api.route('/<uuid:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Get a specific user"""
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)
    
    user = afg_db.session.get(User, user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Access Control
    allowed = current_user.role == 'admin' or \
              current_user.id == user.id or \
              (current_user.role == 'mentor' and user.role == 'student') or \
              (current_user.role == 'student' and user.role == 'mentor')
    
    if not allowed:
        return jsonify({'message': 'Access denied'}), 403

    return jsonify({
        'id': str(user.id),
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'created_at': user.created_at.isoformat() if user.created_at else None
    })

@users_api.route('/role/<role>', methods=['GET'])
@jwt_required()
@role_required(['admin', 'mentor'])
def get_users_by_role(role):
    """Get users by role"""
    users = User.query.filter_by(role=role).all()
    return jsonify([{
        'id': str(u.id),
        'name': u.name,
        'email': u.email,
        'role': u.role,
        'created_at': u.created_at.isoformat() if u.created_at else None
    } for u in users])

@users_api.route('/', methods=['POST'])
@jwt_required()
@role_required(['admin'])
def create_user():
    """Create a new user (super admin only)"""
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    name = data.get('name')
    email = data.get('email')
    role = data.get('role')
    password = data.get('password', None)

    if not name or not email or not role:
        return jsonify({'message': 'Missing required fields: name, email, role'}), 400

    if role not in ['student', 'mentor', 'admin']:
        return jsonify({'message': 'Invalid role'}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'message': 'User already exists'}), 409

    # Validate password if provided
    if password:
        password_errors = validate_password(password)
        if password_errors:
            return jsonify({"message": "Password validation failed", "errors": password_errors}), 400
    else:
        # Generate a random password that meets complexity requirements
        while True:
            alphabet = string.ascii_letters + string.digits + "@$!%*?&#"
            password = ''.join(secrets.choice(alphabet) for i in range(12))
            if not validate_password(password):
                break

    new_user = User(
        name=name,
        email=email,
        role=role,
        created_at=datetime.utcnow()
    )
    new_user.set_password(password)

    afg_db.session.add(new_user)
    afg_db.session.commit()

    # Send welcome email with credentials
    try:
        send_welcome_email(new_user.email, new_user.name, password=password)
    except Exception as e:
        print(f"Failed to send welcome email: {str(e)}")

    return jsonify({
        'id': str(new_user.id),
        'name': new_user.name,
        'email': new_user.email,
        'role': new_user.role,
        'created_at': new_user.created_at.isoformat() if new_user.created_at else None
    }), 201

@users_api.route('/<uuid:user_id>', methods=['PUT'])
@jwt_required()
@role_required(['admin'])
def update_user(user_id):
    """Update user (super admin only)"""
    user = afg_db.session.get(User, user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    # Update name if provided
    if 'name' in data and data['name']:
        user.name = data['name']

    # Update email if provided and not already taken
    if 'email' in data and data['email']:
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.id != user_id:
            return jsonify({'message': 'Email already exists'}), 409
        user.email = data['email']

    # Update role if provided
    if 'role' in data:
        if data['role'] not in ['student', 'mentor', 'admin']:
            return jsonify({'message': 'Invalid role'}), 400
        user.role = data['role']
    
    # Optionally update password
    if 'password' in data and data['password']:
        password = data['password']
        password_errors = validate_password(password)
        if password_errors:
            return jsonify({"message": "Password validation failed", "errors": password_errors}), 400
        user.set_password(password)

    afg_db.session.commit()

    return jsonify({
        'id': str(user.id),
        'name': user.name,
        'email': user.email,
        'role': user.role
    })

@users_api.route('/<uuid:user_id>', methods=['DELETE'])
@jwt_required()
@role_required(['admin'])
def delete_user(user_id):
    """Delete user (super admin only)"""
    user = afg_db.session.get(User, user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    afg_db.session.delete(user)
    afg_db.session.commit()

    return jsonify({'message': 'User deleted successfully'})

@users_api.route('/notification-preferences', methods=['PUT'])
@jwt_required()
def update_notification_preferences():
    current_user_id = get_jwt_identity()
    user = afg_db.session.get(User, current_user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    preferences = request.get_json(silent=True)
    if preferences is None:
        return jsonify({'message': 'Invalid JSON payload'}), 400

    try:
        user.notification_preferences = json.dumps(preferences)
    except Exception:
        return jsonify({'message': 'Failed to serialize preferences'}), 400

    afg_db.session.commit()
    return jsonify({'message': 'Notification preferences updated successfully'})

@users_api.route('/notification-preferences', methods=['GET'])
@jwt_required()
def get_notification_preferences():
    current_user_id = get_jwt_identity()
    user = afg_db.session.get(User, current_user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    try:
        preferences = json.loads(user.notification_preferences or '{}')
    except Exception:
        preferences = {}

    return jsonify({'notification_preferences': preferences})
