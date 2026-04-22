# TODO: Change 'admin' to 'super-admin' throughout the project

## Tasks
- [x] Update app/models/AFG_SCHEMA.sql: Change CHECK constraint to ('student', 'mentor', 'super-admin')
- [x] Update app/routes/auth.py: Replace 'admin' in user_type validation
- [x] Update app/api/users.py: Replace 'admin' in role checks, validations, and decorators
- [x] Update app/api/analytics.py: Replace 'admin' in user_type checks and analytics functions
- [x] Update app/api/assignments.py: Replace 'admin' in access control checks
- [x] Update app/api/courses.py: Replace 'admin' in access control checks
- [x] Update app/api/feedback_templates.py: Replace 'admin' in access control checks
- [x] Update app/api/submissions.py: Replace 'admin' in access control checks
- [x] Update app/api/meetings.py: Replace 'admin' in access control checks
- [x] Update app/api/feedback.py: Replace 'admin' in access control checks
- [x] Update app/api/chat_groups.py: Replace 'admin' in access control checks
- [x] Update app/api/announcements.py: Replace 'admin' in access control checks
- [x] Update tests/test_api_endpoints.py: Replace 'admin' in test data and assertions
- [x] Verify: Search for remaining 'admin' in user_type contexts
- [x] Run tests to ensure no breakage
