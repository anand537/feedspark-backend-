import os
from assignment_ai import init_ai_clients, generate_ai_feedback
from app.models.course import Assignment
import sys
sys.path.append('..')

import json

print('Testing AI Feedback...')
init_ai_clients()

# Mock assignment
class MockAssignment:
    title = 'Test Quiz'
    type = 'quiz'
    questions = json.dumps([{'question': 'What is 2+2?', 'correct': '4'}])
    rubric_json = json.dumps({'criteria': [{'name': 'Accuracy', 'max': 10}]})

a = MockAssignment()

result = generate_ai_feedback(a, {'0': '4'})
print('Test Result:', result)
print('Switch test: ', 'Groq' if os.getenv('GROQ_API_KEY') else 'OpenAI fallback ready')

