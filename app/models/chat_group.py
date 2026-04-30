from app.extensions import afg_db
from datetime import datetime
import uuid

class ChatGroup(afg_db.Model):
    __tablename__ = 'chat_groups'

    id = afg_db.Column(afg_db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = afg_db.Column(afg_db.String(255), nullable=False)
    course_id = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    created_by = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = afg_db.Column(afg_db.DateTime, default=datetime.utcnow)
    
    # Relationships
    members = afg_db.relationship('ChatGroupMember', backref='group', cascade='all, delete-orphan')
    messages = afg_db.relationship('GroupMessage', backref='group', cascade='all, delete-orphan')

class ChatGroupMember(afg_db.Model):
    __tablename__ = 'chat_group_members'

    id = afg_db.Column(afg_db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('chat_groups.id', ondelete='CASCADE'), nullable=False)
    user_id = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    joined_at = afg_db.Column(afg_db.DateTime, default=datetime.utcnow)

class GroupMessage(afg_db.Model):
    __tablename__ = 'group_messages'

    id = afg_db.Column(afg_db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('chat_groups.id', ondelete='CASCADE'), nullable=False)
    sender_id = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = afg_db.Column(afg_db.Text, nullable=False)
    sent_at = afg_db.Column(afg_db.DateTime, default=datetime.utcnow)
