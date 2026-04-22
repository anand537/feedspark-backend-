from app.extensions import afg_db, socketio
from app.models.notification import Notification
from app.models import User
from app.utils.email_utils import send_generic_notification_email
from datetime import datetime

class NotificationService:
    @staticmethod
    def create_notification(user_id, title, message, notification_type='info', email_notify=False):
        """
        Create a notification, save to DB, emit via Socket.IO, and optionally send email.
        """
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            created_at=datetime.utcnow()
        )
        
        afg_db.session.add(notification)
        afg_db.session.commit()
        
        # Real-time update via Socket.IO
        try:
            socketio.emit('new_notification', {
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'created_at': notification.created_at.isoformat()
            }, room=str(user_id))
        except Exception as e:
            print(f"Socket emit failed: {e}")

        # Email notification
        if email_notify:
            try:
                user = afg_db.session.get(User, user_id)
                if user and user.email:
                    send_generic_notification_email(user.email, user.name, title, message)
            except Exception as e:
                print(f"Email notification failed: {e}")
                
        return notification