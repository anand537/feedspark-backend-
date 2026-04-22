from app.extensions import afg_db

class FeedbackTemplate(afg_db.Model):
    __tablename__ = 'feedback_templates'

    id = afg_db.Column(afg_db.Integer, primary_key=True)
    name = afg_db.Column(afg_db.String(255), nullable=False)
    template_text = afg_db.Column(afg_db.Text, nullable=False)
    created_by = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = afg_db.Column(afg_db.DateTime)
