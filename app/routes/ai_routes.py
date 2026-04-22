from flask import Blueprint, request, jsonify
from app.services.ai_service import generate_feedback_ai

ai_bp = Blueprint('ai_bp', __name__)

@ai_bp.route('/generate-feedback', methods=['POST'])
def generate_feedback():
    data = request.get_json()

    try:
        feedback = generate_feedback_ai(
            student_name=data.get("student_name"),
            communication=data.get("communication"),
            teamwork=data.get("teamwork"),
            creativity=data.get("creativity"),
            critical_thinking=data.get("critical_thinking"),
            presentation=data.get("presentation")
        )
        return jsonify({"feedback": feedback}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500