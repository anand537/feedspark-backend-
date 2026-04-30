from app.extensions import afg_db
from datetime import datetime
import uuid

class Notification(afg_db.Model):
    __tablename__ = 'notifications'

    id = afg_db.Column(afg_db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('users.id'), nullable=False)
    title = afg_db.Column(afg_db.String(255), nullable=False)
    message = afg_db.Column(afg_db.Text, nullable=False)
    notification_type = afg_db.Column(afg_db.String(50), default='info')  # feedback, system, reminder
    is_read = afg_db.Column(afg_db.Boolean, default=False)
    action_url = afg_db.Column(afg_db.Text)
    created_at = afg_db.Column(afg_db.DateTime, default=datetime.utcnow)
