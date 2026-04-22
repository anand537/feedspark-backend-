from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import afg_db
from app.models import Announcement, User, Course
from app.services.notification_service import NotificationService
from datetime import datetime
from sqlalchemy import or_, and_

announcements_api = Blueprint('announcements_api', __name__, url_prefix='/announcements')

def send_announcement_notifications(announcement):
    """Helper function to distribute notifications for an announcement"""
    recipients = []
    
    if announcement.target_type == 'all':
        recipients = User.query.all()
    elif announcement.target_type == 'role':
        recipients = User.query.filter_by(user_type=announcement.target_value).all()
    elif announcement.target_type == 'course' and announcement.target_value:
        course = afg_db.session.get(Course, int(announcement.target_value))
        if course:
            # Assuming Course has a 'students' relationship
            recipients = course.students

    for recipient in recipients:
        if recipient.id != announcement.created_by: # Don't notify self
            NotificationService.create_notification(
                user_id=recipient.id,
                title=f"New Announcement: {announcement.title}",
                message=announcement.content[:100] + "..." if len(announcement.content) > 100 else announcement.content,
                notification_type='system',
                email_notify=False 
            )

@announcements_api.route('/', methods=['POST'])
@jwt_required()
def create_announcement():
    """Create a new announcement (Mentors & Admins only)"""
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)

    if current_user.user_type not in ['mentor', 'super-admin']:
        return jsonify({'message': 'Access denied'}), 403

    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({'message': 'Title and content are required'}), 400

    target_type = data.get('target_type', 'all')
    target_value = data.get('target_value')
    
    # Handle scheduling
    scheduled_for = datetime.utcnow()
    if data.get('scheduled_for'):
        # Expecting ISO format string
        scheduled_for = datetime.fromisoformat(data.get('scheduled_for').replace('Z', '+00:00'))

    announcement = Announcement(
        title=data['title'],
        content=data['content'],
        created_by=current_user_id,
        target_type=target_type,
        target_value=str(target_value) if target_value else None,
        created_at=datetime.utcnow(),
        scheduled_for=scheduled_for,
        notification_sent=False
    )

    afg_db.session.add(announcement)

    # If scheduled for now or past, send immediately
    if scheduled_for <= datetime.utcnow():
        send_announcement_notifications(announcement)
        announcement.notification_sent = True
        
    afg_db.session.commit()

    return jsonify({
        'id': announcement.id,
        'message': 'Announcement created' + (' and sent' if announcement.notification_sent else ' and scheduled')
    }), 201

@announcements_api.route('/', methods=['GET'])
@jwt_required()
def get_announcements():
    """Get announcements relevant to the current user"""
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)

    query = Announcement.query

    # admins see everything
    if current_user.user_type == 'super-admin':
        announcements = query.order_by(Announcement.scheduled_for.desc()).all()
    else:
        # Filter based on relevance
        filters = [
            Announcement.target_type == 'all',
            and_(Announcement.target_type == 'role', Announcement.target_value == current_user.user_type)
        ]

        # Add course-specific announcements
        if current_user.user_type == 'student':
            # Get IDs of courses the student is enrolled in
            enrolled_courses = Course.query.filter(Course.students.any(id=current_user.id)).all()
            course_ids = [str(c.id) for c in enrolled_courses]
            if course_ids:
                filters.append(and_(Announcement.target_type == 'course', Announcement.target_value.in_(course_ids)))
        
        elif current_user.user_type == 'mentor':
            # Get IDs of courses the mentor teaches
            taught_courses = Course.query.filter_by(instructor_id=current_user.id).all()
            course_ids = [str(c.id) for c in taught_courses]
            if course_ids:
                filters.append(and_(Announcement.target_type == 'course', Announcement.target_value.in_(course_ids)))

        # Only show announcements that are scheduled for now or in the past
        time_filter = Announcement.scheduled_for <= datetime.utcnow()
        
        announcements = query.filter(and_(or_(*filters), time_filter))\
            .order_by(Announcement.scheduled_for.desc()).all()

    result = []
    for a in announcements:
        creator = afg_db.session.get(User, a.created_by) if a.created_by else None
        result.append({
            'id': a.id,
            'title': a.title,
            'content': a.content,
            'target_type': a.target_type,
            'target_value': a.target_value,
            'created_by': {
                'id': creator.id,
                'name': creator.name
            } if creator else None,
            'created_at': a.created_at.isoformat(),
            'scheduled_for': a.scheduled_for.isoformat() if a.scheduled_for else None,
            'is_published': a.scheduled_for <= datetime.utcnow() if a.scheduled_for else True
        })

    return jsonify(result)

@announcements_api.route('/<int:announcement_id>', methods=['PUT'])
@jwt_required()
def update_announcement(announcement_id):
    """Update an announcement (Mentors & Admins only)"""
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)

    if current_user.user_type not in ['mentor', 'super-admin']:
        return jsonify({'message': 'Access denied'}), 403

    announcement = afg_db.session.get(Announcement, announcement_id)
    if not announcement:
        return jsonify({'message': 'Announcement not found'}), 404

    # Check ownership (unless admin)
    if current_user.user_type != 'super-admin' and announcement.created_by != current_user_id:
        return jsonify({'message': 'Access denied'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    # Allow updating content
    if 'title' in data:
        announcement.title = data['title']
    if 'content' in data:
        announcement.content = data['content']
    if 'target_type' in data:
        announcement.target_type = data['target_type']
    if 'target_value' in data:
        announcement.target_value = str(data['target_value']) if data['target_value'] else None

    # Handle rescheduling only if not yet sent
    if 'scheduled_for' in data:
        if announcement.notification_sent:
            return jsonify({'message': 'Cannot reschedule an announcement that has already been published'}), 400
        
        # Expecting ISO format string
        announcement.scheduled_for = datetime.fromisoformat(data['scheduled_for'].replace('Z', '+00:00'))
        
        # If rescheduled to now or past, send immediately
        if announcement.scheduled_for <= datetime.utcnow():
            send_announcement_notifications(announcement)
            announcement.notification_sent = True

    afg_db.session.commit()

    return jsonify({
        'id': announcement.id,
        'message': 'Announcement updated successfully',
        'notification_sent': announcement.notification_sent
    })

@announcements_api.route('/<int:announcement_id>', methods=['DELETE'])
@jwt_required()
def delete_announcement(announcement_id):
    """Delete an announcement"""
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)

    if current_user.user_type not in ['mentor', 'super-admin']:
        return jsonify({'message': 'Access denied'}), 403

    announcement = afg_db.session.get(Announcement, announcement_id)
    if not announcement:
        return jsonify({'message': 'Announcement not found'}), 404

    # Check ownership (unless admin)
    if current_user.user_type != 'super-admin' and announcement.created_by != current_user_id:
        return jsonify({'message': 'Access denied'}), 403

    afg_db.session.delete(announcement)
    afg_db.session.commit()

    return jsonify({'message': 'Announcement deleted successfully'})