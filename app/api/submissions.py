from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import afg_db, supabase_client
from app.models import Submission, Assignment, User
from app.utils.email_utils import send_submission_confirmation_email
from app.utils.storage_utils import delete_file_async
from datetime import datetime

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

submissions_api = Blueprint('submissions_api', __name__, url_prefix='/submissions')

def get_signed_url(path_or_url):
    """Generate a signed URL valid for 1 hour if input is a path"""
    if not path_or_url or not supabase_client:
        return path_or_url
        
    # If it starts with http, it's likely a legacy public URL, return as is
    if path_or_url.startswith('http'):
        return path_or_url
        
    try:
        # Create signed URL valid for 3600 seconds (1 hour)
        res = supabase_client.storage.from_('submissions').create_signed_url(path_or_url, 3600)
        return res.get('signedURL') if isinstance(res, dict) else res
    except Exception:
        return None

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
            'id': submission.id,
            'assignment_id': submission.assignment_id,
            'assignment_title': assignment.title if assignment else None,
            'student_id': submission.student_id,
            'student_name': student.name if student else None,
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

@submissions_api.route('/<int:submission_id>', methods=['GET'])
@jwt_required()
def get_submission(submission_id):
    """Get a specific submission"""
    submission = Submission.query.get(submission_id)
    if not submission:
        return jsonify({'message': 'Submission not found'}), 404

    assignment = Assignment.query.get(submission.assignment_id)
    student = User.query.get(submission.student_id)

    return jsonify({
        'id': submission.id,
        'assignment_id': submission.assignment_id,
        'assignment_title': assignment.title if assignment else None,
        'student_id': submission.student_id,
        'student_name': student.name if student else None,
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
    if 'file' in request.files and supabase_client:
        file = request.files['file']
        if file.filename != '':
            # Validate file extension
            if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
                return jsonify({'message': 'Invalid file type. Allowed: pdf, doc, docx, txt'}), 400

            try:
                # Generate unique path: assignments/{assignment_id}/{student_id}_{timestamp}_{filename}
                timestamp = int(datetime.utcnow().timestamp())
                file_path = f"assignments/{data['assignment_id']}/{current_user_id}_{timestamp}_{file.filename}"
                
                # Upload file
                file_content = file.read()
                supabase_client.storage.from_('submissions').upload(
                    file_path, 
                    file_content, 
                    {"content-type": file.content_type}
                )
                # Store file path instead of public URL
                file_url = file_path
            except Exception as e:
                return jsonify({'message': f'File upload failed: {str(e)}'}), 500

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

    return jsonify({
        'id': submission.id,
        'assignment_id': submission.assignment_id,
        'student_id': submission.student_id,
        'submitted_at': submission.submitted_at.isoformat(),
        'file_url': get_signed_url(submission.file_url),
        'status': submission.status
    }), 201

@submissions_api.route('/<int:submission_id>', methods=['PUT'])
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
    if current_user.user_type == 'student':
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
    elif current_user.user_type in ['mentor', 'super-admin']:
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
        'id': submission.id,
        'assignment_id': submission.assignment_id,
        'student_id': submission.student_id,
        'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
        'file_url': get_signed_url(submission.file_url),
        'status': submission.status,
        'score': submission.score,
        'feedback': submission.feedback
    })

@submissions_api.route('/<int:submission_id>', methods=['DELETE'])
@jwt_required()
def delete_submission(submission_id):
    """Delete a submission"""
    submission = Submission.query.get(submission_id)
    if not submission:
        return jsonify({'message': 'Submission not found'}), 404

    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if current_user.user_type == 'student':
        if submission.student_id != current_user_id:
            return jsonify({'message': 'Access denied'}), 403
    elif current_user.user_type not in ['mentor', 'super-admin']:
        return jsonify({'message': 'Access denied'}), 403

    # Capture file URL before deleting the record
    file_url_to_delete = submission.file_url

    afg_db.session.delete(submission)
    afg_db.session.commit()

    # Trigger background deletion job
    if file_url_to_delete:
        delete_file_async(file_url_to_delete)

    return jsonify({'message': 'Submission deleted successfully'})
