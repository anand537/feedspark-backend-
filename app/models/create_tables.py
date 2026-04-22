import os
from app import create_app
from app.extensions import afg_db
from app.models import User, Rubric, Criterion, MentorInput, PerformanceData, Feedback, Course, Assignment, Submission, Meeting, MeetingParticipant, Message, FeedbackTemplate, Announcement, ChatGroup, ChatGroupMember, GroupMessage, FeedbackVersion

# Override DATABASE_URL for development - use SQLite for local development
os.environ['DATABASE_URL'] = 'sqlite:///afg.db'
os.environ['FLASK_ENV'] = 'development'

app = create_app()

with app.app_context():
    afg_db.create_all()
    print("Tables created successfully!")
