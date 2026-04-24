from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import afg_db
from app.models import Assignment, Course, Submission, User, Rubric
import json
from datetime import datetime

assignments_api = Blueprint('assignments_api', __name__, url_prefix='/assignments')

def serialize_assignment(assignment):
    """Serialize assignment with JSON fields parsed."""
    d = {
        'id': assignment.id,
        'course_id': assignment.course_id,
        'mentor_id': assignment.course.instructor_id if assignment.course else None,
        'mentor_name': assignment.course.instructor.name if assignment.course and assignment.course.instructor else None,
        'title': assignment.title,
        'description': assignment.description,
        'type': getattr(assignment, 'type', 'essay'),
        'rubric': json.loads(assignment.rubric_json or '{}'),
        'questions': json.loads(assignment.questions or '[]'),
        'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
        'max_score': getattr(assignment, 'max_score', 100),
        'status': assignment.status,
        'created_at': assignment.created_at.isoformat() if assignment.created_at else None,
        'submission_count': Submission.query.filter_by(assignment_id=assignment.id).count()
    }
    if assignment.course:
        d['course_title'] = assignment.course.title
    return d

@assignments_api.route('/', methods=['GET'])
@jwt_required()
def get_assignments():
    mentor_id = request.args.get('mentor_id')
    course_id = request.args.get('course_id')
    query = Assignment.query
    if mentor_id:
        query = query.join(Course).filter(Course.instructor_id == mentor_id)
    if course_id:
        query = query.filter_by(course_id=course_id)
    assignments = query.order_by(Assignment.created_at.desc()).all()
    result = [serialize_assignment(a) for a in assignments]
    return jsonify({'assignments': result})

@assignments_api.route('/<int:assignment_id>', methods=['GET'])
@jwt_required()
def get_assignment(assignment_id):
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({'message': 'Assignment not found'}), 404
    return jsonify(serialize_assignment(assignment))

@assignments_api.route('/', methods=['POST'])
@jwt_required()
def create_assignment():
    data = request.get_json()
    required = ['title', 'course_id']
    for f in required:
        if not data.get(f):
            return jsonify({'error': f"'{f}' is required"}), 400

    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if current_user.user_type not in ['super-admin', 'mentor']:
        return jsonify({'message': 'Only mentors and admins can create assignments'}), 403

    course = Course.query.get(data['course_id'])
    if not course:
        return jsonify({'message': 'Course not found'}), 404

    assignment = Assignment(
        course_id=data['course_id'],
        title=data['title'],
        description=data.get('description', ''),
        type=data.get('type', 'essay'),
        rubric_json=json.dumps(data.get('rubric', {})),
        questions=json.dumps(data.get('questions', [])),
        due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None,
        max_score=data.get('max_score', 100),
        status=data.get('status', 'active'),
        created_at=datetime.utcnow()
    )

    afg_db.session.add(assignment)
    afg_db.session.commit()
    return jsonify(serialize_assignment(assignment)), 201

@assignments_api.route('/<int:assignment_id>', methods=['PUT'])
@jwt_required()
def update_assignment(assignment_id):
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({'message': 'Assignment not found'}), 404

    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if current_user.user_type not in ['super-admin', 'mentor']:
        return jsonify({'message': 'Access denied'}), 403

    data = request.get_json()
    if 'title' in data:
        assignment.title = data['title']
    if 'description' in data:
        assignment.description = data['description']
    if 'type' in data:
        assignment.type = data['type']
    if 'rubric' in data:
        assignment.rubric_json = json.dumps(data['rubric'])
    if 'questions' in data:
        assignment.questions = json.dumps(data['questions'])
    if 'due_date' in data:
        assignment.due_date = datetime.fromisoformat(data['due_date']) if data['due_date'] else None
    if 'max_score' in data:
        assignment.max_score = data['max_score']
    if 'status' in data:
        assignment.status = data['status']

    afg_db.session.commit()
    return jsonify(serialize_assignment(assignment))

@assignments_api.route('/<int:assignment_id>', methods=['DELETE'])
@jwt_required()
def delete_assignment(assignment_id):
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

@assignments_api.route('/<int:assignment_id>/submissions', methods=['GET'])
@jwt_required()
def get_assignment_submissions(assignment_id):
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({'message': 'Assignment not found'}), 404

    submissions = Submission.query.filter_by(assignment_id=assignment_id).order_by(Submission.submitted_at.desc()).all()
    result = []
    for s in submissions:
        student = User.query.get(s.student_id)
        d = {
            'id': s.id,
            'student_id': s.student_id,
            'student_name': student.name if student else None,
            'answers': json.loads(s.answers or '{}'),
            'ai_feedback': json.loads(s.ai_feedback or '{}') if s.ai_feedback else None,
            'score': s.score,
            'feedback': s.feedback,
            'file_url': s.file_url,
            'status': s.status,
            'submitted_at': s.submitted_at.isoformat() if s.submitted_at else None
        }
        result.append(d)
    return jsonify({'submissions': result})

@assignments_api.route('/student/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student_submissions(student_id):
    submissions = Submission.query.join(Assignment).filter(Submission.student_id == student_id).order_by(Submission.submitted_at.desc()).all()
    result = []
    for s in submissions:
        a = s.assignment
        d = {
            'id': s.id,
            'assignment_title': a.title,
            'assignment_type': getattr(a, 'type', 'essay'),
            'max_score': getattr(a, 'max_score', 100),
            'mentor_name': a.course.instructor.name if a.course and a.course.instructor else None,
            'answers': json.loads(s.answers or '{}'),
            'ai_feedback': json.loads(s.ai_feedback or '{}') if s.ai_feedback else None,
            'rubric': json.loads(a.rubric_json or '{}'),
            'score': s.score,
            'feedback': s.feedback,
            'file_url': s.file_url,
            'status': s.status,
            'submitted_at': s.submitted_at.isoformat() if s.submitted_at else None
        }
        result.append(d)
    return jsonify({'submissions': result})

