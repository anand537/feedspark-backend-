from app.extensions import afg_db
from werkzeug.security import generate_password_hash, check_password_hash
from .course import enrollments
import secrets
from datetime import datetime, timedelta
import uuid

class User(afg_db.Model):
    enrolled_courses = afg_db.relationship('Course', secondary=enrollments, back_populates='students')
    __tablename__ = 'users'

    id = afg_db.Column(afg_db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = afg_db.Column(afg_db.String(255))
    email = afg_db.Column(afg_db.String(255), unique=True, nullable=False)
    password_hash = afg_db.Column(afg_db.String(255), nullable=False)
    role = afg_db.Column(afg_db.String(50), nullable=False, default='student')  # 'admin', 'mentor', 'student'
    avatar_url = afg_db.Column(afg_db.Text)
    created_at = afg_db.Column(afg_db.DateTime, default=datetime.utcnow)
    notification_preferences = afg_db.Column(afg_db.Text, default='{}')

    # Email verification fields
    email_verified = afg_db.Column(afg_db.Boolean, default=False)
    email_verification_token = afg_db.Column(afg_db.String(255), unique=True)
    email_verification_expires = afg_db.Column(afg_db.DateTime)

    # Admin approval status
    status = afg_db.Column(afg_db.String(20), default='pending')  # pending, approved, rejected

    # Password reset fields
    password_reset_token = afg_db.Column(afg_db.String(255), unique=True)
    password_reset_expires = afg_db.Column(afg_db.DateTime)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def generate_email_verification_token(self):
        """Generate a secure token for email verification"""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
        return self.email_verification_token

    def verify_email(self, token):
        """Verify email with token"""
        if (self.email_verification_token == token and
            self.email_verification_expires > datetime.utcnow()):
            self.email_verified = True
            self.email_verification_token = None
            self.email_verification_expires = None
            return True
        return False

    def generate_password_reset_token(self):
        """Generate a secure token for password reset"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        return self.password_reset_token

    def reset_password(self, token, new_password):
        """Reset password with token"""
        if (self.password_reset_token == token and
            self.password_reset_expires > datetime.utcnow()):
            self.set_password(new_password)
            self.password_reset_token = None
            self.password_reset_expires = None
            return True
        return False

    def __repr__(self):
        return f"<User {self.email}>"
