from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import afg_db, socketio
from app.models import ChatGroup, ChatGroupMember, GroupMessage, Course, User
from datetime import datetime

chat_groups_api = Blueprint('chat_groups_api', __name__, url_prefix='/chat-groups')

@chat_groups_api.route('/', methods=['POST'])
@jwt_required()
def create_group():
    """Create a new chat group for a course (Mentor only)"""
    current_user_id = get_jwt_identity()
    current_user = afg_db.session.get(User, current_user_id)

    if current_user.role not in ['mentor', 'admin']:
        return jsonify({'message': 'Only mentors can create groups'}), 403

    data = request.get_json()
    if not data or 'course_id' not in data or 'name' not in data:
        return jsonify({'message': 'course_id and name are required'}), 400

    course = afg_db.session.get(Course, data['course_id'])
    if not course:
        return jsonify({'message': 'Course not found'}), 404

    # Create Group
    group = ChatGroup(
        name=data['name'],
        course_id=course.id,
        created_by=current_user_id
    )
    afg_db.session.add(group)
    afg_db.session.flush() # Get ID

    # Add Creator (Mentor)
    mentor_member = ChatGroupMember(group_id=group.id, user_id=current_user_id)
    afg_db.session.add(mentor_member)

    # Add Enrolled Students
    count = 0
    for student in course.students:
        member = ChatGroupMember(group_id=group.id, user_id=student.id)
        afg_db.session.add(member)
        count += 1

    afg_db.session.commit()

    return jsonify({
        'id': str(group.id),
        'name': group.name,
        'members_count': count + 1,
        'message': 'Group created successfully'
    }), 201

@chat_groups_api.route('/', methods=['GET'])
@jwt_required()
def get_my_groups():
    """Get groups the current user is a member of"""
    current_user_id = get_jwt_identity()
    
    # Join ChatGroupMember to find groups
    memberships = ChatGroupMember.query.filter_by(user_id=current_user_id).all()
    group_ids = [m.group_id for m in memberships]
    
    groups = ChatGroup.query.filter(ChatGroup.id.in_(group_ids)).all()
    
    result = []
    for g in groups:
        result.append({
            'id': str(g.id),
            'name': g.name,
            'course_id': str(g.course_id),
            'created_at': g.created_at.isoformat()
        })
    
    return jsonify(result)

@chat_groups_api.route('/<uuid:group_id>/messages', methods=['GET'])
@jwt_required()
def get_group_messages(group_id):
    """Get messages for a group"""
    current_user_id = get_jwt_identity()
    
    # Verify membership
    is_member = ChatGroupMember.query.filter_by(group_id=group_id, user_id=current_user_id).first()
    if not is_member:
        return jsonify({'message': 'Access denied'}), 403
        
    messages = GroupMessage.query.filter_by(group_id=group_id).order_by(GroupMessage.sent_at.asc()).all()
    
    result = []
    for m in messages:
        sender = afg_db.session.get(User, m.sender_id)
        result.append({
            'id': str(m.id),
            'content': m.content,
            'sender': {
                'id': str(sender.id),
                'name': sender.name
            } if sender else None,
            'sent_at': m.sent_at.isoformat()
        })
        
    return jsonify(result)

@chat_groups_api.route('/<uuid:group_id>/messages', methods=['POST'])
@jwt_required()
def send_group_message(group_id):
    """Send a message to a group"""
    current_user_id = get_jwt_identity()
    
    # Verify membership
    is_member = ChatGroupMember.query.filter_by(group_id=group_id, user_id=current_user_id).first()
    if not is_member:
        return jsonify({'message': 'Access denied'}), 403
        
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'message': 'Content is required'}), 400
        
    message = GroupMessage(
        group_id=group_id,
        sender_id=current_user_id,
        content=data['content']
    )
    
    afg_db.session.add(message)
    afg_db.session.commit()
    
    # Emit Socket Event
    sender = afg_db.session.get(User, current_user_id)
    socketio.emit('new_group_message', {
        'id': str(message.id),
        'group_id': str(group_id),
        'content': message.content,
        'sender': {
            'id': str(sender.id),
            'name': sender.name
        },
        'sent_at': message.sent_at.isoformat()
    }, room=f"group_{group_id}")
    
    return jsonify({'message': 'Message sent', 'id': str(message.id)}), 201