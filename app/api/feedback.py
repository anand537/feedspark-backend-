from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import afg_db
from app.models import Feedback, MentorInput, FeedbackTemplate, User, PerformanceData, Rubric, Assignment, Submission, Course, Criterion, FeedbackVersion
from app.ai import generate_feedback as ai_generate_feedback
from app.services.notification_service import NotificationService
from datetime import datetime

feedback_api = Blueprint('feedback_api', __name__, url_prefix='/feedback')

def generate_assignment_feedback(template_text, assignment_description, additional_instructions):
    """Mock AI generation for assignment feedback"""
    return f"AI Generated Feedback based on template. {additional_instructions}"

def create_feedback_version(feedback_id, text, user_id):
    """Helper to save a version of feedback"""
    count = FeedbackVersion.query.filter_by(feedback_id=feedback_id).count()
    version = FeedbackVersion(
        feedback_id=feedback_id,
        feedback_text=text,
        version_number=count + 1,
        created_by=user_id,
        created_at=datetime.utcnow()
    )
    afg_db.session.add(version)

@feedback_api.route('', methods=['POST'])
@jwt_required()
def create_feedback():
    data = request.get_json()
    if not data or 'rubric_id' not in data or 'performance_data' not in data or 'template_id' not in data:
        return jsonify({
            "status": "error",
            "message": "Missing rubric_id, performance_data or template_id"
        }), 400

    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)

    if current_user.user_type not in ['mentor', 'super-admin']:
        return jsonify({'message': 'Only mentors and admins can generate feedback'}), 403

    if 'student_id' not in data:
        return jsonify({'message': 'student_id is required'}), 400

    # Create MentorInput record
    mentor_input = MentorInput(
        student_id=data['student_id'],
        rubric_id=data['rubric_id'],
        evaluator_id=current_user_id,
        submitted_at=datetime.utcnow()
    )
    afg_db.session.add(mentor_input)
    afg_db.session.flush()  # to get mentor_input.id

    # Save performance data
    performance_context = []
    for item in data['performance_data']:
        pd = PerformanceData(
            mentor_input_id=mentor_input.id,
            criterion_id=item['criterion_id'],
            score=item['score'],
            remarks=item.get('remarks')
        )
        afg_db.session.add(pd)
        
        # Fetch criterion details to send to AI (Context is crucial for good feedback)
        criterion = afg_db.session.get(Criterion, item['criterion_id'])
        if criterion:
            performance_context.append({
                "criterion": criterion.name,
                "description": criterion.description,
                "score": item['score'],
                "max_score": criterion.max_score,
                "remarks": item.get('remarks', '')
            })

    # Get template
    template = afg_db.session.get(FeedbackTemplate, data['template_id'])
    if not template:
        return jsonify({
            "status": "error",
            "message": "Feedback template not found"
        }), 404

    # Generate AI feedback using template and performance data
    feedback_text = ai_generate_feedback(template.template_text, performance_context)

    # Save feedback
    feedback = Feedback(
        mentor_input_id=mentor_input.id,
        feedback_text=feedback_text,
        generated_at=datetime.utcnow()
    )
    afg_db.session.add(feedback)
    afg_db.session.commit()
    
    # Save initial version
    create_feedback_version(feedback.id, feedback_text, current_user_id)
    afg_db.session.commit()

    # Send notification email to student
    try:
        student = afg_db.session.get(User, data['student_id'])
        if student:
            NotificationService.create_notification(
                user_id=student.id,
                title="New Feedback Available",
                message=f"Mentor {current_user.name} has provided feedback.",
                notification_type="feedback",
                email_notify=True
            )
    except Exception as e:
        print(f"Failed to send feedback notification email: {str(e)}")
        # Don't fail the feedback generation if email fails

    return jsonify({
        "status": "success",
        "message": "Feedback generated and saved",
        "data": {
            "feedback_text": feedback_text,
            "mentor_input_id": mentor_input.id,
            "feedback_id": feedback.id
        }
    }), 201

@feedback_api.route('/<int:feedback_id>', methods=['PUT'])
@jwt_required()
def update_feedback(feedback_id):
    """Update feedback text (Mentor/Admin only)"""
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)

    if current_user.user_type not in ['mentor', 'super-admin']:
        return jsonify({'message': 'Access denied'}), 403

    feedback = afg_db.session.get(Feedback, feedback_id)
    if not feedback:
        return jsonify({'message': 'Feedback not found'}), 404

    # Verify ownership via MentorInput
    mentor_input = afg_db.session.get(MentorInput, feedback.mentor_input_id)
    if current_user.user_type != 'super-admin' and mentor_input.evaluator_id != current_user_id:
        return jsonify({'message': 'Access denied'}), 403

    data = request.get_json()
    if 'feedback_text' in data:
        feedback.feedback_text = data['feedback_text']
        
        # Save new version
        create_feedback_version(feedback.id, data['feedback_text'], current_user_id)
        afg_db.session.commit()
        return jsonify({'message': 'Feedback updated successfully', 'feedback_text': feedback.feedback_text})
    
    return jsonify({'message': 'No data provided'}), 400

@feedback_api.route('/<int:feedback_id>', methods=['DELETE'])
@jwt_required()
def delete_feedback(feedback_id):
    """Delete feedback and associated evaluation data"""
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)

    if current_user.user_type not in ['mentor', 'super-admin']:
        return jsonify({'message': 'Access denied'}), 403

    feedback = afg_db.session.get(Feedback, feedback_id)
    if not feedback:
        return jsonify({'message': 'Feedback not found'}), 404

    # Delete the parent MentorInput, which cascades to Feedback and PerformanceData
    mentor_input = afg_db.session.get(MentorInput, feedback.mentor_input_id)
    afg_db.session.delete(mentor_input)
    afg_db.session.commit()

    return jsonify({'message': 'Feedback and evaluation deleted successfully'})

@feedback_api.route('/<int:feedback_id>/regenerate', methods=['POST'])
@jwt_required()
def regenerate_feedback(feedback_id):
    """Regenerate feedback with optional new instructions"""
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)

    if current_user.user_type not in ['mentor', 'super-admin']:
        return jsonify({'message': 'Access denied'}), 403

    feedback = afg_db.session.get(Feedback, feedback_id)
    if not feedback:
        return jsonify({'message': 'Feedback not found'}), 404

    mentor_input = afg_db.session.get(MentorInput, feedback.mentor_input_id)
    
    # Check ownership
    if current_user.user_type != 'super-admin' and mentor_input.evaluator_id != current_user_id:
        return jsonify({'message': 'Access denied'}), 403

    data = request.get_json()
    if not data or 'template_id' not in data:
         return jsonify({'message': 'template_id is required for regeneration'}), 400

    template = afg_db.session.get(FeedbackTemplate, data['template_id'])
    if not template:
        return jsonify({'message': 'Template not found'}), 404

    # Reconstruct performance context from database
    performance_data = PerformanceData.query.filter_by(mentor_input_id=mentor_input.id).all()
    performance_context = []
    for pd in performance_data:
        criterion = afg_db.session.get(Criterion, pd.criterion_id)
        if criterion:
            performance_context.append({
                "criterion": criterion.name,
                "description": criterion.description,
                "score": pd.score,
                "max_score": criterion.max_score,
                "remarks": pd.remarks or ''
            })

    feedback_text = ai_generate_feedback(
        template.template_text, 
        performance_context, 
        instructions=data.get('additional_instructions')
    )
    
    feedback.feedback_text = feedback_text
    feedback.generated_at = datetime.utcnow()
    
    # Save new version
    create_feedback_version(feedback.id, feedback_text, current_user_id)
    afg_db.session.commit()
    
    return jsonify({
        "status": "success",
        "message": "Feedback regenerated",
        "data": {
            "feedback_text": feedback_text,
            "feedback_id": feedback.id
        }
    })

@feedback_api.route('/<int:feedback_id>/versions', methods=['GET'])
@jwt_required()
def get_feedback_versions(feedback_id):
    """Get version history for a feedback"""
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)
    
    feedback = afg_db.session.get(Feedback, feedback_id)
    if not feedback:
        return jsonify({'message': 'Feedback not found'}), 404
        
    # Check access
    mentor_input = afg_db.session.get(MentorInput, feedback.mentor_input_id)
    if current_user.user_type == 'student' and mentor_input.student_id != current_user_id:
        return jsonify({'message': 'Access denied'}), 403
    if current_user.user_type == 'mentor' and mentor_input.evaluator_id != current_user_id:
        # Mentors can see versions of feedback they created
        pass
        
    versions = FeedbackVersion.query.filter_by(feedback_id=feedback_id).order_by(FeedbackVersion.version_number.desc()).all()
    
    return jsonify([{
        'id': v.id,
        'version_number': v.version_number,
        'feedback_text': v.feedback_text,
        'created_at': v.created_at.isoformat(),
        'created_by': v.created_by
    } for v in versions])

@feedback_api.route('/<int:feedback_id>/revert/<int:version_id>', methods=['POST'])
@jwt_required()
def revert_feedback_version(feedback_id, version_id):
    """Revert feedback to a specific version"""
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)
    
    if current_user.user_type not in ['mentor', 'super-admin']:
        return jsonify({'message': 'Access denied'}), 403
        
    feedback = afg_db.session.get(Feedback, feedback_id)
    version = afg_db.session.get(FeedbackVersion, version_id)
    
    if not feedback or not version or version.feedback_id != feedback_id:
        return jsonify({'message': 'Feedback or version not found'}), 404
        
    feedback.feedback_text = version.feedback_text
    # Create a new version for the revert action so history is preserved
    create_feedback_version(feedback.id, version.feedback_text, current_user_id)
    afg_db.session.commit()
    
    return jsonify({'message': f'Reverted to version {version.version_number}', 'feedback_text': feedback.feedback_text})

@feedback_api.route('/history', methods=['GET'])
@jwt_required()
def feedback_history():
    current_user_id = get_jwt_identity()
    feedbacks = Feedback.query.join(MentorInput).filter(MentorInput.student_id == current_user_id).all()
    result = []
    for fb in feedbacks:
        mentor_input = afg_db.session.get(MentorInput, fb.mentor_input_id)
        rubric = None
        if mentor_input:
            rubric = afg_db.session.get(Rubric, mentor_input.rubric_id)
        result.append({
            'id': fb.id,
            'feedback_text': fb.feedback_text,
            'generated_at': fb.generated_at.isoformat() if fb.generated_at else None,
            'rubric_title': rubric.title if rubric else None
        })
    return jsonify(result)

@feedback_api.route('/analytics', methods=['GET'])
@jwt_required()
def feedback_analytics():
    # Example analytics: count feedbacks generated per student
    from sqlalchemy import func
    counts = afg_db.session.query(
        MentorInput.student_id,
        func.count(Feedback.id)
    ).join(Feedback, Feedback.mentor_input_id == MentorInput.id).group_by(MentorInput.student_id).all()

    result = [{'student_id': c[0], 'feedback_count': c[1]} for c in counts]
    return jsonify(result)

@feedback_api.route('/generate-assignment-feedback', methods=['POST'])
@jwt_required()
def generate_assignment_feedback_endpoint():
    data = request.get_json()
    if not data or 'template_id' not in data or 'assignment_id' not in data or 'student_ids' not in data:
        return jsonify({
            "status": "error",
            "message": "Missing template_id, assignment_id or student_ids"
        }), 400

    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)

    if current_user.user_type not in ['mentor', 'super-admin']:
        return jsonify({'message': 'Only mentors and admins can generate feedback'}), 403

    # Get template
    template = afg_db.session.get(FeedbackTemplate, data['template_id'])
    if not template:
        return jsonify({
            "status": "error",
            "message": "Feedback template not found"
        }), 404

    # Get assignment details
    assignment = afg_db.session.get(Assignment, data['assignment_id'])
    if not assignment:
        return jsonify({
            "status": "error",
            "message": "Assignment not found"
        }), 404

    # Get course details
    course = afg_db.session.get(Course, assignment.course_id)
    if not course:
        return jsonify({
            "status": "error",
            "message": "Course not found"
        }), 404

    # Get student submissions for this assignment
    submissions = Submission.query.filter(
        Submission.assignment_id == data['assignment_id'],
        Submission.student_id.in_(data['student_ids'])
    ).all()

    generated_feedbacks = []

    for student_id in data['student_ids']:
        # Find submission for this student
        submission = next((s for s in submissions if s.student_id == student_id), None)

        if not submission:
            continue  # Skip if no submission found

        # Get student details
        student = afg_db.session.get(User, student_id)
        if not student:
            continue

        # Prepare assignment description for AI
        assignment_description = f"""
        Assignment: {assignment.title}
        Description: {assignment.description or 'No description provided'}
        Course: {course.title}
        Student: {student.name}
        Submission: {submission.file_url or 'No file submitted'}
        """

        # Generate AI feedback using template and assignment details
        feedback_text = generate_assignment_feedback(
            template.template_text,
            assignment_description,
            data.get('additional_instructions', '')
        )

        # Create MentorInput record
        mentor_input = MentorInput(
            student_id=student_id,
            rubric_id=None,  # No rubric for AI-generated feedback
            evaluator_id=current_user_id,
            submitted_at=datetime.utcnow()
        )
        afg_db.session.add(mentor_input)
        afg_db.session.flush()

        # Save feedback
        feedback = Feedback(
            mentor_input_id=mentor_input.id,
            feedback_text=feedback_text,
            generated_at=datetime.utcnow()
        )
        afg_db.session.add(feedback)
        afg_db.session.flush() # Get ID
        
        create_feedback_version(feedback.id, feedback_text, current_user_id)

        # Update submission with feedback
        if submission:
            submission.feedback = feedback_text
            submission.status = 'graded'  # Update status to graded

        # Trigger Notification for the student
        try:
            NotificationService.create_notification(
                user_id=student_id,
                title="New Feedback Available",
                message=f"Feedback for assignment '{assignment.title}' is now available.",
                notification_type="feedback",
                email_notify=True
            )
        except Exception as e:
            print(f"Failed to send notification to student {student_id}: {str(e)}")

        generated_feedbacks.append({
            'student_id': student_id,
            'student_name': student.name,
            'assignment_id': assignment.id,
            'assignment_title': assignment.title,
            'feedback_text': feedback_text,
            'generated_at': feedback.generated_at.isoformat()
        })

    afg_db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"Feedback generated for {len(generated_feedbacks)} students",
        "data": generated_feedbacks
    }), 201
