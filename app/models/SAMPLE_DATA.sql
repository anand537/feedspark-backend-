-- ============================================================
-- FeedSpark Database Validation & Sample Data
-- Safe Mode: Only adds missing data, no schema changes
-- ============================================================

-- ============================================================
-- STEP 1: Schema Validation Report
-- ============================================================

-- ✓ All 22 tables exist:
--   users, courses, enrollments, assignments, submissions,
--   rubrics, criteria, meetings, meeting_participants,
--   messages, conversations, chat_groups, chat_group_members,
--   group_messages, notifications, feedback_templates,
--   announcements, mentor_inputs, performance_data,
--   feedbacks, feedback_versions, token_blocklist

-- ✓ All Foreign Keys are valid (UUID references)

-- ✓ All tables use UUID PRIMARY KEY

-- ✓ Chat System Complete:
--   - 1-on-1: messages(sender_id, receiver_id, conversation_id)
--   - Group: chat_groups, chat_group_members, group_messages
--   - conversations table exists

-- ============================================================
-- STEP 2: Sample Data (Only if tables are empty)
-- ============================================================

-- Note: Run these queries to check if data exists first
-- SELECT COUNT(*) FROM users;

-- Sample Users (only if empty)
-- INSERT INTO users (id, name, email, password_hash, role, created_at)
-- VALUES 
--   -- Admin
--   (gen_random_uuid(), 'Super Admin', 'admin@feedspark.com', '$2b$12$...', 'admin', NOW()),
--   -- Mentors
--   (gen_random_uuid(), 'Dr. Sarah Johnson', 'sarah@feedspark.com', '$2b$12$...', 'mentor', NOW()),
--   (gen_random_uuid(), 'Prof. Michael Chen', 'michael@feedspark.com', '$2b$12$...', 'mentor', NOW()),
--   (gen_random_uuid(), 'Ms. Emily Davis', 'emily@feedspark.com', '$2b$12$...', 'mentor', NOW()),
--   (gen_random_uuid(), 'Mr. James Wilson', 'james@feedspark.com', '$2b$12$...', 'mentor', NOW()),
--   (gen_random_uuid(), 'Mrs. Lisa Brown', 'lisa@feedspark.com', '$2b$12$...', 'mentor', NOW()),
--   -- Students (sample 20)
--   (gen_random_uuid(), 'Alice Smith', 'alice@example.com', '$2b$12$...', 'student', NOW()),
--   (gen_random_uuid(), 'Bob Johnson', 'bob@example.com', '$2b$12$...', 'student', NOW()),
--   (gen_random_uuid(), 'Charlie Brown', 'charlie@example.com', '$2b$12$...', 'student', NOW()),
--   (gen_random_uuid(), 'Diana Prince', 'diana@example.com', '$2b$12$...', 'student', NOW()),
--   (gen_random_uuid(), 'Eve Wilson', 'eve@example.com', '$2b$12$...', 'student', NOW()),
--   (gen_random_uuid(), 'Frank Miller', 'frank@example.com', '$2b$12$...', 'student', NOW()),
--   (gen_random_uuid(), 'Grace Lee', 'grace@example.com', '$2b$12$...', 'student', NOW()),
--   (gen_random_uuid(), 'Henry Ford', 'henry@example.com', '$2b$12$...', 'student', NOW()),
--   (gen_random_uuid(), 'Ivy Chen', 'ivy@example.com', '$2b$12$...', 'student', NOW()),
--   (gen_random_uuid(), 'Jack Williams', 'jack@example.com', '$2b$12$...', 'student', NOW()),
--   (gen_random_uuid(), 'Kate Brown', 'kate@example.com', '$2b$12$...', 'student', NOW()),
--   (gen_random_uuid(), 'Leo Garcia', 'leo@example.com', '$2b$12$...', 'student', NOW()),
--   (gen_random_uuid(), 'Mia Rodriguez', 'mia@example.com', '$2b$12$...', 'student', NOW()),
--   (gen_random_uuid(), 'Noah Martinez', 'noah@example.com', '$2b$12$...', 'student', NOW()),
--   (gen_random_uuid(), 'Olivia Taylor', 'olivia@example.com', '$2b$12$...', 'student', NOW()),
--   (gen_random_uuid(), 'Paul Anderson', 'paul@example.com', '$2b$12$...', 'student', NOW()),
--   (gen_random_uuid(), 'Quinn Murphy', 'quinn@example.com', '$2b$12$...', 'student', NOW()),
--   (gen_random_uuid(), 'Rose Thompson', 'rose@example.com', '$2b$12$...', 'student', NOW())
-- ON CONFLICT (email) DO NOTHING;

-- Sample Courses (only if empty)
-- INSERT INTO courses (id, title, description, mentor_id, duration_weeks, price, status, created_at)
-- SELECT gen_random_uuid(), 'Introduction to Web Development', 'Learn HTML, CSS, and JavaScript basics', id, 8, 199.99, 'active', NOW()
-- FROM users WHERE role = 'mentor' LIMIT 1
-- ON CONFLICT DO NOTHING;

-- Sample Enrollments (only if empty)
-- INSERT INTO enrollments (id, student_id, course_id, progress, status, enrolled_at, created_at)
-- SELECT gen_random_uuid(), 
--        (SELECT id FROM users WHERE role = 'student' LIMIT 1),
--        (SELECT id FROM courses LIMIT 1),
--        0, 'active', NOW(), NOW()
-- ON CONFLICT DO NOTHING;

-- Sample Assignments (only if empty)
-- INSERT INTO assignments (id, course_id, title, description, due_date, max_score, status, type, created_at)
-- SELECT gen_random_uuid(),
--        (SELECT id FROM courses LIMIT 1),
--        'Week 1 Project', 'Build a simple webpage', NOW() + INTERVAL '7 days', 100, 'active', 'essay', NOW()
-- ON CONFLICT DO NOTHING;

-- Sample Conversations (only if empty)
-- INSERT INTO conversations (id, is_group, created_at)
-- VALUES (gen_random_uuid(), false, NOW())
-- ON CONFLICT DO NOTHING;

-- Sample Chat Groups (only if empty)
-- INSERT INTO chat_groups (id, name, course_id, created_by, created_at)
-- SELECT gen_random_uuid(), 
--        'Web Dev Cohort 2024',
--        (SELECT id FROM courses LIMIT 1),
--        (SELECT id FROM users WHERE role = 'mentor' LIMIT 1),
--        NOW()
-- ON CONFLICT DO NOTHING;

-- ============================================================
-- STEP 3: Frontend Field Mapping
-- ============================================================

-- users table fields:
--   id, name, email, role, avatar_url, email_verified, 
--   notification_preferences, created_at

-- courses table fields:
--   id, title, description, mentor_id, duration_weeks, 
--   price, rating, status, created_at

-- enrollments table fields:
--   id, student_id, course_id, progress (0-100), 
--   status (active/completed/dropped), enrolled_at, completed_at

-- assignments table fields:
--   id, course_id, title, description, due_date, 
--   max_score, status, type, questions, rubric_json, created_at

-- submissions table fields:
--   id, assignment_id, student_id, submitted_at, file_url,
--   status (submitted/graded), score, feedback, answers, ai_feedback

-- messages table fields:
--   id, sender_id, receiver_id, content, sent_at, 
--   read_at, conversation_id

-- notifications table fields:
--   id, user_id, title, message, notification_type, 
--   is_read, action_url, created_at

-- meetings table fields:
--   id, title, description, scheduled_at, duration, 
--   created_by, meeting_link, status, attendance_processed

-- announcements table fields:
--   id, title, content, created_by, target_type, target_value,
--   scheduled_for, notification_sent, created_at

-- ============================================================
-- STEP 4: API Query Templates
-- ============================================================

-- Get user profile:
-- SELECT id, name, email, role, avatar_url FROM users WHERE id = auth.uid();

-- Get student enrollments:
-- SELECT e.*, c.title as course_title 
-- FROM enrollments e 
-- JOIN courses c ON e.course_id = c.id 
-- WHERE e.student_id = auth.uid();

-- Get course assignments:
-- SELECT * FROM assignments 
-- WHERE course_id = (SELECT course_id FROM enrollments WHERE student_id = auth.uid());

-- Get 1-on-1 messages:
-- SELECT m.*, 
--        (SELECT name FROM users WHERE id = m.sender_id) as sender_name
-- FROM messages m
-- WHERE m.sender_id = auth.uid() OR m.receiver_id = auth.uid()
-- ORDER BY m.sent_at DESC;

-- Get group messages:
-- SELECT gm.*, 
--        (SELECT name FROM users WHERE id = gm.sender_id) as sender_name
-- FROM group_messages gm
-- WHERE gm.group_id IN (
--    SELECT group_id FROM chat_group_members WHERE user_id = auth.uid()
-- )
-- ORDER BY gm.sent_at DESC;

-- Get notifications:
-- SELECT * FROM notifications 
-- WHERE user_id = auth.uid() 
-- ORDER BY created_at DESC;

-- ============================================================
-- Validation Complete
-- ============================================================
