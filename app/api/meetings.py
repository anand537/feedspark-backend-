from flask import Blueprint, request, jsonify, send_file, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Meeting, MeetingParticipant, User
from app.extensions import afg_db
from app.services.notification_service import NotificationService
from datetime import datetime
from sqlalchemy import or_
import uuid
import csv
import io

meetings_api = Blueprint('meetings_api', __name__, url_prefix='/meetings')

@meetings_api.route('/', methods=['GET'])
@jwt_required()
def get_meetings():
    """Get meetings relevant to the current user"""
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)

    query = Meeting.query

    if current_user.role != 'admin':
        # Filter: Created by user OR User is a participant
        query = query.outerjoin(MeetingParticipant, Meeting.id == MeetingParticipant.meeting_id)\
            .filter(or_(
                Meeting.created_by == current_user_id,
                MeetingParticipant.user_id == current_user_id
            )).distinct()

    meetings = query.order_by(Meeting.scheduled_at.desc()).all()
    result = []
    for meeting in meetings:
        creator = User.query.get(meeting.created_by) if meeting.created_by else None
        participants = MeetingParticipant.query.filter_by(meeting_id=meeting.id).all()
        result.append({
            'id': str(meeting.id),
            'title': meeting.title,
            'description': meeting.description,
            'scheduled_at': meeting.scheduled_at.isoformat() if meeting.scheduled_at else None,
            'duration': meeting.duration,
            'meeting_link': meeting.meeting_link,
            'status': meeting.status,
            'created_by': {
                'id': str(creator.id),
                'name': creator.name,
                'email': creator.email
            } if creator else None,
            'participants': [{
                'id': str(u.id),
                'name': u.name if u else 'Unknown',
                'email': u.email if u else 'Unknown',
                'joined_at': p.joined_at.isoformat() if p.joined_at else None,
                'status': p.status
            } for p in participants for u in [User.query.get(p.user_id)] if u],
            'created_at': meeting.created_at.isoformat() if meeting.created_at else None
        })
    return jsonify(result)

@meetings_api.route('/next-class', methods=['GET'])
@jwt_required()
def get_next_class():
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)

    query = Meeting.query.filter(Meeting.scheduled_at >= datetime.utcnow())
    query = query.outerjoin(MeetingParticipant, Meeting.id == MeetingParticipant.meeting_id)\
        .filter(or_(
            Meeting.created_by == current_user_id,
            MeetingParticipant.user_id == current_user_id
        )).distinct()

    next_meeting = query.order_by(Meeting.scheduled_at.asc()).first()
    if not next_meeting:
        return jsonify({'message': 'No upcoming class found'}), 404

    creator = afg_db.session.get(User, next_meeting.created_by) if next_meeting.created_by else None
    return jsonify({
        'id': str(next_meeting.id),
        'title': next_meeting.title,
        'description': next_meeting.description,
        'scheduled_at': next_meeting.scheduled_at.isoformat() if next_meeting.scheduled_at else None,
        'duration': next_meeting.duration,
        'meeting_link': next_meeting.meeting_link,
        'status': next_meeting.status,
        'created_by': {
            'id': str(creator.id),
            'name': creator.name,
            'email': creator.email
        } if creator else None
    })

@meetings_api.route('/<uuid:meeting_id>', methods=['GET'])
@jwt_required()
def get_meeting(meeting_id):
    """Get a specific meeting"""
    meeting = Meeting.query.get(meeting_id)
    if not meeting:
        return jsonify({'message': 'Meeting not found'}), 404

    creator = User.query.get(meeting.created_by) if meeting.created_by else None
    participants = MeetingParticipant.query.filter_by(meeting_id=meeting.id).all()

    return jsonify({
        'id': str(meeting.id),
        'title': meeting.title,
        'description': meeting.description,
        'scheduled_at': meeting.scheduled_at.isoformat() if meeting.scheduled_at else None,
        'duration': meeting.duration,
        'meeting_link': meeting.meeting_link,
        'status': meeting.status,
        'created_by': {
            'id': str(creator.id),
            'name': creator.name,
            'email': creator.email
        } if creator else None,
        'participants': [{
            'id': str(u.id),
            'name': u.name if u else 'Unknown',
            'email': u.email if u else 'Unknown',
            'joined_at': p.joined_at.isoformat() if p.joined_at else None,
            'status': p.status
        } for p in participants for u in [User.query.get(p.user_id)] if u],
        'created_at': meeting.created_at.isoformat() if meeting.created_at else None
    })

@meetings_api.route('/', methods=['POST'])
@jwt_required()
def create_meeting():
    """Create a new meeting"""
    data = request.get_json()
    if not data or 'title' not in data or 'scheduled_at' not in data or 'duration' not in data:
        return jsonify({'message': 'Title, scheduled_at, and duration are required'}), 400

    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if current_user.role not in ['mentor', 'admin']:
        return jsonify({'message': 'Only mentors and admins can create meetings'}), 403

    # Auto-generate Jitsi Meet link if not provided
    meeting_link = data.get('meeting_link')
    if not meeting_link:
        # Generate a unique room name using UUID to ensure no collisions
        room_name = f"AFG-{uuid.uuid4()}"
        meeting_link = f"https://meet.jit.si/{room_name}"

    meeting = Meeting(
        title=data['title'],
        description=data.get('description'),
        scheduled_at=datetime.fromisoformat(data['scheduled_at']),
        duration=data['duration'],
        meeting_link=meeting_link,
        created_by=current_user_id,
        created_at=datetime.utcnow()
    )

    afg_db.session.add(meeting)
    afg_db.session.commit()

    # Add participants if provided
    participant_ids = data.get('participant_ids', [])
    for user_id in participant_ids:
        participant = MeetingParticipant(meeting_id=meeting.id, user_id=user_id)
        afg_db.session.add(participant)
        
        # Notify participant
        NotificationService.create_notification(
            user_id=user_id,
            title=f"New Meeting: {meeting.title}",
            message=f"You have been invited to a meeting on {meeting.scheduled_at}",
            notification_type='meeting',
            email_notify=True
        )
    afg_db.session.commit()

    return jsonify({'id': str(meeting.id)}), 201

@meetings_api.route('/<uuid:meeting_id>', methods=['PUT'])
@jwt_required()
def update_meeting(meeting_id):
    """Update a meeting"""
    meeting = Meeting.query.get(meeting_id)
    if not meeting:
        return jsonify({'message': 'Meeting not found'}), 404

    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if current_user.role != 'admin' and meeting.created_by != current_user_id:
        return jsonify({'message': 'Access denied'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    if 'title' in data:
        meeting.title = data['title']
    if 'description' in data:
        meeting.description = data['description']
    if 'scheduled_at' in data:
        meeting.scheduled_at = datetime.fromisoformat(data['scheduled_at'])
    if 'duration' in data:
        meeting.duration = data['duration']
    if 'meeting_link' in data:
        meeting.meeting_link = data['meeting_link']
    if 'status' in data:
        meeting.status = data['status']

    afg_db.session.commit()

    # Update participants if provided
    if 'participant_ids' in data:
        # Remove existing participants
        MeetingParticipant.query.filter_by(meeting_id=meeting.id).delete()
        # Add new participants
        for user_id in data['participant_ids']:
            participant = MeetingParticipant(meeting_id=meeting.id, user_id=user_id)
            afg_db.session.add(participant)
        afg_db.session.commit()

    # Notify participants of update
    participants = MeetingParticipant.query.filter_by(meeting_id=meeting.id).all()
    for p in participants:
        NotificationService.create_notification(
            user_id=p.user_id,
            title=f"Meeting Updated: {meeting.title}",
            message=f"The meeting details have been updated.",
            notification_type='meeting'
        )

    return jsonify({'message': 'Meeting updated successfully'})

@meetings_api.route('/<uuid:meeting_id>/start', methods=['POST'])
@jwt_required()
def start_meeting(meeting_id):
    """Start a meeting (Mentor only)"""
    meeting = afg_db.session.get(Meeting, meeting_id)
    if not meeting:
        return jsonify({'message': 'Meeting not found'}), 404

    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)

    # Only creator (mentor) or admin can start
    if current_user.role != 'admin' and meeting.created_by != current_user_id:
        return jsonify({'message': 'Access denied'}), 403

    if not meeting.meeting_link:
        return jsonify({'message': 'No meeting link configured'}), 400

    meeting.status = 'in_progress'
    afg_db.session.commit()

    # Notify participants that meeting has started
    participants = MeetingParticipant.query.filter_by(meeting_id=meeting.id).all()
    for p in participants:
        NotificationService.create_notification(
            user_id=p.user_id,
            title=f"Meeting Started: {meeting.title}",
            message=f"The meeting '{meeting.title}' has started. Join now!",
            notification_type='meeting'
        )

    return jsonify({
        'message': 'Meeting started successfully',
        'meeting_link': meeting.meeting_link
    })

@meetings_api.route('/<uuid:meeting_id>/join', methods=['POST'])
@jwt_required()
def join_meeting(meeting_id):
    """Record attendance and return meeting link"""
    meeting = afg_db.session.get(Meeting, meeting_id)
    if not meeting:
        return jsonify({'message': 'Meeting not found'}), 404

    current_user_id = get_jwt_identity()
    
    # Check if user is a participant
    participant = MeetingParticipant.query.filter_by(
        meeting_id=meeting.id, 
        user_id=current_user_id
    ).first()

    # If not explicitly invited, check if they are the creator
    if not participant:
        if meeting.created_by == current_user_id:
            return jsonify({'meeting_link': meeting.meeting_link})
        return jsonify({'message': 'You are not invited to this meeting'}), 403

    # Record attendance if not already recorded
    if not participant.joined_at:
        participant.joined_at = datetime.utcnow()
        participant.status = 'present'
        afg_db.session.commit()

    return jsonify({
        'meeting_link': meeting.meeting_link,
        'message': 'Attendance recorded'
    })

@meetings_api.route('/<uuid:meeting_id>/attendance/<uuid:user_id>', methods=['PUT'])
@jwt_required()
def update_attendance(meeting_id, user_id):
    """Manually update attendance status for a participant"""
    meeting = afg_db.session.get(Meeting, meeting_id)
    if not meeting:
        return jsonify({'message': 'Meeting not found'}), 404

    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)

    # Only creator (mentor) or admin can update attendance manually
    if current_user.role != 'admin' and meeting.created_by != current_user_id:
        return jsonify({'message': 'Access denied'}), 403

    participant = MeetingParticipant.query.filter_by(meeting_id=meeting_id, user_id=user_id).first()
    if not participant:
        return jsonify({'message': 'Participant not found in this meeting'}), 404

    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'message': 'Status is required'}), 400

    new_status = data['status']
    if new_status not in ['present', 'absent', 'pending']:
        return jsonify({'message': 'Invalid status. Allowed: present, absent, pending'}), 400

    participant.status = new_status
    afg_db.session.commit()

    return jsonify({
        'message': 'Attendance updated successfully',
        'user_id': str(user_id),
        'status': new_status
    })

@meetings_api.route('/<uuid:meeting_id>', methods=['DELETE'])
@jwt_required()
def delete_meeting(meeting_id):
    """Delete a meeting"""
    meeting = Meeting.query.get(meeting_id)
    if not meeting:
        return jsonify({'message': 'Meeting not found'}), 404

    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if current_user.role != 'admin' and meeting.created_by != current_user_id:
        return jsonify({'message': 'Access denied'}), 403

    # Notify participants before deletion
    participants = MeetingParticipant.query.filter_by(meeting_id=meeting.id).all()
    for p in participants:
        NotificationService.create_notification(
            user_id=p.user_id,
            title=f"Meeting Cancelled: {meeting.title}",
            message=f"The meeting scheduled for {meeting.scheduled_at} has been cancelled.",
            notification_type='meeting'
        )

    # Delete participants first
    MeetingParticipant.query.filter_by(meeting_id=meeting.id).delete()
    afg_db.session.delete(meeting)
    afg_db.session.commit()

    return jsonify({'message': 'Meeting deleted successfully'})

@meetings_api.route('/<uuid:meeting_id>/export', methods=['GET'])
@jwt_required()
def export_attendance(meeting_id):
    """Export attendance list as CSV or PDF"""
    meeting = afg_db.session.get(Meeting, meeting_id)
    if not meeting:
        return jsonify({'message': 'Meeting not found'}), 404

    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)

    # Only creator (mentor) or admin can export
    if current_user.role != 'admin' and meeting.created_by != current_user_id:
        return jsonify({'message': 'Access denied'}), 403

    export_format = request.args.get('format', 'csv').lower()
    
    # Fetch participants
    participants = MeetingParticipant.query.filter_by(meeting_id=meeting.id).all()
    data = []
    for p in participants:
        user = afg_db.session.get(User, p.user_id)
        if user:
            data.append({
                'name': user.name,
                'email': user.email,
                'status': p.status,
                'joined_at': p.joined_at.strftime('%Y-%m-%d %H:%M:%S') if p.joined_at else 'N/A'
            })

    if export_format == 'csv':
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(['Name', 'Email', 'Status', 'Joined At'])
        for row in data:
            cw.writerow([row['name'], row['email'], row['status'], row['joined_at']])
        
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = f"attachment; filename=attendance_{meeting_id}.csv"
        output.headers["Content-type"] = "text/csv"
        return output

    elif export_format == 'pdf':
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
        except ImportError:
            return jsonify({'message': 'PDF generation library (reportlab) not installed'}), 500

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        elements.append(Paragraph(f"Attendance Report: {meeting.title}", styles['Title']))
        elements.append(Paragraph(f"Date: {meeting.scheduled_at.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 12))

        # Table Data
        table_data = [['Name', 'Email', 'Status', 'Joined At']]
        for row in data:
            table_data.append([row['name'], row['email'], row['status'], row['joined_at']])

        # Table Style
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"attendance_{meeting_id}.pdf",
            mimetype='application/pdf'
        )

    else:
        return jsonify({'message': 'Invalid format. Use csv or pdf'}), 400
