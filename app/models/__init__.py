# Import all models to register them with SQLAlchemy
from .course import Course, Assignment, Submission
from .feedback_template import FeedbackTemplate
from .feedback import Feedback, MentorInput, PerformanceData, FeedbackVersion
from .meeting import Meeting, MeetingParticipant
from .message import Message
from .rubric import Rubric, Criterion
from .user import User
from .token_blocklist import TokenBlocklist
from .notification import Notification
from .announcement import Announcement
from .chat_group import ChatGroup, ChatGroupMember, GroupMessage
