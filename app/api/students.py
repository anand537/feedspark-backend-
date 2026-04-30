from datetime import datetime, timedelta
import json
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from app.extensions import afg_db
from app.models import User, Course, Assignment, Submission, Meeting, MeetingParticipant, MentorInput

students_api = Blueprint('students_api', __name__, url_prefix='/student')

@students_api.route('/dashboard', methods=['GET'])
@jwt_required()
def get_student_dashboard():
    current_user_id = get_jwt_identity()
    user = afg_db.session.get(User, current_user_id)
    if not user or user.role != 'student':
        return jsonify({'message': 'Only students can access this dashboard'}), 403

    enrolled_courses = Course.query.filter(Course.students.any(id=current_user_id)).all()
    courses_data = []
    for course in enrolled_courses:
        assignments = Assignment.query.filter_by(course_id=course.id).all()
        total_assignments = len(assignments)
        completed = Submission.query.filter_by(student_id=current_user_id)
        completed = completed.filter(Submission.assignment_id.in_([a.id for a in assignments])).count() if total_assignments else 0
        progress = round((completed / total_assignments) * 100, 1) if total_assignments else 0
        instructor = afg_db.session.get(User, course.mentor_id) if course.mentor_id else None
        courses_data.append({
            'id': str(course.id),
            'title': course.title,
            'progress': progress,
            'status': course.status,
            'instructor': {
                'id': instructor.id,
                'name': instructor.name,
                'email': instructor.email
            } if instructor else None
        })

    upcoming_meetings = Meeting.query.outerjoin(MeetingParticipant, Meeting.id == MeetingParticipant.meeting_id)\
        .filter(Meeting.scheduled_at >= datetime.utcnow())\
        .filter((Meeting.created_by == current_user_id) | (MeetingParticipant.user_id == current_user_id))\
        .order_by(Meeting.scheduled_at.asc()).limit(3).all()

    meetings_data = []
    for meeting in upcoming_meetings:
        meetings_data.append({
            'id': meeting.id,
            'title': meeting.title,
            'scheduled_at': meeting.scheduled_at.isoformat() if meeting.scheduled_at else None,
            'meeting_link': meeting.meeting_link,
            'status': meeting.status
        })

    recent_feedback_count = MentorInput.query.filter_by(student_id=current_user_id).count()

    total_submissions = Submission.query.filter_by(student_id=current_user_id).count()
    graded_submissions = Submission.query.filter_by(student_id=current_user_id).filter(Submission.score.isnot(None)).count()
    avg_score = afg_db.session.query(func.avg(Submission.score)).filter(Submission.student_id == current_user_id, Submission.score.isnot(None)).scalar()

    return jsonify({
        'student': {
            'id': user.id,
            'name': user.name,
            'email': user.email
        },
        'enrolled_courses': courses_data,
        'upcoming_meetings': meetings_data,
        'recent_feedback_count': recent_feedback_count,
        'submission_summary': {
            'total_submissions': total_submissions,
            'graded_submissions': graded_submissions,
            'average_score': round(avg_score, 1) if avg_score else None
        }
    })

@students_api.route('/awards', methods=['GET'])
@jwt_required()
def get_student_awards():
    current_user_id = get_jwt_identity()
    user = afg_db.session.get(User, current_user_id)
    if not user or user.role != 'student':
        return jsonify({'message': 'Only students can access awards'}), 403

    total_submissions = Submission.query.filter_by(student_id=current_user_id).count()
    completed = Submission.query.filter_by(student_id=current_user_id).filter(Submission.status.in_(['graded', 'completed'])).count()
    avg_score = afg_db.session.query(func.avg(Submission.score)).filter(Submission.student_id == current_user_id, Submission.score.isnot(None)).scalar() or 0
    recent_present = Feedback.query.join(Submission, Feedback.submission_id == Submission.id).filter(Submission.student_id == current_user_id).count()

    awards = []
    if avg_score >= 90:
        awards.append({'name': 'High Achiever', 'description': 'Maintained a top average score.'})
    if completed >= 5:
        awards.append({'name': 'Consistent Completer', 'description': 'Completed five or more assignments.'})
    if total_submissions >= 8:
        awards.append({'name': 'Active Learner', 'description': 'Submitted lots of work on time.'})
    if recent_present >= 3:
        awards.append({'name': 'Feedback First', 'description': 'Regularly requested and reviewed feedback.'})
    if not awards:
        awards.append({'name': 'Getting Started', 'description': 'Keep learning and you will earn more awards.'})

    return jsonify({'awards': awards})
