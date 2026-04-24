from app.extensions import afg_db

class Course(afg_db.Model):
    __tablename__ = 'courses'

    id = afg_db.Column(afg_db.Integer, primary_key=True)
    title = afg_db.Column(afg_db.String(255), nullable=False)
    description = afg_db.Column(afg_db.Text)
    instructor_id = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = afg_db.Column(afg_db.DateTime)
    status = afg_db.Column(afg_db.String(50), default='active')  # active, completed, archived


class Assignment(afg_db.Model):
    __tablename__ = 'assignments'

    id = afg_db.Column(afg_db.Integer, primary_key=True)
    course_id = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('courses.id', ondelete='CASCADE'))
    title = afg_db.Column(afg_db.String(255), nullable=False)
    description = afg_db.Column(afg_db.Text)
    due_date = afg_db.Column(afg_db.DateTime)
    created_at = afg_db.Column(afg_db.DateTime)
    status = afg_db.Column(afg_db.String(50), default='active')  # active, completed
    type = afg_db.Column(afg_db.String(50), default='essay')  # quiz, essay, coding
    rubric_id = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('rubrics.id', ondelete='SET NULL'))
    questions = afg_db.Column(afg_db.Text)  # JSON string for quiz/coding
    max_score = afg_db.Column(afg_db.Integer, default=100)
    rubric_json = afg_db.Column(afg_db.Text)  # JSON rubric from mentor


class Submission(afg_db.Model):
    __tablename__ = 'submissions'

    id = afg_db.Column(afg_db.Integer, primary_key=True)
    assignment_id = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('assignments.id', ondelete='CASCADE'))
    student_id = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('users.id', ondelete='CASCADE'))
    submitted_at = afg_db.Column(afg_db.DateTime)
    file_url = afg_db.Column(afg_db.String(500))
    status = afg_db.Column(afg_db.String(50), default='submitted')  # submitted, graded
    score = afg_db.Column(afg_db.Float)
    feedback = afg_db.Column(afg_db.Text)
    answers = afg_db.Column(afg_db.Text)  # JSON answers for quiz/essay/coding
    ai_feedback = afg_db.Column(afg_db.Text)  # AI generated JSON feedback
