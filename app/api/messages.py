from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import afg_db
from app.models import Message, User
from datetime import datetime

messages_api = Blueprint('messages_api', __name__, url_prefix='/messages')

@messages_api.route('/', methods=['GET'])
@jwt_required()
def get_messages():
    """Get messages for current user"""
    current_user_id = get_jwt_identity()
    received = Message.query.filter_by(receiver_id=current_user_id).all()
    sent = Message.query.filter_by(sender_id=current_user_id).all()

    def serialize_message(m):
        sender = User.query.get(m.sender_id)
        receiver = User.query.get(m.receiver_id)
        return {
            'id': str(m.id),
            'sender': {'id': str(sender.id), 'name': sender.name, 'email': sender.email} if sender else None,
            'receiver': {'id': str(receiver.id), 'name': receiver.name, 'email': receiver.email} if receiver else None,
            'content': m.content,
            'sent_at': m.sent_at.isoformat() if m.sent_at else None,
            'read_at': m.read_at.isoformat() if m.read_at else None
        }

    return jsonify({
        'received': [serialize_message(m) for m in received],
        'sent': [serialize_message(m) for m in sent]
    })

@messages_api.route('/<uuid:message_id>', methods=['GET'])
@jwt_required()
def get_message(message_id):
    """Get a specific message"""
    message = Message.query.get(message_id)
    if not message:
        return jsonify({'message': 'Message not found'}), 404

    current_user_id = get_jwt_identity()
    if message.sender_id != current_user_id and message.receiver_id != current_user_id:
        return jsonify({'message': 'Access denied'}), 403

    sender = User.query.get(message.sender_id)
    receiver = User.query.get(message.receiver_id)

    return jsonify({
        'id': str(message.id),
        'sender': {'id': str(sender.id), 'name': sender.name, 'email': sender.email} if sender else None,
        'receiver': {'id': str(receiver.id), 'name': receiver.name, 'email': receiver.email} if receiver else None,
        'content': message.content,
        'sent_at': message.sent_at.isoformat() if message.sent_at else None,
        'read_at': message.read_at.isoformat() if message.read_at else None
    })

@messages_api.route('/', methods=['POST'])
@jwt_required()
def send_message():
    """Send a new message"""
    data = request.get_json()
    if not data or 'receiver_id' not in data or 'content' not in data:
        return jsonify({'message': 'receiver_id and content are required'}), 400

    # Verify receiver exists
    receiver = User.query.get(data['receiver_id'])
    if not receiver:
        return jsonify({'message': 'Receiver not found'}), 404

    current_user_id = get_jwt_identity()
    sender = User.query.get(current_user_id)

    if not sender:
        return jsonify({'message': 'Sender not found'}), 404

    # Enforce messaging restrictions
    if sender.role == 'student' and receiver.role != 'mentor':
        return jsonify({'message': 'Students can only message mentors'}), 403
    
    if sender.role == 'mentor' and receiver.role != 'student':
        return jsonify({'message': 'Mentors can only message students'}), 403

    message = Message(
        sender_id=current_user_id,
        receiver_id=data['receiver_id'],
        content=data['content'],
        sent_at=datetime.utcnow()
    )

    afg_db.session.add(message)
    afg_db.session.commit()

    # Emit real-time message via Socket.IO
    from app.extensions import socketio
    socketio.emit('new_message', {
        'id': str(message.id),
        'sender_id': str(message.sender_id),
        'receiver_id': str(message.receiver_id),
        'content': message.content,
        'sent_at': message.sent_at.isoformat()
    }, room=str(data['receiver_id']))

    return jsonify({
        'id': str(message.id),
        'sender_id': str(message.sender_id),
        'receiver_id': str(message.receiver_id),
        'content': message.content,
        'sent_at': message.sent_at.isoformat()
    }), 201

@messages_api.route('/<uuid:message_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(message_id):
    """Mark a message as read"""
    message = Message.query.get(message_id)
    if not message:
        return jsonify({'message': 'Message not found'}), 404

    current_user_id = int(get_jwt_identity())
    if message.receiver_id != current_user_id:
        return jsonify({'message': 'Access denied'}), 403

    message.read_at = datetime.utcnow()
    afg_db.session.commit()

    # Emit real-time update via Socket.IO
    from app.extensions import socketio
    socketio.emit('message_read', {
        'message_id': message_id,
        'read_at': message.read_at.isoformat()
    }, room=str(current_user_id))

    return jsonify({'message': 'Message marked as read'})

@messages_api.route('/<uuid:message_id>', methods=['DELETE'])
@jwt_required()
def delete_message(message_id):
    """Delete a message"""
    message = Message.query.get(message_id)
    if not message:
        return jsonify({'message': 'Message not found'}), 404

    current_user_id = int(get_jwt_identity())
    if message.sender_id != current_user_id and message.receiver_id != current_user_id:
        return jsonify({'message': 'Access denied'}), 403

    afg_db.session.delete(message)
    afg_db.session.commit()

    return jsonify({'message': 'Message deleted successfully'})
