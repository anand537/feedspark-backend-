from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.notification import Notification
from app.extensions import afg_db

notification_bp = Blueprint('notification_bp', __name__, url_prefix='/notifications')

@notification_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get notifications for the current user"""
    current_user_id = get_jwt_identity()
    # Get unread first, then sorted by date
    notifications = Notification.query.filter_by(user_id=current_user_id)\
        .order_by(Notification.is_read.asc(), Notification.created_at.desc())\
        .limit(50).all()
        
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.notification_type,
        'is_read': n.is_read,
        'created_at': n.created_at.isoformat()
    } for n in notifications])

@notification_bp.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(notification_id):
    """Mark a specific notification as read"""
    current_user_id = get_jwt_identity()
    notification = afg_db.session.get(Notification, notification_id)
    
    if not notification or notification.user_id != current_user_id:
        return jsonify({'message': 'Notification not found or access denied'}), 404
        
    if not notification.is_read:
        notification.is_read = True
        afg_db.session.commit()
        
    return jsonify({'message': 'Marked as read'})

@notification_bp.route('/mark-all-read', methods=['PUT'])
@jwt_required()
def mark_all_read():
    """Mark all notifications as read for current user"""
    current_user_id = get_jwt_identity()
    Notification.query.filter_by(user_id=current_user_id, is_read=False).update({'is_read': True})
    afg_db.session.commit()
    return jsonify({'message': 'All notifications marked as read'})