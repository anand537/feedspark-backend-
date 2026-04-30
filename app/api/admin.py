from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import afg_db
from app.models import User
from app.utils.validation import validate_password
import secrets
import string

admin_api = Blueprint('admin_api', __name__, url_prefix='/admin')

@admin_api.route('/users', methods=['GET'])
@jwt_required()
def get_admin_users():
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)
    if not current_user or current_user.role != 'admin':
        return jsonify({'message': 'Access denied'}), 403

    role_filter = request.args.get('role')
    query = User.query
    if role_filter:
        query = query.filter_by(role=role_filter)

    users = query.all()
    return jsonify([{
        'id': str(u.id),
        'name': u.name,
        'email': u.email,
        'role': u.role,
        'created_at': u.created_at.isoformat() if u.created_at else None
    } for u in users])

@admin_api.route('/users', methods=['POST'])
@jwt_required()
def create_admin_user():
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)
    if not current_user or current_user.role != 'admin':
        return jsonify({'message': 'Access denied'}), 403

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

    if password:
        password_errors = validate_password(password)
        if password_errors:
            return jsonify({'message': 'Password validation failed', 'errors': password_errors}), 400
    else:
        alphabet = string.ascii_letters + string.digits + "@$!%*?&#"
        while True:
            password = ''.join(secrets.choice(alphabet) for i in range(12))
            if not validate_password(password):
                break

    new_user = User(name=name, email=email, role=role)
    new_user.set_password(password)
    afg_db.session.add(new_user)
    afg_db.session.commit()

    return jsonify({
        'id': str(new_user.id),
        'name': new_user.name,
        'email': new_user.email,
        'role': new_user.role
    }), 201
