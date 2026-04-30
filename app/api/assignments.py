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
        'id': str(assignment.id),
        'course_id': str(assignment.course_id),
        'mentor_id': str(assignment.course.mentor_id) if assignment.course else None,
        'mentor_name': assignment.course.mentor.name if assignment.course and assignment.course.mentor else None,
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
        query = query.join(Course).filter(Course.mentor_id == mentor_id)
    if course_id:
        query = query.filter_by(course_id=course_id)
    assignments = query.order_by(Assignment.created_at.desc()).all()
    result = [serialize_assignment(a) for a in assignments]
    return jsonify({'assignments': result})

@assignments_api.route('/<uuid:assignment_id>', methods=['GET'])
@jwt_required()
def get_assignment(assignment_id):
    assignment = afg_db.session.get(Assignment, assignment_id)
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
    current_user = afg_db.session.get(User, current_user_id)
    if current_user.role not in ['admin', 'mentor']:
        return jsonify({'message': 'Only mentors and admins can create assignments'}), 403

    course = afg_db.session.get(Course, data['course_id'])
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

@assignments_api.route('/<uuid:assignment_id>', methods=['PUT'])
@jwt_required()
def update_assignment(assignment_id):
    assignment = afg_db.session.get(Assignment, assignment_id)
    if not assignment:
        return jsonify({'message': 'Assignment not found'}), 404

    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)
    if current_user.role not in ['admin', 'mentor']:
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

@assignments_api.route('/<uuid:assignment_id>', methods=['DELETE'])
@jwt_required()
def delete_assignment(assignment_id):
    assignment = afg_db.session.get(Assignment, assignment_id)
    if not assignment:
        return jsonify({'message': 'Assignment not found'}), 404

    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)
    if current_user.role not in ['admin', 'mentor']:
        return jsonify({'message': 'Access denied'}), 403

    afg_db.session.delete(assignment)
    afg_db.session.commit()
    return jsonify({'message': 'Assignment deleted successfully'})

@assignments_api.route('/<uuid:assignment_id>/submissions', methods=['GET'])
@jwt_required()
def get_assignment_submissions(assignment_id):
    assignment = afg_db.session.get(Assignment, assignment_id)
    if not assignment:
        return jsonify({'message': 'Assignment not found'}), 404

    submissions = Submission.query.filter_by(assignment_id=assignment_id).order_by(Submission.submitted_at.desc()).all()
    result = []
    for s in submissions:
        student = afg_db.session.get(User, s.student_id)
        d = {
            'id': str(s.id),
            'student_id': str(s.student_id),
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

@assignments_api.route('/student/<uuid:student_id>', methods=['GET'])
@jwt_required()
def get_student_submissions(student_id):
    submissions = Submission.query.join(Assignment).filter(Submission.student_id == student_id).order_by(Submission.submitted_at.desc()).all()
    result = []
    for s in submissions:
        a = s.assignment
        d = {
            'id': str(s.id),
            'assignment_title': a.title,
            'assignment_type': getattr(a, 'type', 'essay'),
            'max_score': getattr(a, 'max_score', 100),
            'mentor_name': a.course.mentor.name if a.course and a.course.mentor else None,
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

