from app.extensions import afg_db
from datetime import datetime
import uuid

class Rubric(afg_db.Model):
    __tablename__ = 'rubrics'

    id = afg_db.Column(afg_db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = afg_db.Column(afg_db.String(255), nullable=False)
    description = afg_db.Column(afg_db.Text)
    created_by = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = afg_db.Column(afg_db.DateTime, default=datetime.utcnow)


class Criterion(afg_db.Model):
    __tablename__ = 'criteria'

    id = afg_db.Column(afg_db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rubric_id = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('rubrics.id', ondelete='CASCADE'))
    name = afg_db.Column(afg_db.String(255), nullable=False)
    description = afg_db.Column(afg_db.Text)
    max_score = afg_db.Column(afg_db.Integer)
