from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import afg_db
from app.models import Course, User, Assignment, Submission
from datetime import datetime

courses_api = Blueprint('courses_api', __name__, url_prefix='/courses')

@courses_api.route('/', methods=['GET'])
@jwt_required()
def get_courses():
    """Get all courses"""
    courses = Course.query.all()
    result = []
    for course in courses:
        mentor = afg_db.session.get(User, course.mentor_id) if course.mentor_id else None
        result.append({
            'id': str(course.id),
            'title': course.title,
            'description': course.description,
            'mentor': {
                'id': str(mentor.id),
                'name': mentor.name,
                'email': mentor.email
            } if mentor else None,
            'status': course.status,
            'created_at': course.created_at.isoformat() if course.created_at else None
        })
    return jsonify(result)

@courses_api.route('/enrolled', methods=['GET'])
@jwt_required()
def get_enrolled_courses():
    """Get courses the current student is enrolled in"""
    current_user_id = get_jwt_identity()
    
    courses = Course.query.filter(Course.students.any(id=current_user_id)).all()
    
    result = []
    for course in courses:
        mentor = afg_db.session.get(User, course.mentor_id) if course.mentor_id else None
        result.append({
            'id': str(course.id),
            'title': course.title,
            'description': course.description,
            'mentor': {
                'id': str(mentor.id),
                'name': mentor.name,
                'email': mentor.email
            } if mentor else None,
            'status': course.status,
            'created_at': course.created_at.isoformat() if course.created_at else None
        })
    return jsonify(result)

@courses_api.route('/progress', methods=['GET'])
@jwt_required()
def get_course_progress():
    """Get progress for courses"""
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)
    course_id = request.args.get('course_id')

    query = Course.query
    if current_user.role == 'student':
        query = query.filter(Course.students.any(id=current_user_id))
    elif course_id is not None:
        query = query.filter_by(id=course_id)

    courses = query.all()
    progress_data = []
    for course in courses:
        assignments = Assignment.query.filter_by(course_id=course.id).all()
        total_assignments = len(assignments)
        if current_user.role == 'student':
            completed = Submission.query.filter_by(student_id=current_user_id).filter(Submission.assignment_id.in_([a.id for a in assignments])).count() if total_assignments else 0
            progress = round((completed / total_assignments) * 100, 1) if total_assignments else 0
        else:
            enrolled_students_count = len(course.students)
            expected_submissions = total_assignments * enrolled_students_count
            actual_submissions = Submission.query.join(Assignment, Submission.assignment_id == Assignment.id).filter(Assignment.course_id == course.id).count()
            progress = round((actual_submissions / expected_submissions) * 100, 1) if expected_submissions else 0

        mentor = afg_db.session.get(User, course.mentor_id) if course.mentor_id else None
        progress_data.append({
            'course_id': str(course.id),
            'course_title': course.title,
            'progress': progress,
            'status': course.status,
            'mentor': {
                'id': str(mentor.id),
                'name': mentor.name
            } if mentor else None
        })

    return jsonify({'progress': progress_data})

@courses_api.route('/<uuid:course_id>', methods=['GET'])
@jwt_required()
def get_course(course_id):
    """Get a specific course"""
    course = afg_db.session.get(Course, course_id)
    if not course:
        return jsonify({'message': 'Course not found'}), 404

    mentor = afg_db.session.get(User, course.mentor_id) if course.mentor_id else None
    return jsonify({
        'id': str(course.id),
        'title': course.title,
        'description': course.description,
        'mentor': {
            'id': str(mentor.id),
            'name': mentor.name,
            'email': mentor.email
        } if mentor else None,
        'status': course.status,
        'created_at': course.created_at.isoformat() if course.created_at else None
    })

@courses_api.route('/', methods=['POST'])
@jwt_required()
def create_course():
    """Create a new course"""
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'message': 'Title is required'}), 400

    # Get current user as mentor
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)

    if current_user.role not in ['admin', 'mentor']:
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
        'created_at': course.created_at.isoformat()
    }), 201

@courses_api.route('/<uuid:course_id>', methods=['PUT'])
@jwt_required()
def update_course(course_id):
    """Update a course"""
    course = afg_db.session.get(Course, course_id)
    if not course:
        return jsonify({'message': 'Course not found'}), 404
    
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)
    if current_user.role not in ['admin', 'mentor']:
        return jsonify({'message': 'Access denied'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    if 'title' in data:
        course.title = data['title']
    if 'description' in data:
        course.description = data['description']
    if 'status' in data:
        course.status = data['status']

    afg_db.session.commit()

    return jsonify({
        'id': str(course.id),
        'title': course.title,
        'description': course.description,
        'mentor_id': str(course.mentor_id),
        'status': course.status,
        'created_at': course.created_at.isoformat() if course.created_at else None
    })

@courses_api.route('/<uuid:course_id>', methods=['DELETE'])
@jwt_required()
def delete_course(course_id):
    """Delete a course"""
    course = afg_db.session.get(Course, course_id)
    if not course:
        return jsonify({'message': 'Course not found'}), 404
    
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)
    if current_user.role not in ['admin', 'mentor']:
        return jsonify({'message': 'Access denied'}), 403

    afg_db.session.delete(course)
    afg_db.session.commit()

    return jsonify({'message': 'Course deleted successfully'})

@courses_api.route('/<uuid:course_id>/enroll', methods=['POST'])
@jwt_required()
def enroll_in_course(course_id):
    """Enroll a student in a course"""
    course = afg_db.session.get(Course, course_id)
    if not course:
        return jsonify({'message': 'Course not found'}), 404

    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)

    if current_user.role != 'student':
        return jsonify({'message': 'Only students can enroll in courses'}), 403

    if current_user in course.students:
        return jsonify({'message': 'Already enrolled'}), 409

    course.students.append(current_user)
    afg_db.session.commit()

    return jsonify({'message': 'Enrolled successfully'}), 201
