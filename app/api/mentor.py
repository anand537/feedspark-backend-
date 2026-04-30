from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import afg_db
from app.models import User, Course

mentor_api = Blueprint('mentor_api', __name__, url_prefix='/mentor')

@mentor_api.route('/students', methods=['GET'])
@jwt_required()
def get_mentor_students():
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)
    if not current_user or current_user.role != 'mentor':
        return jsonify({'message': 'Only mentors can access this endpoint'}), 403

    courses = Course.query.filter_by(mentor_id=current_user_id).all()
    student_ids = set()
    students = []
    for course in courses:
        for student in getattr(course, 'students', []):
            if student.id not in student_ids:
                student_ids.add(student.id)
                students.append({
                    'id': str(student.id),
                    'name': student.name,
                    'email': student.email,
                    'role': student.role
                })

    return jsonify({'students': students})

@mentor_api.route('/courses', methods=['POST'])
@jwt_required()
def create_mentor_course():
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'message': 'Title is required'}), 400

    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)
    if not current_user or current_user.role not in ['mentor', 'admin']:
        return jsonify({'message': 'Only mentors and admins can create courses'}), 403

    course = Course(
        title=data['title'],
        description=data.get('description'),
        mentor_id=current_user_id,
        status=data.get('status', 'active'),
        created_at=datetime.utcnow()
    )

    afg_db.session.add(course)
    afg_db.session.commit()

    return jsonify({
        'id': str(course.id),
        'title': course.title,
        'description': course.description,
        'mentor_id': str(course.mentor_id),
        'status': course.status,
        'created_at': course.created_at.isoformat() if course.created_at else None
    }), 201
