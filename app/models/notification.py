from app.extensions import afg_db
from datetime import datetime

class Notification(afg_db.Model):
    __tablename__ = 'notifications'

    id = afg_db.Column(afg_db.Integer, primary_key=True)
    user_id = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('users.id'), nullable=False)
    title = afg_db.Column(afg_db.String(255), nullable=False)
    message = afg_db.Column(afg_db.Text, nullable=False)
    notification_type = afg_db.Column(afg_db.String(50), default='info')  # feedback, system, reminder
    is_read = afg_db.Column(afg_db.Boolean, default=False)
    created_at = afg_db.Column(afg_db.DateTime, default=datetime.utcnow)