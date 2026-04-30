from app.extensions import afg_db
from datetime import datetime
import uuid

class TokenBlocklist(afg_db.Model):
    __tablename__ = 'token_blocklist'

    id = afg_db.Column(afg_db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jti = afg_db.Column(afg_db.String(36), nullable=False, unique=True, index=True)
    created_at = afg_db.Column(afg_db.DateTime, nullable=False, default=datetime.utcnow)
