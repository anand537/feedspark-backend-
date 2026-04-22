import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_feedback_ai(student_name, communication, teamwork, creativity, critical_thinking, presentation):
    """
    Generate personalized performance feedback using OpenAI GPT.

    Args:
        student_name (str): Name of the student
        communication (int): Communication score (0-10)
        teamwork (int): Teamwork score (0-10)
        creativity (int): Creativity score (0-10)
        critical_thinking (int): Critical thinking score (0-10)
        presentation (int): Presentation score (0-10)

    Returns:
        str: Generated feedback text
    """
    prompt = f"""
    Write constructive, personalized performance feedback for a student named {student_name}, based on these scores:
    - Communication: {communication}/10
    - Teamwork: {teamwork}/10
    - Creativity: {creativity}/10
    - Critical Thinking: {critical_thinking}/10
    - Presentation: {presentation}/10

    Focus on strengths, one area of improvement, and how the student can improve further.
    Keep the feedback professional, encouraging, and specific.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides constructive feedback for students."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=250
        )
        feedback = response['choices'][0]['message']['content'].strip()
        return feedback
    except Exception as e:
        return f"Error generating feedback: {str(e)}"