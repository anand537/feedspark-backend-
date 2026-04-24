"""
chatbot.py - Flask Blueprint for FeedSpark Chatbot (Powered by Groq)
Place this file in your Flask backend directory and register it as a blueprint.

Usage in your main app.py:
    from chatbot import chatbot_bp
    app.register_blueprint(chatbot_bp)

Install dependency:
    pip install groq

Set environment variable:
    export GROQ_API_KEY=your_groq_key_here
    Get your free key at: https://console.groq.com
"""

import os
from flask import Blueprint, request, jsonify
from groq import Groq
# At the top of chatbot.py, after imports
import os
print("GROQ KEY LOADED:", os.environ.get("GROQ_API_KEY", "NOT FOUND")) 

chatbot_bp = Blueprint("chatbot", __name__)

# Load website details once at startup
DETAILS_FILE = os.path.join(os.path.dirname(__file__), "website_details.txt")

def load_website_details():
    try:
        with open(DETAILS_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Website details not found."

WEBSITE_DETAILS = load_website_details()

SYSTEM_PROMPT = f"""You are FeedBot, a friendly and helpful assistant for FeedSpark — an online learning management system for educational institutions.

You answer questions ONLY based on the information provided below. If a question falls outside this information, politely say you don't have that info and suggest they contact support@feedspark.com.

Keep answers concise (2–4 sentences max), warm, and helpful. Use bullet points only when listing multiple items. Do not make up information.

=== PLATFORM INFORMATION ===
{WEBSITE_DETAILS}
"""

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


@chatbot_bp.route("/api/chatbot", methods=["POST"])
def chatbot():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400

    user_message = data["message"].strip()
    conversation_history = data.get("history", [])  # list of {role, content}

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    # Build messages array: system prompt + history + new message
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for entry in conversation_history[-10:]:  # Keep last 10 turns for context
        if entry.get("role") in ("user", "assistant") and entry.get("content"):
            messages.append({"role": entry["role"], "content": entry["content"]})

    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # Free, fast, and smart
            messages=messages,
            max_tokens=512,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chatbot_bp.route("/api/chatbot/suggestions", methods=["GET"])
def suggestions():
    """Return suggested questions for the chatbot UI."""
    role = request.args.get("role", "student")  # 'student' or 'instructor'

    student_suggestions = [
        "How do I enroll in a course?",
        "How do I submit an assignment?",
        "What is the attendance policy?",
        "How do I join a meeting?",
        "Can I view my grades?",
    ]

    instructor_suggestions = [
        "How do I create a course?",
        "How do I schedule a meeting?",
        "How do I provide feedback?",
        "What analytics are available?",
        "How do I manage announcements?",
    ]

    suggestions_list = instructor_suggestions if role == "instructor" else student_suggestions
    return jsonify({"suggestions": suggestions_list})