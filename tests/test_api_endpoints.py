import unittest
import json
import os
from datetime import datetime
from unittest.mock import patch
from app import create_app, afg_db
from flask_jwt_extended import create_access_token
from app.models import User, Rubric, Criterion, FeedbackTemplate, Course, Assignment

class APITestCase(unittest.TestCase):
    def setUp(self):
        # Set testing environment variables before creating app
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['SUPABASE_URL'] = ''
        os.environ['SUPABASE_ANON_KEY'] = ''
        self.app = create_app('config.Config')
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            afg_db.create_all()
            # Create a test user for authentication
            user = User(name="Test User", email="test@example.com", user_type="mentor")
            user.set_password("Password123!")
            afg_db.session.add(user)
            afg_db.session.commit()

            # Create a test rubric
            rubric = Rubric(title="Test Rubric", description="Test rubric description", created_by=user.id)
            afg_db.session.add(rubric)
            afg_db.session.commit()

            # Create a criterion for the rubric
            criterion = Criterion(rubric_id=rubric.id, name="Test Criterion", description="Test criterion", max_score=10.0)
            afg_db.session.add(criterion)
            afg_db.session.commit()

            # Create a feedback template
            template = FeedbackTemplate(name="Test Template", template_text="This is a test feedback template.", created_by=user.id)
            afg_db.session.add(template)
            afg_db.session.commit()

            # Create a admin user
            admin = User(name="Super Admin", email="admin@example.com", user_type="super-admin")
            admin.set_password("Adminpass1!")
            afg_db.session.add(admin)
            afg_db.session.commit()

            # Create a student user
            student = User(name="Test Student", email="student@example.com", user_type="student")
            student.set_password("Studentpass123!")
            afg_db.session.add(student)
            afg_db.session.commit()

            # Create a test course
            course = Course(title="Test Course", description="Test course description", instructor_id=user.id, status="active")
            afg_db.session.add(course)
            afg_db.session.commit()

            # Create a test assignment
            from datetime import timedelta
            assignment = Assignment(course_id=course.id, title="Test Assignment", description="Test assignment", due_date=datetime.utcnow() + timedelta(days=7), status="active")
            afg_db.session.add(assignment)
            afg_db.session.commit()

            self.user_id = user.id
            self.rubric_id = rubric.id
            self.criterion_id = criterion.id
            self.template_id = template.id
            self.admin_id = admin.id
            self.student_id = student.id
            self.course_id = course.id
            self.assignment_id = assignment.id

            self.access_token = create_access_token(identity=str(self.user_id))
            self.admin_token = create_access_token(identity=str(self.admin_id))

            afg_db.session.expunge_all()

            # Remove references to ORM objects after expunge_all
            del user
            del rubric
            del criterion
            del template
            del admin
            del student
            del course
            del assignment

    def tearDown(self):
        with self.app.app_context():
            afg_db.session.remove()
            afg_db.drop_all()

    def auth_headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}'
        }

    def test_auth_register_and_login(self):
        # Test registration endpoint
        response = self.client.post('/auth/register', json={
            "name": "New User",
            "email": "newuser@example.com",
            "password": "Newpassword1!",
            "user_type": "student"
        })
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn("verification_token", data)
        verification_token = data["verification_token"]

        # Test email verification
        response = self.client.post(f'/auth/verify-email/{verification_token}')
        self.assertEqual(response.status_code, 200)

        # Test login endpoint
        response = self.client.post('/auth/login', json={
            "email": "newuser@example.com",
            "password": "Newpassword1!"
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("access_token", data)

    def test_students_crud(self):
        # Create student
        response = self.client.post('/api/users/', headers={'Authorization': f'Bearer {self.admin_token}'}, json={
            "name": "Student One",
            "email": "student1@example.com",
            "password": "Studentpass1!",
            "user_type": "student"
        })
        self.assertEqual(response.status_code, 201)
        student_id = response.get_json()['id']

        # Get student
        response = self.client.get(f'/api/users/{student_id}', headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)

        # Update student
        response = self.client.put(f'/api/users/{student_id}', headers={'Authorization': f'Bearer {self.admin_token}'}, json={
            "name": "Student One Updated"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['name'], "Student One Updated")

        # Delete student
        response = self.client.delete(f'/api/users/{student_id}', headers={'Authorization': f'Bearer {self.admin_token}'})
        self.assertEqual(response.status_code, 200)

    def test_courses_crud(self):
        # Create course
        response = self.client.post('/api/courses/', headers=self.auth_headers(), json={
            "title": "Test Course",
            "description": "Course description",
            "status": "Active"
        })
        self.assertEqual(response.status_code, 201)
        course_id = response.get_json()['id']

        # Get course
        response = self.client.get(f'/api/courses/{course_id}', headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)

        # Update course
        response = self.client.put(f'/api/courses/{course_id}', headers=self.auth_headers(), json={
            "title": "Updated Course"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['title'], "Updated Course")

        # Delete course
        response = self.client.delete(f'/api/courses/{course_id}', headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)

    # Similar CRUD tests for assignments, submissions, meetings, messages, feedback_templates

    @patch('app.api.feedback.ai_generate_feedback')
    def test_feedback_generation(self, mock_generate_feedback):
        # Mock the AI feedback generation
        mock_generate_feedback.return_value = "Mocked feedback text based on rubric and performance."
        # Test feedback generation endpoint with valid data
        response = self.client.post('/api/feedback', headers=self.auth_headers(), json={
            "student_id": self.student_id,
            "rubric_id": self.rubric_id,
            "performance_data": [
                {
                    "criterion_id": self.criterion_id,
                    "score": 8.5,
                    "remarks": "Good performance"
                }
            ],
            "template_id": self.template_id
        })
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('feedback_text', data['data'])
        self.assertIn('mentor_input_id', data['data'])
        self.assertIn('feedback_id', data['data'])

    def test_protected_route_requires_auth(self):
        # Access protected route without token
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, 401)

    def test_invalid_input_feedback(self):
        # Missing required fields
        response = self.client.post('/api/feedback', headers=self.auth_headers(), json={
            "rubric_id": self.rubric_id
        })
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data['status'], 'error')
        self.assertIn('Missing rubric_id, performance_data or template_id', data['message'])

    def test_assignments_crud(self):
        # Create assignment
        response = self.client.post('/api/assignments/', headers=self.auth_headers(), json={
            "title": "New Assignment",
            "description": "Assignment description",
            "course_id": self.course_id,
            "due_date": "2024-12-31T23:59:59"
        })
        self.assertEqual(response.status_code, 201)
        assignment_id = response.get_json()['id']

        # Get assignment
        response = self.client.get(f'/api/assignments/{assignment_id}', headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)

        # Update assignment
        response = self.client.put(f'/api/assignments/{assignment_id}', headers=self.auth_headers(), json={
            "title": "Updated Assignment"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['title'], "Updated Assignment")

        # Delete assignment
        response = self.client.delete(f'/api/assignments/{assignment_id}', headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)

    def test_submissions_crud(self):
        # Create submission
        response = self.client.post('/api/submissions/', headers=self.auth_headers(), json={
            "assignment_id": self.assignment_id,
            "file_url": "http://example.com/file.pdf"
        })
        self.assertEqual(response.status_code, 201)
        submission_id = response.get_json()['id']

        # Get submission
        response = self.client.get(f'/api/submissions/{submission_id}', headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)

        # Update submission
        response = self.client.put(f'/api/submissions/{submission_id}', headers=self.auth_headers(), json={
            "score": 9.0,
            "feedback": "Great work!"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['score'], 9.0)

        # Delete submission
        response = self.client.delete(f'/api/submissions/{submission_id}', headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)

    def test_feedback_templates_crud(self):
        # Create feedback template
        response = self.client.post('/api/feedback-templates/', headers=self.auth_headers(), json={
            "name": "New Template",
            "template_text": "This is a new feedback template."
        })
        self.assertEqual(response.status_code, 201)
        template_id = response.get_json()['id']

        # Get feedback template
        response = self.client.get(f'/api/feedback-templates/{template_id}', headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)

        # Update feedback template
        response = self.client.put(f'/api/feedback-templates/{template_id}', headers=self.auth_headers(), json={
            "name": "Updated Template"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['name'], "Updated Template")

        # Delete feedback template
        response = self.client.delete(f'/api/feedback-templates/{template_id}', headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)

    def test_users_crud(self):
        # Create user (admin only)
        response = self.client.post('/api/users/', headers={'Authorization': f'Bearer {self.admin_token}'}, json={
            "name": "New User",
            "email": "newuser2@example.com",
            "user_type": "mentor",
            "password": "Newpass1!"
        })
        self.assertEqual(response.status_code, 201)
        user_id = response.get_json()['id']

        # Get users (admin only)
        response = self.client.get('/api/users/', headers={'Authorization': f'Bearer {self.admin_token}'})
        self.assertEqual(response.status_code, 200)

        # Update user (admin only)
        response = self.client.put(f'/api/users/{user_id}', headers={'Authorization': f'Bearer {self.admin_token}'}, json={
            "name": "Updated User"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['name'], "Updated User")

        # Delete user (admin only)
        response = self.client.delete(f'/api/users/{user_id}', headers={'Authorization': f'Bearer {self.admin_token}'})
        self.assertEqual(response.status_code, 200)

    def test_analytics_dashboard(self):
        # Test dashboard analytics
        response = self.client.get('/api/analytics/dashboard', headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('user_info', data)

    def test_feedback_history(self):
        # Test feedback history
        response = self.client.get('/api/feedback/history', headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)

    def test_feedback_analytics(self):
        # Test feedback analytics
        response = self.client.get('/api/feedback/analytics', headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)

    @patch('app.api.feedback.generate_assignment_feedback')
    def test_generate_assignment_feedback(self, mock_generate_feedback):
        # Mock the assignment feedback generation
        mock_generate_feedback.return_value = "Mocked assignment feedback text."
        # Test generate assignment feedback endpoint
        response = self.client.post('/api/feedback/generate-assignment-feedback', headers=self.auth_headers(), json={
            "template_id": self.template_id,
            "assignment_id": self.assignment_id,
            "student_ids": [self.student_id]
        })
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')

    def test_messages_crud(self):
        # Create message
        response = self.client.post('/api/messages/', headers=self.auth_headers(), json={
            "receiver_id": self.student_id,
            "content": "This is a test message."
        })
        self.assertEqual(response.status_code, 201)
        message_id = response.get_json()['id']

        # Get message
        response = self.client.get(f'/api/messages/{message_id}', headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)

        # Delete message
        response = self.client.delete(f'/api/messages/{message_id}', headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
