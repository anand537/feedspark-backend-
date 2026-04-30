from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import afg_db  # supabase_client removed
from app.models import Submission, Assignment, User
from flask import current_app
from app.utils.email_utils import send_submission_confirmation_email
from app.utils.storage_utils import delete_file_async
from app.services.assignment_ai import generate_ai_feedback
import json
from datetime import datetime

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

submissions_api = Blueprint('submissions_api', __name__, url_prefix='/submissions')

def get_signed_url(path_or_url):
    """Return path_or_url as is (signed URLs handled client-side or via API)"""
    return path_or_url

@submissions_api.route('/', methods=['GET'])
@jwt_required()
def get_submissions():
    """Get all submissions"""
    assignment_id = request.args.get('assignment_id')
    student_id = request.args.get('student_id')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = Submission.query
    if assignment_id:
        query = query.filter_by(assignment_id=assignment_id)
    if student_id:
        query = query.filter_by(student_id=student_id)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    submissions = pagination.items
    result = []
    for submission in submissions:
        assignment = Assignment.query.get(submission.assignment_id)
        student = User.query.get(submission.student_id)
        result.append({
            'id': str(submission.id),
            'assignment_id': str(submission.assignment_id),
            'assignment_title': assignment.title if assignment else None,
            'student_id': str(submission.student_id),
            'student_name': student.name if student else None,
            'answers': json.loads(submission.answers or '{}') if submission.answers else None,
            'ai_feedback': json.loads(submission.ai_feedback or '{}') if submission.ai_feedback else None,
            'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
            'file_url': get_signed_url(submission.file_url),
            'status': submission.status,
            'score': submission.score,
            'feedback': submission.feedback
        })

    return jsonify({
        'data': result,
        'meta': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })

@submissions_api.route('/<uuid:submission_id>', methods=['GET'])
@jwt_required()
def get_submission(submission_id):
    """Get a specific submission"""
    submission = Submission.query.get(submission_id)
    if not submission:
        return jsonify({'message': 'Submission not found'}), 404

    assignment = Assignment.query.get(submission.assignment_id)
    student = User.query.get(submission.student_id)

    return jsonify({
        'id': str(submission.id),
        'assignment_id': str(submission.assignment_id),
        'assignment_title': assignment.title if assignment else None,
        'student_id': str(submission.student_id),
        'student_name': student.name if student else None,
        'answers': json.loads(submission.answers or '{}') if submission.answers else None,
        'ai_feedback': json.loads(submission.ai_feedback or '{}') if submission.ai_feedback else None,
        'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
        'file_url': get_signed_url(submission.file_url),
        'status': submission.status,
        'score': submission.score,
        'feedback': submission.feedback
    })

@submissions_api.route('/', methods=['POST'])
@jwt_required()
def create_submission():
    """Create a new submission"""
    # Support both JSON (for testing/manual URL) and Multipart Form (for uploads)
    data = request.get_json(silent=True) or request.form
    if not data or 'assignment_id' not in data:
        return jsonify({'message': 'assignment_id is required'}), 400

    # Verify assignment exists
    assignment = Assignment.query.get(data['assignment_id'])
    if not assignment:
        return jsonify({'message': 'Assignment not found'}), 404

    # Get current user as student
    current_user_id = get_jwt_identity()

    # Check if student already submitted
    existing = Submission.query.filter_by(assignment_id=data['assignment_id'], student_id=current_user_id).first()
    if existing:
        return jsonify({'message': 'You have already submitted for this assignment'}), 409

    file_url = data.get('file_url')

    # Handle File Upload via Supabase Storage
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            # Validate file extension
            if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
                return jsonify({'message': 'Invalid file type. Allowed: pdf, doc, docx, txt'}), 400

            # Store file locally or handle differently post-migration
            # For now, use filename as placeholder
            file_url = f"uploads/{file.filename}"
            current_app.logger.info(f"File received: {file.filename} (upload to be implemented)")

    submission = Submission(
        assignment_id=data['assignment_id'],
        student_id=current_user_id,
        file_url=file_url,
        status='submitted',
        submitted_at=datetime.utcnow()
    )

    afg_db.session.add(submission)
    afg_db.session.commit()

    # Send confirmation email to student
    try:
        student = User.query.get(current_user_id)
        if student:
            send_submission_confirmation_email(
                student.email,
                student.name,
                assignment.title
            )
    except Exception as e:
        print(f"Failed to send submission confirmation email: {str(e)}")
        # Don't fail the submission if email fails

    # Auto-generate AI feedback if answers provided (quiz/essay)
    if 'answers' in data:
        try:
            student_answers = json.loads(data['answers'])
            ai_result = generate_ai_feedback(assignment, student_answers, file_url)
            submission.answers = data['answers']
            submission.ai_feedback = json.dumps(ai_result)
            submission.score = ai_result.get('score', 0)
            submission.status = 'ai_graded'
            afg_db.session.commit()
            current_app.logger.info(f"AI feedback generated for submission {submission.id}")
        except Exception as e:
            current_app.logger.error(f"AI feedback generation failed for submission {submission.id}: {e}")

    return jsonify({
        'id': str(submission.id),
        'assignment_id': str(submission.assignment_id),
        'student_id': str(submission.student_id),
        'submitted_at': submission.submitted_at.isoformat(),
        'file_url': get_signed_url(submission.file_url),
        'status': submission.status,
        'ai_feedback': json.loads(submission.ai_feedback or '{}') if submission.ai_feedback else None
    }), 201

@submissions_api.route('/upload', methods=['POST'])
@jwt_required()
def upload_submission():
    return create_submission()

@submissions_api.route('/<uuid:submission_id>', methods=['PUT'])
@jwt_required()
def update_submission(submission_id):
    """Update a submission (grading for mentors, resubmission for students)"""
    submission = Submission.query.get(submission_id)
    if not submission:
        return jsonify({'message': 'Submission not found'}), 404

    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # Support both JSON and Multipart Form
    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    # Logic for Student
    if current_user.role == 'student':
        if submission.student_id != current_user_id:
            return jsonify({'message': 'Access denied'}), 403
        
        if submission.status in ['graded', 'completed']:
            return jsonify({'message': 'Cannot modify submission after it has been graded'}), 403
        
        # Handle File Upload on Update
        if 'file' in request.files and supabase_client:
            file = request.files['file']
            if file.filename != '':
                # Validate file extension
                if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
                    return jsonify({'message': 'Invalid file type. Allowed: pdf, doc, docx, txt'}), 400

                try:
                    timestamp = int(datetime.utcnow().timestamp())
                    file_path = f"assignments/{submission.assignment_id}/{current_user_id}_{timestamp}_{file.filename}"
                    
                    file_content = file.read()
                    supabase_client.storage.from_('submissions').upload(
                        file_path, 
                        file_content, 
                        {"content-type": file.content_type}
                    )
                    submission.file_url = file_path
                    submission.submitted_at = datetime.utcnow()
                except Exception as e:
                    return jsonify({'message': f'File upload failed: {str(e)}'}), 500
        
        elif 'file_url' in data:
            submission.file_url = data['file_url']
            submission.submitted_at = datetime.utcnow()
            
    # Logic for Mentor/Admin
    elif current_user.role in ['mentor', 'admin']:
        if 'score' in data:
            submission.score = data['score']
        if 'feedback' in data:
            submission.feedback = data['feedback']
        if 'status' in data:
            submission.status = data['status']
    else:
        return jsonify({'message': 'Access denied'}), 403

    afg_db.session.commit()

    return jsonify({
        'id': str(submission.id),
        'assignment_id': str(submission.assignment_id),
        'student_id': str(submission.student_id),
        'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
        'file_url': get_signed_url(submission.file_url),
        'status': submission.status,
        'score': submission.score,
        'feedback': submission.feedback
    })

@submissions_api.route('/<uuid:submission_id>', methods=['DELETE'])
@jwt_required()
def delete_submission(submission_id):
    """Delete a submission"""
    submission = Submission.query.get(submission_id)
    if not submission:
        return jsonify({'message': 'Submission not found'}), 404

    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if current_user.role == 'student':
        if submission.student_id != current_user_id:
            return jsonify({'message': 'Access denied'}), 403
    elif current_user.role not in ['mentor', 'admin']:
        return jsonify({'message': 'Access denied'}), 403

    # Capture file URL before deleting the record
    file_url_to_delete = submission.file_url

    afg_db.session.delete(submission)
    afg_db.session.commit()

    # Trigger background deletion job
    if file_url_to_delete:
        delete_file_async(file_url_to_delete)

    return jsonify({'message': 'Submission deleted successfully'})
