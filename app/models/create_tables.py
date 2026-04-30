import os
from pathlib import Path
from app import create_app
from app.extensions import afg_db
from app.models import User, Rubric, Criterion, MentorInput, PerformanceData, Feedback, Course, Assignment, Submission, Meeting, MeetingParticipant, Message, FeedbackTemplate, Announcement, ChatGroup, ChatGroupMember, GroupMessage, FeedbackVersion

# Override DATABASE_URL for development - use SQLite for local development.
# Persist the database in the repository root so the file is easier to locate.
project_root = Path(__file__).resolve().parents[2]
local_db_path = project_root / 'afg.db'
os.environ['DATABASE_URL'] = f'sqlite:///{local_db_path.as_posix()}'
os.environ['FLASK_ENV'] = 'development'

app = create_app()

with app.app_context():
    afg_db.create_all()
    print("Tables created successfully!")
