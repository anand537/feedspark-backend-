from flask import Blueprint
# from app.api.students import students_api
from app.api.courses import courses_api
from app.api.assignments import assignments_api
from app.api.submissions import submissions_api
from app.api.meetings import meetings_api
from app.api.messages import messages_api
from app.api.feedback_templates import feedback_templates_api
from app.api.feedback import feedback_api
from app.api.users import users_api
from app.api.analytics import analytics_api
from app.api.announcements import announcements_api
from app.api.chat_groups import chat_groups_api

api_bp = Blueprint('api', __name__, url_prefix='/api')

# api_bp.register_blueprint(students_api)
api_bp.register_blueprint(courses_api)
api_bp.register_blueprint(assignments_api)
api_bp.register_blueprint(submissions_api)
api_bp.register_blueprint(meetings_api)
api_bp.register_blueprint(messages_api)
api_bp.register_blueprint(feedback_templates_api)
api_bp.register_blueprint(feedback_api)
api_bp.register_blueprint(users_api)
api_bp.register_blueprint(analytics_api)
api_bp.register_blueprint(announcements_api)
api_bp.register_blueprint(chat_groups_api)
