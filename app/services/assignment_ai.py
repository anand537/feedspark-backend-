import os
import json
from datetime import datetime
from groq import Groq
from openai import OpenAI
from flask import current_app

client_groq = None
client_openai = None

def init_ai_clients(app=None):
    global client_groq, client_openai
    groq_key = os.environ.get("GROQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if groq_key:
        client_groq = Groq(api_key=groq_key)
        if app:
            app.logger.info("Groq client initialized")
    
    if openai_key:
        client_openai = OpenAI(api_key=openai_key)
        if app:
            app.logger.info("OpenAI client initialized")

def generate_ai_feedback(assignment, answers, file_url=None):
    """
    Generate AI feedback using Groq (primary) or OpenAI fallback.
    assignment: Assignment model instance
    answers: dict of student answers (JSON)
    file_url: optional file path
    """
    if not client_groq and not client_openai:
        return {
            "error": "No AI client available. Set GROQ_API_KEY or OPENAI_API_KEY."
        }
    
    atype = getattr(assignment, 'type', 'essay') or 'essay'
    rubric_text = "No rubric"  # Fetch from rubric_id if needed
    questions = json.loads(getattr(assignment, 'questions', '[]'))
    max_score = getattr(assignment, 'max_score', 100)
    
    # Build prompt like original
    if atype == "quiz":
        qa_pairs = []
        correct_count = 0
        for i, q in enumerate(questions):
            student_ans = answers.get(str(i), "")
            correct = q.get("correct", "")
            is_correct = str(student_ans).strip().lower() == str(correct).strip().lower()
            if is_correct:
                correct_count += 1
            qa_pairs.append(
                f"Q{i+1}: {q['question']}\\n  Student: {student_ans}\\n  Correct: {correct}\\n  Result: {'✓' if is_correct else '✗'}"
            )
        raw_score = round((correct_count / max(len(questions), 1)) * max_score)
        qa_text = "\\n".join(qa_pairs)
        
        prompt = f"""Quiz submission analysis.

Assignment: {assignment.title}
Score: {raw_score}/{max_score}
Rubric: {rubric_text}

{qa_text}

JSON response only:
{{
  "score": {raw_score},
  "percentage": {round(raw_score/max_score*100)},
  "grade": "A/B/C/D/F",
  "overall_comment": "...",
  "strengths": [...],
  "improvements": [...],
  "rubric_breakdown": [{{"criterion": "...", "score": 0, "max": 10, "comment": "..."}}],
  "encouragement": "..."
}}"""
    
    else:  # essay/coding
        content = answers.get('content', '') or file_url or 'No content'
        prompt = f"""Evaluate {'essay' if atype=='essay' else 'code'}.

Title: {assignment.title}
Rubric: {rubric_text}
Student work: {content[:2000]}

JSON response:
{{
  "score": 85,
  "percentage": 85,
  "grade": "B",
  "overall_comment": "...",
  "strengths": [...],
  "improvements": [...],
  "rubric_breakdown": [...],
  "encouragement": "..."
}}"""
    
    # Try Groq first
    if client_groq:
        try:
            resp = client_groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.3
            )
            text = resp.choices[0].message.content.strip()
        except Exception as e:
            current_app.logger.warning(f"Groq failed: {e}")
            text = None
    
    # Fallback OpenAI
    if not text and client_openai:
        try:
            resp = client_openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.3
            )
            text = resp.choices[0].message.content.strip()
        except Exception as e:
            current_app.logger.error(f"OpenAI failed: {e}")
    
    if text:
        # Parse JSON
        text = text.replace('```json', '').replace('```', '').strip()
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1:
            try:
                result = json.loads(text[start:end])
                result.setdefault("score", 0)
                result["score"] = float(result["score"])
                return result
            except:
                pass
    
    return {
        "score": 0,
        "percentage": 0,
        "grade": "N/A",
        "overall_comment": "Feedback unavailable.",
        "strengths": [],
        "improvements": [],
        "rubric_breakdown": [],
        "encouragement": "Keep learning!"
    }

