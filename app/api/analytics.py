from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import afg_db
from app.models import User, Course, Assignment, Submission, Feedback, MentorInput, Message, Meeting, MeetingParticipant
from sqlalchemy import func, desc, and_, or_, extract
from datetime import datetime, timedelta
import calendar

analytics_api = Blueprint('analytics_api', __name__, url_prefix='/analytics')

@analytics_api.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard_analytics():
    """Get comprehensive dashboard analytics based on user role"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    base_data = {
        "user_info": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "user_type": user.user_type
        }
    }

    if user.user_type == 'super-admin':
        return jsonify({**base_data, **_get_admin_analytics()})
    elif user.user_type == 'mentor':
        return jsonify({**base_data, **_get_mentor_analytics(current_user_id)})
    elif user.user_type == 'student':
        return jsonify({**base_data, **_get_student_analytics(current_user_id)})
    else:
        return jsonify({"error": "Invalid user type"}), 400

def _get_admin_analytics():
    """Get analytics for admin dashboard"""
    # User statistics
    total_users = User.query.count()
    users_by_type = afg_db.session.query(
        User.user_type,
        func.count(User.id)
    ).group_by(User.user_type).all()

    # Course and assignment statistics
    total_courses = Course.query.count()
    total_assignments = Assignment.query.count()
    active_courses = Course.query.filter_by(status='active').count()

    # Submission and feedback statistics
    total_submissions = Submission.query.count()
    total_feedbacks = Feedback.query.count()

    # Recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()
    recent_submissions = Submission.query.filter(Submission.submitted_at >= thirty_days_ago).count()
    recent_feedbacks = Feedback.query.filter(Feedback.generated_at >= thirty_days_ago).count()

    # Monthly growth data (last 12 months)
    monthly_growth = []
    for i in range(11, -1, -1):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=i*30)
        month_end = month_start.replace(day=calendar.monthrange(month_start.year, month_start.month)[1])

        users_count = User.query.filter(
            and_(User.created_at >= month_start, User.created_at <= month_end)
        ).count()

        monthly_growth.append({
            "month": month_start.strftime("%B %Y"),
            "users": users_count
        })

    # Popular courses
    popular_courses = afg_db.session.query(
        Course.title,
        func.count(Submission.id).label('enrollment_count')
    ).join(Assignment, Course.id == Assignment.course_id)\
     .join(Submission, Assignment.id == Submission.assignment_id)\
     .group_by(Course.id, Course.title)\
     .order_by(desc('enrollment_count'))\
     .limit(5).all()

    # Engagement metrics
    total_students = User.query.filter_by(user_type='student').count()
    total_mentors = User.query.filter_by(user_type='mentor').count()

    # Calculate completion rates
    completed_submissions = Submission.query.filter(
        or_(Submission.status == 'graded', Submission.status == 'completed')
    ).count()

    completion_rate = (completed_submissions / total_submissions * 100) if total_submissions > 0 else 0

    # Feedback response rate
    feedback_response_rate = (total_feedbacks / total_submissions * 100) if total_submissions > 0 else 0

    return {
        "summary": {
            "total_users": total_users,
            "total_courses": total_courses,
            "total_assignments": total_assignments,
            "total_submissions": total_submissions,
            "total_feedbacks": total_feedbacks,
            "active_courses": active_courses
        },
        "user_distribution": {
            "students": next((count for type_, count in users_by_type if type_ == 'student'), 0),
            "mentors": next((count for type_, count in users_by_type if type_ == 'mentor'), 0),
            "admins": next((count for type_, count in users_by_type if type_ == 'super-admin'), 0)
        },
        "recent_activity": {
            "new_users_30d": recent_users,
            "new_submissions_30d": recent_submissions,
            "new_feedbacks_30d": recent_feedbacks
        },
        "monthly_growth": monthly_growth,
        "popular_courses": [{"name": name, "enrollments": count} for name, count in popular_courses],
        "engagement_metrics": {
            "completion_rate": round(completion_rate, 1),
            "feedback_response_rate": round(feedback_response_rate, 1),
            "avg_users_per_course": round(total_users / total_courses, 1) if total_courses > 0 else 0
        }
    }

def _get_mentor_analytics(mentor_id):
    """Get analytics for mentor dashboard"""
    # Courses taught by mentor
    courses_taught = Course.query.filter_by(instructor_id=mentor_id).all()
    course_ids = [course.id for course in courses_taught]

    # Students in mentor's courses
    student_count = afg_db.session.query(func.count(func.distinct(Submission.student_id)))\
        .join(Assignment, Submission.assignment_id == Assignment.id)\
        .filter(Assignment.course_id.in_(course_ids)).scalar()

    # Assignments and submissions
    total_assignments = Assignment.query.filter(Assignment.course_id.in_(course_ids)).count()
    total_submissions = Submission.query.join(Assignment)\
        .filter(Assignment.course_id.in_(course_ids)).count()

    # Feedback statistics
    feedback_count = Feedback.query.join(MentorInput)\
        .filter(MentorInput.evaluator_id == mentor_id).count()

    # Recent activity
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_submissions = Submission.query.join(Assignment)\
        .filter(and_(Assignment.course_id.in_(course_ids),
                    Submission.submitted_at >= thirty_days_ago)).count()

    # Average scores per course
    course_scores = []
    for course in courses_taught:
        avg_score = afg_db.session.query(func.avg(Submission.score))\
            .join(Assignment, Submission.assignment_id == Assignment.id)\
            .filter(Assignment.course_id == course.id)\
            .filter(Submission.score.isnot(None)).scalar()

        course_scores.append({
            "course_name": course.title,
            "avg_score": round(avg_score, 1) if avg_score else None,
            "submissions": Submission.query.join(Assignment)\
                .filter(Assignment.course_id == course.id).count()
        })

    return {
        "courses_taught": len(courses_taught),
        "total_students": student_count,
        "total_assignments": total_assignments,
        "total_submissions": total_submissions,
        "total_feedbacks": feedback_count,
        "recent_submissions_30d": recent_submissions,
        "course_performance": course_scores,
        "feedback_efficiency": {
            "avg_feedbacks_per_student": round(feedback_count / student_count, 1) if student_count > 0 else 0,
            "submission_feedback_ratio": round(feedback_count / total_submissions * 100, 1) if total_submissions > 0 else 0
        }
    }

def _get_student_analytics(student_id):
    """Get analytics for student dashboard"""
    # Enrolled courses (based on submissions)
    enrolled_courses = afg_db.session.query(func.count(func.distinct(Assignment.course_id)))\
        .join(Submission, Assignment.id == Submission.assignment_id)\
        .filter(Submission.student_id == student_id).scalar()

    # Total submissions and assignments
    total_submissions = Submission.query.filter_by(student_id=student_id).count()

    # Completed assignments
    completed_submissions = Submission.query.filter(
        and_(Submission.student_id == student_id,
             Submission.status.in_(['graded', 'completed']))
    ).count()

    # Average score
    avg_score = afg_db.session.query(func.avg(Submission.score))\
        .filter(and_(Submission.student_id == student_id,
                    Submission.score.isnot(None))).scalar()

    # Feedback received
    feedback_count = Feedback.query.join(MentorInput)\
        .filter(MentorInput.student_id == student_id).count()

    # Recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_submissions = Submission.query.filter(
        and_(Submission.student_id == student_id,
             Submission.submitted_at >= thirty_days_ago)
    ).count()

    # Performance by course
    course_performance = afg_db.session.query(
        Course.title,
        func.avg(Submission.score).label('avg_score'),
        func.count(Submission.id).label('submissions')
    ).join(Assignment, Course.id == Assignment.course_id)\
     .join(Submission, Assignment.id == Submission.assignment_id)\
     .filter(Submission.student_id == student_id)\
     .filter(Submission.score.isnot(None))\
     .group_by(Course.id, Course.title).all()

    return {
        "enrolled_courses": enrolled_courses,
        "total_submissions": total_submissions,
        "completed_assignments": completed_submissions,
        "average_score": round(avg_score, 1) if avg_score else None,
        "feedback_received": feedback_count,
        "recent_submissions_30d": recent_submissions,
        "completion_rate": round(completed_submissions / total_submissions * 100, 1) if total_submissions > 0 else 0,
        "course_performance": [
            {
                "course_name": name,
                "avg_score": round(score, 1) if score else None,
                "submissions": submissions
            } for name, score, submissions in course_performance
        ]
    }

@analytics_api.route('/user-activity', methods=['GET'])
@jwt_required()
def user_activity_analytics():
    """Get detailed user activity analytics"""
    # This endpoint provides more granular activity data
    days = int(request.args.get('days', 30))
    start_date = datetime.utcnow() - timedelta(days=days)

    # Daily activity
    daily_activity = []
    for i in range(days):
        day = start_date + timedelta(days=i)
        next_day = day + timedelta(days=1)

        day_users = User.query.filter(
            and_(User.created_at >= day, User.created_at < next_day)
        ).count()

        day_submissions = Submission.query.filter(
            and_(Submission.submitted_at >= day, Submission.submitted_at < next_day)
        ).count()

        day_feedbacks = Feedback.query.filter(
            and_(Feedback.generated_at >= day, Feedback.generated_at < next_day)
        ).count()

        daily_activity.append({
            "date": day.strftime("%Y-%m-%d"),
            "new_users": day_users,
            "submissions": day_submissions,
            "feedbacks": day_feedbacks
        })

    # User engagement by type
    user_engagement = afg_db.session.query(
        User.user_type,
        func.count(func.distinct(User.id)).label('active_users'),
        func.avg(func.extract('epoch', func.now() - User.created_at) / 86400).label('avg_account_age_days')
    ).filter(User.created_at >= start_date).group_by(User.user_type).all()

    return jsonify({
        "period_days": days,
        "daily_activity": daily_activity,
        "user_engagement": [
            {
                "user_type": type_,
                "active_users": active,
                "avg_account_age_days": round(age, 1) if age else 0
            } for type_, active, age in user_engagement
        ]
    })

@analytics_api.route('/feedback-metrics', methods=['GET'])
@jwt_required()
def feedback_metrics():
    """Get detailed feedback analytics and metrics"""
    # Feedback generation trends
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    total_feedbacks = Feedback.query.count()
    recent_feedbacks = Feedback.query.filter(Feedback.generated_at >= thirty_days_ago).count()

    # Average feedback length
    avg_feedback_length = afg_db.session.query(
        func.avg(func.length(Feedback.feedback_text))
    ).scalar()

    # Feedback by template usage
    template_usage = afg_db.session.query(
        FeedbackTemplate.name,
        func.count(Feedback.id).label('usage_count')
    ).join(MentorInput, FeedbackTemplate.id == MentorInput.rubric_id)\
     .join(Feedback, MentorInput.id == Feedback.mentor_input_id)\
     .group_by(FeedbackTemplate.id, FeedbackTemplate.name)\
     .order_by(desc('usage_count')).limit(10).all()

    # Response time analysis (if we had timestamps for when feedback was requested)
    # For now, we'll use generation time as proxy

    return jsonify({
        "total_feedbacks": total_feedbacks,
        "recent_feedbacks_30d": recent_feedbacks,
        "avg_feedback_length": round(avg_feedback_length, 0) if avg_feedback_length else 0,
        "template_usage": [
            {"template_name": name, "usage_count": count}
            for name, count in template_usage
        ],
        "feedback_generation_rate": round(recent_feedbacks / 30, 1)  # per day
    })

@analytics_api.route('/course-analytics', methods=['GET'])
@jwt_required()
def course_analytics():
    """Get course-specific analytics"""
    course_id = request.args.get('course_id')
    if not course_id:
        return jsonify({"error": "course_id parameter required"}), 400

    # Course basic info
    course = Course.query.get(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    # Enrollment and submission stats
    total_assignments = Assignment.query.filter_by(course_id=course_id).count()
    total_submissions = Submission.query.join(Assignment)\
        .filter(Assignment.course_id == course_id).count()

    unique_students = afg_db.session.query(func.count(func.distinct(Submission.student_id)))\
        .join(Assignment, Submission.assignment_id == Assignment.id)\
        .filter(Assignment.course_id == course_id).scalar()

    # Average scores
    avg_course_score = afg_db.session.query(func.avg(Submission.score))\
        .join(Assignment, Submission.assignment_id == Assignment.id)\
        .filter(and_(Assignment.course_id == course_id, Submission.score.isnot(None))).scalar()

    # Assignment performance
    assignment_performance = afg_db.session.query(
        Assignment.title,
        func.avg(Submission.score).label('avg_score'),
        func.count(Submission.id).label('submissions'),
        func.count(func.case((Submission.status == 'graded', 1))).label('graded')
    ).join(Submission, Assignment.id == Submission.assignment_id)\
     .filter(Assignment.course_id == course_id)\
     .group_by(Assignment.id, Assignment.title).all()

    # Completion rate
    completed_submissions = Submission.query.join(Assignment)\
        .filter(and_(Assignment.course_id == course_id,
                    Submission.status.in_(['graded', 'completed']))).count()

    completion_rate = (completed_submissions / total_submissions * 100) if total_submissions > 0 else 0

    return jsonify({
        "course_info": {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "status": course.status
        },
        "statistics": {
            "total_assignments": total_assignments,
            "total_submissions": total_submissions,
            "unique_students": unique_students,
            "average_score": round(avg_course_score, 1) if avg_course_score else None,
            "completion_rate": round(completion_rate, 1)
        },
        "assignment_performance": [
            {
                "assignment_title": title,
                "avg_score": round(score, 1) if score else None,
                "submissions": submissions,
                "graded": graded,
                "grading_rate": round(graded / submissions * 100, 1) if submissions > 0 else 0
            } for title, score, submissions, graded in assignment_performance
        ]
    })
