from flask import Blueprint, render_template, request, jsonify
from app.services.ai_service import generate_feedback_ai
from app.models import Feedback
from app.extensions import afg_db

bp = Blueprint('main', __name__)

@bp.route('/', methods=['GET', 'POST'])
def index():
    feedback = None
    if request.method == 'POST':
        rubric = request.form['rubric']
        performance = request.form['performance']
        student_name = request.form.get('student_name', 'Student')

        try:
            # Integrating the actual AI service
            feedback_text = generate_feedback_ai(
                student_name=student_name,
                communication=5, # Defaulting or parsing from performance
                teamwork=5,
                creativity=5,
                critical_thinking=5,
                presentation=5
            )
        except Exception as e:
            feedback_text = f"Error generating feedback: {str(e)}"

        # Save feedback to the database
        new_feedback = Feedback(
            rubric_text=rubric,
            performance_text=performance,
            generated_feedback=feedback_text
        )
        afg_db.session.add(new_feedback)
        afg_db.session.commit()

        feedback = feedback_text

    return render_template('index.html', feedback=feedback)
