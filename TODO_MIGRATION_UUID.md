# UUID Migration Plan for Supabase Schema Integration

## Overview
Migrate all Python ORM models from INTEGER-based IDs to UUID-based IDs to match SUPABASE_SCHEMA.sql.

## Model Files Updated (11 files)

### Phase 1: Core Models ✅
- [x] 1. app/models/user.py - User model (add avatar_url, rename user_type to role, password to password_hash)
- [x] 2. app/models/course.py - Course model (instructor_id to mentor_id, add enrollment table)

### Phase 2: Related Models ✅
- [x] 3. app/models/announcement.py
- [x] 4. app/models/chat_group.py
- [x] 5. app/models/feedback.py
- [x] 6. app/models/feedback_template.py
- [x] 7. app/models/meeting.py
- [x] 8. app/models/message.py
- [x] 9. app/models/notification.py
- [x] 10. app/models/rubric.py
- [x] 11. app/models/token_blocklist.py

### Phase 3: API Files to Update ✅
- [x] app/api/courses.py - Update route handlers to accept UUID strings
- [x] app/api/assignments.py
- [x] app/api/submissions.py
- [x] app/api/users.py
- [x] app/api/announcements.py
- [x] app/api/meetings.py
- [x] app/api/admin.py
- [x] app/api/analytics.py
- [x] app/api/chat_groups.py
- [x] app/api/feedback.py
- [x] app/api/feedback_templates.py
- [x] app/api/mentor.py
- [x] app/api/messages.py
- [x] app/api/students.py

## Field Mappings (Python -> Supabase)

| Table | Integer Field | UUID Field |
|------|-------------|------------|
| users | id (Integer) | id (UUID) |
| users | user_type | role |
| users | password | password_hash |
| courses | id (Integer) | id (UUID) |
| courses | instructor_id | mentor_id |
| enrollments | id (Integer), student_id (Integer), course_id (Integer) | id (UUID), student_id (UUID), course_id (UUID) |
| assignments | id (Integer), course_id (Integer) | id (UUID), course_id (UUID) |
| submissions | id (Integer), assignment_id (Integer), student_id (Integer) | id (UUID), assignment_id (UUID), student_id (UUID) |
| rubrics | id (Integer), created_by (Integer) | id (UUID), created_by (UUID) |
| criteria | id (Integer), rubric_id (Integer) | id (UUID), rubric_id (UUID) |
| meetings | id (Integer), created_by (Integer) | id (UUID), created_by (UUID) |
| meeting_participants | id (Integer), meeting_id (Integer), user_id (Integer) | id (UUID), meeting_id (UUID), user_id (UUID) |
| messages | id (Integer), sender_id (Integer), receiver_id (Integer) | id (UUID), sender_id (UUID), receiver_id (UUID) |
| conversations | id (Integer) | id (UUID) |
| chat_groups | id (Integer), course_id (Integer), created_by (Integer) | id (UUID), course_id (UUID), created_by (UUID) |
| chat_group_members | id (Integer), group_id (Integer), user_id (Integer) | id (UUID), group_id (UUID), user_id (UUID) |
| group_messages | id (Integer), group_id (Integer), sender_id (Integer) | id (UUID), group_id (UUID), sender_id (UUID) |
| notifications | id (Integer), user_id (Integer) | id (UUID), user_id (UUID) |
| feedback_templates | id (Integer), created_by (Integer) | id (UUID), created_by (UUID) |
| announcements | id (Integer), created_by (Integer) | id (UUID), created_by (UUID) |
| mentor_inputs | id (Integer), student_id (Integer), rubric_id (Integer), evaluator_id (Integer) | id (UUID), student_id (UUID), rubric_id (UUID), evaluator_id (UUID) |
| performance_data | id (Integer), mentor_input_id (Integer), criterion_id (Integer) | id (UUID), mentor_input_id (UUID), criterion_id (UUID) |
| feedbacks | id (Integer), mentor_input_id (Integer) | id (UUID), mentor_input_id (UUID) |
| feedback_versions | id (Integer), feedback_id (Integer), created_by (Integer) | id (UUID), feedback_id (UUID), created_by (UUID) |
| token_blocklist | id (Integer) | id (UUID) |

## Implementation Notes

1. Use SQLAlchemy's Uuid column type (available in SQLAlchemy 1.4+)
2. Set default to gen_random_uuid() via server_default
3. Foreign key references must use UUID columns
4. Update all API route handlers to accept UUID strings
5. Test with Supabase connection after migration

## Migration Completed ✅

All phases of the UUID migration have been successfully completed:

- **Phase 1**: All model files updated with UUID primary keys and field name changes
- **Phase 2**: All related models updated to use UUID foreign keys
- **Phase 3**: All API files updated to handle UUID routes, role field, mentor_id field, and return string IDs

The API is now fully compatible with the Supabase schema using UUID-based IDs.
