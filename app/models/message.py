from app.extensions import afg_db

class Message(afg_db.Model):
    __tablename__ = 'messages'

    id = afg_db.Column(afg_db.Integer, primary_key=True)
    sender_id = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('users.id', ondelete='CASCADE'))
    receiver_id = afg_db.Column(afg_db.Integer, afg_db.ForeignKey('users.id', ondelete='CASCADE'))
    content = afg_db.Column(afg_db.Text, nullable=False)
    sent_at = afg_db.Column(afg_db.DateTime)
    read_at = afg_db.Column(afg_db.DateTime)
