from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import afg_db
from app.models import Assignment, Course, Submission, User
from datetime import datetime

assignments_api = Blueprint('assignments_api', __name__, url_prefix='/assignments')

@assignments_api.route('/', methods=['GET'])
@jwt_required()
def get_assignments():
    """Get all assignments"""
    course_id = request.args.get('course_id')
    query = Assignment.query
    if course_id:
        query = query.filter_by(course_id=course_id)

    assignments = query.all()
    result = []
    for assignment in assignments:
        course = Course.query.get(assignment.course_id)
        submission_count = Submission.query.filter_by(assignment_id=assignment.id).count()
        result.append({
            'id': assignment.id,
            'course_id': assignment.course_id,
            'course_title': course.title if course else None,
            'title': assignment.title,
            'description': assignment.description,
            'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
            'status': assignment.status,
            'created_at': assignment.created_at.isoformat() if assignment.created_at else None,
            'submission_count': submission_count
        })
    return jsonify(result)

@assignments_api.route('/<int:assignment_id>', methods=['GET'])
@jwt_required()
def get_assignment(assignment_id):
    """Get a specific assignment"""
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({'message': 'Assignment not found'}), 404

    course = Course.query.get(assignment.course_id)
    submission_count = Submission.query.filter_by(assignment_id=assignment.id).count()

    return jsonify({
        'id': assignment.id,
        'course_id': assignment.course_id,
        'course_title': course.title if course else None,
        'title': assignment.title,
        'description': assignment.description,
        'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
        'status': assignment.status,
        'created_at': assignment.created_at.isoformat() if assignment.created_at else None,
        'submission_count': submission_count
    })

@assignments_api.route('/', methods=['POST'])
@jwt_required()
def create_assignment():
    """Create a new assignment"""
    data = request.get_json()
    if not data or 'title' not in data or 'course_id' not in data:
        return jsonify({'message': 'Title and course_id are required'}), 400

    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if current_user.user_type not in ['super-admin', 'mentor']:
        return jsonify({'message': 'Only mentors and admins can create assignments'}), 403

    # Verify course exists
    course = Course.query.get(data['course_id'])
    if not course:
        return jsonify({'message': 'Course not found'}), 404

    assignment = Assignment(
        course_id=data['course_id'],
        title=data['title'],
        description=data.get('description'),
        due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None,
        status=data.get('status', 'active'),
        created_at=datetime.utcnow()
    )

    afg_db.session.add(assignment)
    afg_db.session.commit()

    return jsonify({
        'id': assignment.id,
        'course_id': assignment.course_id,
        'title': assignment.title,
        'description': assignment.description,
        'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
        'status': assignment.status,
        'created_at': assignment.created_at.isoformat()
    }), 201

@assignments_api.route('/<int:assignment_id>', methods=['PUT'])
@jwt_required()
def update_assignment(assignment_id):
    """Update an assignment"""
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({'message': 'Assignment not found'}), 404

    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if current_user.user_type not in ['super-admin', 'mentor']:
        return jsonify({'message': 'Access denied'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    if 'title' in data:
        assignment.title = data['title']
    if 'description' in data:
        assignment.description = data['description']
    if 'due_date' in data:
        assignment.due_date = datetime.fromisoformat(data['due_date']) if data['due_date'] else None
    if 'status' in data:
        assignment.status = data['status']

    afg_db.session.commit()

    return jsonify({
        'id': assignment.id,
        'course_id': assignment.course_id,
        'title': assignment.title,
        'description': assignment.description,
        'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
        'status': assignment.status,
        'created_at': assignment.created_at.isoformat() if assignment.created_at else None
    })

@assignments_api.route('/<int:assignment_id>', methods=['DELETE'])
@jwt_required()
def delete_assignment(assignment_id):
    """Delete an assignment"""
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({'message': 'Assignment not found'}), 404

    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if current_user.user_type not in ['super-admin', 'mentor']:
        return jsonify({'message': 'Access denied'}), 403

    afg_db.session.delete(assignment)
    afg_db.session.commit()

    return jsonify({'message': 'Assignment deleted successfully'})
