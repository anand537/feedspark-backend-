from flask_socketio import emit, join_room
from flask_jwt_extended import decode_token
from app.extensions import socketio
from app.models import ChatGroupMember

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('authenticate')
def handle_authenticate(data):
    """
    Event for client to authenticate and join their user-specific room.
    Client should emit 'authenticate' with {'token': 'JWT_TOKEN'}
    """
    token = data.get('token')
    if not token:
        return emit('error', {'message': 'Token required'})
    
    try:
        decoded = decode_token(token)
        user_id = decoded['sub']  # 'sub' contains the identity (user_id)
        join_room(str(user_id))
        
        # Join all group chat rooms the user is a member of
        memberships = ChatGroupMember.query.filter_by(user_id=user_id).all()
        for membership in memberships:
            join_room(f"group_{membership.group_id}")
            
        emit('authenticated', {'message': f'Joined room {user_id}'})
    except Exception as e:
        emit('error', {'message': 'Invalid token'})