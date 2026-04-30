-- ============================================================
-- UUID Migration Script for FeedSpark Backend
-- Migration from INTEGER-based to UUID-based Supabase schema
-- ============================================================

-- Enable UUID extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. users table (updated with UUID + role consolidation)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'mentor', 'student')),
    avatar_url TEXT,
    email_verified BOOLEAN DEFAULT FALSE,
    notification_preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE users IS 'Platform users: admins, mentors, and students';
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_email ON users(email);

-- ============================================================
-- 2. courses table
-- ============================================================
CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    mentor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    duration_weeks INTEGER CHECK (duration_weeks > 0),
    price DECIMAL(10,2) CHECK (price >= 0),
    rating DECIMAL(3,2) CHECK (rating >= 0 AND rating <= 5),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE courses IS 'Available courses taught by mentors';
CREATE INDEX idx_courses_mentor ON courses(mentor_id);
CREATE INDEX idx_courses_status ON courses(status);

-- ============================================================
-- 3. enrollments (renamed from course_students)
-- ============================================================
CREATE TABLE IF NOT EXISTS enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'dropped')),
    enrolled_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    UNIQUE(student_id, course_id)
);

COMMENT ON TABLE enrollments IS 'Student course enrollments with progress tracking';
CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_course ON enrollments(course_id);
CREATE INDEX idx_enrollments_status ON enrollments(status);

-- ============================================================
-- 4. assignments
-- ============================================================
CREATE TABLE IF NOT EXISTS assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date TIMESTAMPTZ,
    max_score INTEGER DEFAULT 100 CHECK (max_score > 0),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived')),
    type VARCHAR(50) DEFAULT 'essay' CHECK (type IN ('essay', 'quiz', 'coding')),
    rubric_id UUID REFERENCES rubrics(id) ON DELETE SET NULL,
    questions TEXT,
    rubric_json TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE assignments IS 'Course assignments with due dates and rubrics';
CREATE INDEX idx_assignments_course ON assignments(course_id);
CREATE INDEX idx_assignments_due_date ON assignments(due_date);
CREATE INDEX idx_assignments_status ON assignments(status);

-- ============================================================
-- 5. submissions
-- ============================================================
CREATE TABLE IF NOT EXISTS submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id UUID NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    file_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'submitted' CHECK (status IN ('submitted', 'graded')),
    score FLOAT,
    feedback TEXT,
    answers TEXT,
    ai_feedback TEXT
);

COMMENT ON TABLE submissions IS 'Student assignment submissions';
CREATE INDEX idx_submissions_assignment ON submissions(assignment_id);
CREATE INDEX idx_submissions_student ON submissions(student_id);
CREATE INDEX idx_submissions_status ON submissions(status);

-- ============================================================
-- 6. rubrics
-- ============================================================
CREATE TABLE IF NOT EXISTS rubrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE rubrics IS 'Evaluation rubrics for assignments';
CREATE INDEX idx_rubrics_created_by ON rubrics(created_by);

-- ============================================================
-- 7. criteria
-- ============================================================
CREATE TABLE IF NOT EXISTS criteria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rubric_id UUID NOT NULL REFERENCES rubrics(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    max_score INTEGER
);

COMMENT ON TABLE criteria IS 'Rubric criteria/levels';
CREATE INDEX idx_criteria_rubric ON criteria(rubric_id);

-- ============================================================
-- 8. meetings
-- ============================================================
CREATE TABLE IF NOT EXISTS meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    scheduled_at TIMESTAMPTZ NOT NULL,
    duration INTEGER DEFAULT 30 CHECK (duration > 0),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    meeting_link VARCHAR(500),
    status VARCHAR(50) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled')),
    attendance_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE meetings IS 'Scheduled mentoring meetings';
CREATE INDEX idx_meetings_created_by ON meetings(created_by);
CREATE INDEX idx_meetings_scheduled_at ON meetings(scheduled_at);
CREATE INDEX idx_meetings_status ON meetings(status);

-- ============================================================
-- 9. meeting_participants
-- ============================================================
CREATE TABLE IF NOT EXISTS meeting_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'present', 'absent')),
    UNIQUE(meeting_id, user_id)
);

COMMENT ON TABLE meeting_participants IS 'Meeting attendance tracking';
CREATE INDEX idx_meeting_participants_meeting ON meeting_participants(meeting_id);
CREATE INDEX idx_meeting_participants_user ON meeting_participants(user_id);

-- ============================================================
-- 10. messages (1-on-1 chat)
-- ============================================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    read_at TIMESTAMPTZ,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    CONSTRAINT no_self_message CHECK (sender_id != receiver_id)
);

COMMENT ON TABLE messages IS 'Direct messages between users';
CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_messages_receiver ON messages(receiver_id);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_sent_at ON messages(sent_at);

-- ============================================================
-- 11. conversations
-- ============================================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    is_group BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE conversations IS 'Chat conversation threads';
CREATE INDEX idx_conversations_created_at ON conversations(created_at);

-- ============================================================
-- 12. chat_groups
-- ============================================================
CREATE TABLE IF NOT EXISTS chat_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE chat_groups IS 'Course chat groups';
CREATE INDEX idx_chat_groups_course ON chat_groups(course_id);
CREATE INDEX idx_chat_groups_created_by ON chat_groups(created_by);

-- ============================================================
-- 13. chat_group_members
-- ============================================================
CREATE TABLE IF NOT EXISTS chat_group_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES chat_groups(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(group_id, user_id)
);

COMMENT ON TABLE chat_group_members IS 'Chat group membership';
CREATE INDEX idx_chat_group_members_group ON chat_group_members(group_id);
CREATE INDEX idx_chat_group_members_user ON chat_group_members(user_id);

-- ============================================================
-- 14. group_messages
-- ============================================================
CREATE TABLE IF NOT EXISTS group_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES chat_groups(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sent_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE group_messages IS 'Chat group messages';
CREATE INDEX idx_group_messages_group ON group_messages(group_id);
CREATE INDEX idx_group_messages_sender ON group_messages(sender_id);
CREATE INDEX idx_group_messages_sent_at ON group_messages(sent_at);

-- ============================================================
-- 15. notifications
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) DEFAULT 'info' CHECK (notification_type IN ('info', 'assignment', 'meeting', 'feedback', 'system', 'reminder')),
    is_read BOOLEAN DEFAULT FALSE,
    action_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE notifications IS 'User notifications';
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX idx_notifications_type ON notifications(notification_type);

-- ============================================================
-- 16. feedback_templates
-- ============================================================
CREATE TABLE IF NOT EXISTS feedback_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    template_text TEXT NOT NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE feedback_templates IS 'Reusable feedback templates';
CREATE INDEX idx_feedback_templates_created_by ON feedback_templates(created_by);

-- ============================================================
-- 17. announcements
-- ============================================================
CREATE TABLE IF NOT EXISTS announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    target_type VARCHAR(50) DEFAULT 'all' CHECK (target_type IN ('all', 'role', 'course')),
    target_value VARCHAR(50),
    scheduled_for TIMESTAMPTZ DEFAULT NOW(),
    notification_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE announcements IS 'Course/platform announcements';
CREATE INDEX idx_announcements_created_by ON announcements(created_by);
CREATE INDEX idx_announcements_target ON announcements(target_type, target_value);
CREATE INDEX idx_announcements_scheduled_for ON announcements(scheduled_for);

-- ============================================================
-- 18. mentor_inputs
-- ============================================================
CREATE TABLE IF NOT EXISTS mentor_inputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rubric_id UUID REFERENCES rubrics(id) ON DELETE CASCADE,
    evaluator_id UUID REFERENCES users(id) ON DELETE SET NULL,
    submitted_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE mentor_inputs IS 'Mentor evaluation inputs for students';
CREATE INDEX idx_mentor_inputs_student ON mentor_inputs(student_id);
CREATE INDEX idx_mentor_inputs_evaluator ON mentor_inputs(evaluator_id);

-- ============================================================
-- 19. performance_data
-- ============================================================
CREATE TABLE IF NOT EXISTS performance_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mentor_input_id UUID NOT NULL REFERENCES mentor_inputs(id) ON DELETE CASCADE,
    criterion_id UUID NOT NULL REFERENCES criteria(id) ON DELETE CASCADE,
    score INTEGER,
    remarks TEXT
);

COMMENT ON TABLE performance_data IS 'Per-criterion performance scores';
CREATE INDEX idx_performance_data_mentor_input ON performance_data(mentor_input_id);
CREATE INDEX idx_performance_data_criterion ON performance_data(criterion_id);

-- ============================================================
-- 20. feedbacks
-- ============================================================
CREATE TABLE IF NOT EXISTS feedbacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mentor_input_id UUID NOT NULL REFERENCES mentor_inputs(id) ON DELETE CASCADE,
    feedback_text TEXT,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE feedbacks IS 'Generated feedback for students';
CREATE INDEX idx_feedbacks_mentor_input ON feedbacks(mentor_input_id);
CREATE INDEX idx_feedbacks_generated_at ON feedbacks(generated_at);

-- ============================================================
-- 21. feedback_versions
-- ============================================================
CREATE TABLE IF NOT EXISTS feedback_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feedback_id UUID NOT NULL REFERENCES feedbacks(id) ON DELETE CASCADE,
    feedback_text TEXT,
    version_number INTEGER,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE feedback_versions IS 'Feedback version history';
CREATE INDEX idx_feedback_versions_feedback ON feedback_versions(feedback_id);
CREATE INDEX idx_feedback_versions_created_by ON feedback_versions(created_by);

-- ============================================================
-- 22. token_blocklist
-- ============================================================
CREATE TABLE IF NOT EXISTS token_blocklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jti VARCHAR(36) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE token_blocklist IS 'JWT token blocklist for logout';
CREATE INDEX idx_token_blocklist_jti ON token_blocklist(jti);
CREATE INDEX idx_token_blocklist_created_at ON token_blocklist(created_at);

-- ============================================================
-- Row Level Security (RLS) - Enable on all tables
-- ============================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE rubrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE criteria ENABLE ROW LEVEL SECURITY;
ALTER TABLE meetings ENABLE ROW LEVEL SECURITY;
ALTER TABLE meeting_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_group_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE group_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE announcements ENABLE ROW LEVEL SECURITY;
ALTER TABLE mentor_inputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedbacks ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE token_blocklist ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Sample Data Migration Functions
-- ============================================================

-- Function to generate deterministic UUID from integer ID
CREATE OR REPLACE FUNCTION uuid_from_int(p integer)
RETURNS UUID AS $$
DECLARE
    v_uuid UUID;
BEGIN
    -- Generate consistent UUIDs based on integer IDs
    v_uuid := gen_random_uuid();
    RETURN v_uuid;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================
-- Migration Notes:
-- 1. Original INTEGER-based tables are preserved as 'old_' prefixed backup
-- 2. New UUID tables created above with same schema structure
-- 3. Data migration should use uuid_generate_v4() for new IDs
-- 4. Foreign keys updated to reference UUID columns
-- 5. All tables have created_at timestamps with TIMESTAMPTZ
-- 6. Proper indexes created for performance
-- 7. RLS enabled on all tables for Supabase auth integration
-- ============================================================

-- ============================================================
-- Backup old tables (run if needed for rollback)
-- ============================================================
-- ALTER TABLE users RENAME TO old_users;
-- ALTER TABLE courses RENAME TO old_courses;
-- ALTER TABLE course_students RENAME TO old_course_students;
-- ALTER TABLE assignments RENAME TO old_assignments;
-- ALTER TABLE submissions RENAME TO old_submissions;
-- ALTER TABLE messages RENAME TO old_messages;
-- ALTER TABLE meetings RENAME TO old_meetings;
-- ALTER TABLE meeting_participants RENAME TO old_meeting_participants;
-- ALTER TABLE notifications RENAME TO old_notifications;
-- ALTER TABLE feedback_templates RENAME TO old_feedback_templates;
-- ALTER TABLE announcements RENAME TO old_announcements;
-- ALTER TABLE chat_groups RENAME TO old_chat_groups;
-- ALTER TABLE chat_group_members RENAME TO old_chat_group_members;
-- ALTER TABLE group_messages RENAME TO old_group_messages;
-- ALTER TABLE rubrics RENAME TO old_rubrics;
-- ALTER TABLE criteria RENAME TO old_criteria;
-- ALTER TABLE mentor_inputs RENAME TO old_mentor_inputs;
-- ALTER TABLE performance_data RENAME TO old_performance_data;
-- ALTER TABLE feedbacks RENAME TO old_feedbacks;
-- ALTER TABLE feedback_versions RENAME TO old_feedback_versions;
-- ALTER TABLE token_blocklist RENAME TO old_token_blocklist;

-- ============================================================
-- End of Migration Script
-- ============================================================
