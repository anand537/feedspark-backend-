from app.extensions import afg_db
from datetime import datetime

class MentorInput(afg_db.Model):
    __tablename__ = 'mentor_inputs'

    id = afg_db.Column(afg_db.Integer, primary_key=True)
    student_id = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('users.id', ondelete='CASCADE'))
    rubric_id = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('rubrics.id', ondelete='CASCADE'))
    evaluator_id = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('users.id', ondelete='SET NULL'))
    submitted_at = afg_db.Column(afg_db.DateTime)


class PerformanceData(afg_db.Model):
    __tablename__ = 'performance_data'

    id = afg_db.Column(afg_db.Integer, primary_key=True)
    mentor_input_id = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('mentor_inputs.id', ondelete='CASCADE'))
    criterion_id = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('criteria.id', ondelete='CASCADE'))
    score = afg_db.Column(afg_db.Integer)
    remarks = afg_db.Column(afg_db.Text)


class Feedback(afg_db.Model):
    __tablename__ = 'feedbacks'

    id = afg_db.Column(afg_db.Integer, primary_key=True)
    mentor_input_id = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('mentor_inputs.id', ondelete='CASCADE'))
    feedback_text = afg_db.Column(afg_db.Text)
    generated_at = afg_db.Column(afg_db.DateTime)

class FeedbackVersion(afg_db.Model):
    __tablename__ = 'feedback_versions'

    id = afg_db.Column(afg_db.Integer, primary_key=True)
    feedback_id = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('feedbacks.id', ondelete='CASCADE'))
    feedback_text = afg_db.Column(afg_db.Text)
    created_at = afg_db.Column(afg_db.DateTime, default=datetime.utcnow)
    version_number = afg_db.Column(afg_db.Integer)
    created_by = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('users.id', ondelete='SET NULL'))
