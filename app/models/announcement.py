from app.extensions import afg_db
from datetime import datetime
import uuid

class Announcement(afg_db.Model):
    __tablename__ = 'announcements'

    id = afg_db.Column(afg_db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = afg_db.Column(afg_db.String(255), nullable=False)
    content = afg_db.Column(afg_db.Text, nullable=False)
    created_by = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = afg_db.Column(afg_db.DateTime, default=datetime.utcnow)
    
    # Target audience configuration
    target_type = afg_db.Column(afg_db.String(50), default='all')  # Options: 'all', 'role', 'course'
    target_value = afg_db.Column(afg_db.String(50), nullable=True) # e.g., 'student', 'mentor', or course_id

    scheduled_for = afg_db.Column(afg_db.DateTime, default=datetime.utcnow)
    notification_sent = afg_db.Column(afg_db.Boolean, default=False)
