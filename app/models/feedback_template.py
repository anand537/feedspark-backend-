from app.extensions import afg_db
from datetime import datetime
import uuid

class FeedbackTemplate(afg_db.Model):
    __tablename__ = 'feedback_templates'

    id = afg_db.Column(afg_db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = afg_db.Column(afg_db.String(255), nullable=False)
    template_text = afg_db.Column(afg_db.Text, nullable=False)
    created_by = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = afg_db.Column(afg_db.DateTime, default=datetime.utcnow)
