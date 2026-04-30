from app.extensions import afg_db
from datetime import datetime
import uuid

class Message(afg_db.Model):
    __tablename__ = 'messages'

    id = afg_db.Column(afg_db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('users.id', ondelete='CASCADE'))
    receiver_id = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('users.id', ondelete='CASCADE'))
    content = afg_db.Column(afg_db.Text, nullable=False)
    sent_at = afg_db.Column(afg_db.DateTime, default=datetime.utcnow)
    read_at = afg_db.Column(afg_db.DateTime)
