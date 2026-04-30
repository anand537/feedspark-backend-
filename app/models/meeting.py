from app.extensions import afg_db
from datetime import datetime
import uuid

class Meeting(afg_db.Model):
    __tablename__ = 'meetings'

    id = afg_db.Column(afg_db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = afg_db.Column(afg_db.String(255), nullable=False)
    description = afg_db.Column(afg_db.Text)
    scheduled_at = afg_db.Column(afg_db.DateTime)
    duration = afg_db.Column(afg_db.Integer, default=30)  # in minutes
    created_by = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = afg_db.Column(afg_db.DateTime, default=datetime.utcnow)
    meeting_link = afg_db.Column(afg_db.String(500))
    status = afg_db.Column(afg_db.String(50), default='scheduled')  # scheduled, cancelled, completed
    attendance_processed = afg_db.Column(afg_db.Boolean, default=False)


class MeetingParticipant(afg_db.Model):
    __tablename__ = 'meeting_participants'

    id = afg_db.Column(afg_db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('meetings.id', ondelete='CASCADE'))
    user_id = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('users.id', ondelete='CASCADE'))
    joined_at = afg_db.Column(afg_db.DateTime, nullable=True)
    status = afg_db.Column(afg_db.String(20), default='pending')  # pending, present, absent
