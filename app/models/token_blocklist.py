from app.extensions import afg_db
from datetime import datetime

class TokenBlocklist(afg_db.Model):
    __tablename__ = 'token_blocklist'

    id = afg_db.Column(afg_db.Integer, primary_key=True)
    jti = afg_db.Column(afg_db.String(36), nullable=False, index=True)
    created_at = afg_db.Column(afg_db.DateTime, nullable=False, default=datetime.utcnow)