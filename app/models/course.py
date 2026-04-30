from app.extensions import afg_db
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

# Enrollment association table (with progress/status tracking)
enrollments = afg_db.Table(
    'enrollments',
    afg_db.Column('id', afg_db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    afg_db.Column('course_id', afg_db.UUID(as_uuid=True), afg_db.ForeignKey('courses.id', ondelete='CASCADE')),
    afg_db.Column('student_id', afg_db.UUID(as_uuid=True), afg_db.ForeignKey('users.id', ondelete='CASCADE')),
    afg_db.Column('progress', afg_db.Integer, default=0),  # 0-100
    afg_db.Column('status', afg_db.String(50), default='active'),  # active, completed, dropped
    afg_db.Column('enrolled_at', afg_db.DateTime, default=datetime.utcnow),
    afg_db.Column('completed_at', afg_db.DateTime),
    afg_db.Column('created_at', afg_db.DateTime, default=datetime.utcnow),
    afg_db.UniqueConstraint('course_id', 'student_id', name='uq_enrollment_course_student')
)

class Course(afg_db.Model):
    __tablename__ = 'courses'

    id = afg_db.Column(afg_db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = afg_db.Column(afg_db.String(255), nullable=False)
    description = afg_db.Column(afg_db.Text)
    mentor_id = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('users.id', ondelete='SET NULL'))
    duration_weeks = afg_db.Column(afg_db.Integer)
    price = afg_db.Column(afg_db.Numeric(10, 2))
    rating = afg_db.Column(afg_db.Numeric(3, 2))
    created_at = afg_db.Column(afg_db.DateTime, default=datetime.utcnow)
    status = afg_db.Column(afg_db.String(50), default='active')  # active, completed, archived
    students = relationship('User', secondary=enrollments, back_populates='enrolled_courses')


class Assignment(afg_db.Model):
    __tablename__ = 'assignments'

    id = afg_db.Column(afg_db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('courses.id', ondelete='CASCADE'))
    title = afg_db.Column(afg_db.String(255), nullable=False)
    description = afg_db.Column(afg_db.Text)
    due_date = afg_db.Column(afg_db.DateTime)
    created_at = afg_db.Column(afg_db.DateTime, default=datetime.utcnow)
    status = afg_db.Column(afg_db.String(50), default='active')  # active, completed
    type = afg_db.Column(afg_db.String(50), default='essay')  # quiz, essay, coding
    rubric_id = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('rubrics.id', ondelete='SET NULL'))
    questions = afg_db.Column(afg_db.Text)  # JSON string for quiz/coding
    max_score = afg_db.Column(afg_db.Integer, default=100)
    rubric_json = afg_db.Column(afg_db.Text)  # JSON rubric from mentor


class Submission(afg_db.Model):
    __tablename__ = 'submissions'

    id = afg_db.Column(afg_db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('assignments.id', ondelete='CASCADE'))
    student_id = afg_db.Column(afg_db.UUID(as_uuid=True), afg_db.ForeignKey('users.id', ondelete='CASCADE'))
    submitted_at = afg_db.Column(afg_db.DateTime, default=datetime.utcnow)
    file_url = afg_db.Column(afg_db.String(500))
    status = afg_db.Column(afg_db.String(50), default='submitted')  # submitted, graded
    score = afg_db.Column(afg_db.Float)
    feedback = afg_db.Column(afg_db.Text)
    answers = afg_db.Column(afg_db.Text)  # JSON answers for quiz/essay/coding
    ai_feedback = afg_db.Column(afg_db.Text)  # AI generated JSON feedback
