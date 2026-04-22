from app.extensions import afg_db

class Rubric(afg_db.Model):
    __tablename__ = 'rubrics'

    id = afg_db.Column(afg_db.Integer, primary_key=True)
    title = afg_db.Column(afg_db.String(255), nullable=False)
    description = afg_db.Column(afg_db.Text)
    created_by = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = afg_db.Column(afg_db.DateTime)


class Criterion(afg_db.Model):
    __tablename__ = 'criteria'

    id = afg_db.Column(afg_db.Integer, primary_key=True)
    rubric_id = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('rubrics.id', ondelete='CASCADE'))
    name = afg_db.Column(afg_db.String(255), nullable=False)
    description = afg_db.Column(afg_db.Text)
    max_score = afg_db.Column(afg_db.Integer)
