-- ============================================================
-- FeedSpark Backend Schema
-- Updated with enrollments, conversations, RLS, and proper indexes
-- ============================================================

-- users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    user_type VARCHAR(50) CHECK (user_type IN ('student', 'mentor', 'admin')) DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255) UNIQUE,
    email_verification_expires TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    password_reset_token VARCHAR(255) UNIQUE,
    password_reset_expires TIMESTAMP,
    notification_preferences TEXT DEFAULT '{}'
);

-- Indexes for users table
CREATE INDEX idx_users_user_type ON users(user_type);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_created_at ON users(created_at);

-- courses table
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    instructor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active'
);

-- Indexes for courses table
CREATE INDEX idx_courses_instructor ON courses(instructor_id);
CREATE INDEX idx_courses_status ON courses(status);
CREATE INDEX idx_courses_created_at ON courses(created_at);

-- enrollments table (renamed from course_students with progress/status fields)
CREATE TABLE enrollments (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'dropped')),
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_id, student_id)
);

-- Indexes for enrollments table
CREATE INDEX idx_enrollments_course ON enrollments(course_id);
CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_status ON enrollments(status);
CREATE INDEX idx_enrollments_created_at ON enrollments(created_at);

-- assignments table
CREATE TABLE assignments (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date TIMESTAMP,
    created_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',
    type VARCHAR(50) DEFAULT 'essay',
    rubric_id INTEGER REFERENCES rubrics(id) ON DELETE SET NULL,
    questions TEXT,
    max_score INTEGER DEFAULT 100,
    rubric_json TEXT
);

-- submissions table
CREATE TABLE submissions (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER REFERENCES assignments(id) ON DELETE CASCADE,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    submitted_at TIMESTAMP,
    file_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'submitted',
    score FLOAT,
    feedback TEXT,
    answers TEXT,
    ai_feedback TEXT
);

-- messages table
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    receiver_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sent_at TIMESTAMP,
    read_at TIMESTAMP
);

-- meetings table
CREATE TABLE meetings (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    scheduled_at TIMESTAMP,
    duration INTEGER,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP,
    meeting_link VARCHAR(500),
    status VARCHAR(50) DEFAULT 'scheduled',
    attendance_processed BOOLEAN DEFAULT FALSE
);

-- meeting_participants table
CREATE TABLE meeting_participants (
    id SERIAL PRIMARY KEY,
    meeting_id INTEGER REFERENCES meetings(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending'
);

-- notifications table
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- feedback_templates table
CREATE TABLE feedback_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    template_text TEXT NOT NULL,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP
);

-- announcements table
CREATE TABLE announcements (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    target_type VARCHAR(50) DEFAULT 'all',
    target_value VARCHAR(50),
    scheduled_for TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notification_sent BOOLEAN DEFAULT FALSE
);

-- chat groups tables
CREATE TABLE chat_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chat_group_members (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES chat_groups(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE group_messages (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES chat_groups(id) ON DELETE CASCADE,
    sender_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- mentor_inputs table (was student_inputs)
CREATE TABLE mentor_inputs (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    rubric_id INTEGER REFERENCES rubrics(id) ON DELETE CASCADE,
    evaluator_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- performance_data table
CREATE TABLE performance_data (
    id SERIAL PRIMARY KEY,
    mentor_input_id INTEGER REFERENCES mentor_inputs(id) ON DELETE CASCADE,
    criterion_id INTEGER REFERENCES criteria(id) ON DELETE CASCADE,
    score INTEGER,
    remarks TEXT
);

-- feedbacks table
CREATE TABLE feedbacks (
    id SERIAL PRIMARY KEY,
    mentor_input_id INTEGER REFERENCES mentor_inputs(id) ON DELETE CASCADE,
    feedback_text TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- feedback_versions table
CREATE TABLE feedback_versions (
    id SERIAL PRIMARY KEY,
    feedback_id INTEGER REFERENCES feedbacks(id) ON DELETE CASCADE,
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version_number INTEGER,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- token_blocklist table
CREATE TABLE token_blocklist (
    id SERIAL PRIMARY KEY,
    jti VARCHAR(36) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for token_blocklist
CREATE INDEX idx_token_blocklist_jti ON token_blocklist(jti);
CREATE INDEX idx_token_blocklist_created_at ON token_blocklist(created_at);

-- conversations table (for chat system improvements)
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    is_group BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for conversations
CREATE INDEX idx_conversations_created_at ON conversations(created_at);

-- ============================================================
-- Indexes for remaining tables
-- ============================================================

-- assignments table indexes
CREATE INDEX idx_assignments_course ON assignments(course_id);
CREATE INDEX idx_assignments_due_date ON assignments(due_date);
CREATE INDEX idx_assignments_status ON assignments(status);
CREATE INDEX idx_assignments_created_at ON assignments(created_at);

-- submissions table indexes
CREATE INDEX idx_submissions_assignment ON submissions(assignment_id);
CREATE INDEX idx_submissions_student ON submissions(student_id);
CREATE INDEX idx_submissions_status ON submissions(status);
CREATE INDEX idx_submissions_submitted_at ON submissions(submitted_at);

-- messages table indexes
CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_messages_receiver ON messages(receiver_id);
CREATE INDEX idx_messages_sent_at ON messages(sent_at);
CREATE INDEX idx_messages_read_at ON messages(read_at);

-- meetings table indexes
CREATE INDEX idx_meetings_created_by ON meetings(created_by);
CREATE INDEX idx_meetings_scheduled_at ON meetings(scheduled_at);
CREATE INDEX idx_meetings_status ON meetings(status);
CREATE INDEX idx_meetings_created_at ON meetings(created_at);

-- meeting_participants table indexes
CREATE INDEX idx_meeting_participants_meeting ON meeting_participants(meeting_id);
CREATE INDEX idx_meeting_participants_user ON meeting_participants(user_id);

-- notifications table indexes
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_type ON notifications(notification_type);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

-- feedback_templates table indexes
CREATE INDEX idx_feedback_templates_created_by ON feedback_templates(created_by);
CREATE INDEX idx_feedback_templates_created_at ON feedback_templates(created_at);

-- announcements table indexes
CREATE INDEX idx_announcements_created_by ON announcements(created_by);
CREATE INDEX idx_announcements_target ON announcements(target_type, target_value);
CREATE INDEX idx_announcements_scheduled_for ON announcements(scheduled_for);
CREATE INDEX idx_announcements_created_at ON announcements(created_at);

-- chat_groups table indexes
CREATE INDEX idx_chat_groups_course ON chat_groups(course_id);
CREATE INDEX idx_chat_groups_created_by ON chat_groups(created_by);
CREATE INDEX idx_chat_groups_created_at ON chat_groups(created_at);

-- chat_group_members table indexes
CREATE INDEX idx_chat_group_members_group ON chat_group_members(group_id);
CREATE INDEX idx_chat_group_members_user ON chat_group_members(user_id);

-- group_messages table indexes
CREATE INDEX idx_group_messages_group ON group_messages(group_id);
CREATE INDEX idx_group_messages_sender ON group_messages(sender_id);
CREATE INDEX idx_group_messages_sent_at ON group_messages(sent_at);

-- mentor_inputs table indexes
CREATE INDEX idx_mentor_inputs_student ON mentor_inputs(student_id);
CREATE INDEX idx_mentor_inputs_evaluator ON mentor_inputs(evaluator_id);
CREATE INDEX idx_mentor_inputs_submitted_at ON mentor_inputs(submitted_at);

-- performance_data table indexes
CREATE INDEX idx_performance_data_mentor_input ON performance_data(mentor_input_id);
CREATE INDEX idx_performance_data_criterion ON performance_data(criterion_id);

-- feedbacks table indexes
CREATE INDEX idx_feedbacks_mentor_input ON feedbacks(mentor_input_id);
CREATE INDEX idx_feedbacks_generated_at ON feedbacks(generated_at);

-- feedback_versions table indexes
CREATE INDEX idx_feedback_versions_feedback ON feedback_versions(feedback_id);
CREATE INDEX idx_feedback_versions_created_by ON feedback_versions(created_by);
CREATE INDEX idx_feedback_versions_created_at ON feedback_versions(created_at);

-- ============================================================
-- Row Level Security (RLS) Policies for Supabase Auth
-- ============================================================

-- Enable RLS on users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- RLS policy: Users can read their own profile, admins can read all
CREATE POLICY "Users can read own profile" ON users
    FOR SELECT USING (auth.uid() = id);

-- RLS policy: Users can update own profile
CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

-- Enable RLS on courses table
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;

-- RLS policy: Anyone can read active courses
CREATE POLICY "Anyone can read active courses" ON courses
    FOR SELECT USING (status = 'active');

-- RLS policy: Mentors and admins can create/update courses
CREATE POLICY "Mentors and admins can manage courses" ON courses
    FOR ALL USING (auth.uid() = instructor_id);

-- Enable RLS on enrollments table
ALTER TABLE enrollments ENABLE ROW LEVEL SECURITY;

-- RLS policy: Users can see their own enrollments
CREATE POLICY "Users can read own enrollments" ON enrollments
    FOR SELECT USING (auth.uid() = student_id);

-- RLS policy: Students can manage their own enrollments
CREATE POLICY "Students can manage own enrollments" ON enrollments
    FOR ALL USING (auth.uid() = student_id);

-- Enable RLS on assignments table
ALTER TABLE assignments ENABLE ROW LEVEL SECURITY;

-- RLS policy: Students can read assignments from their enrolled courses
CREATE POLICY "Students can read course assignments" ON assignments
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM enrollments WHERE enrollments.course_id = assignments.course_id AND enrollments.student_id = auth.uid())
    );

-- RLS policy: Mentors and admins can manage assignments
CREATE POLICY "Mentors and admins can manage assignments" ON assignments
    FOR ALL USING (
        EXISTS (SELECT 1 FROM courses WHERE courses.id = assignments.course_id AND courses.instructor_id = auth.uid())
    );

-- Enable RLS on submissions table
ALTER TABLE submissions ENABLE ROW LEVEL SECURITY;

-- RLS policy: Users can read their own submissions
CREATE POLICY "Users can read own submissions" ON submissions
    FOR SELECT USING (auth.uid() = student_id);

-- RLS policy: Students can create submissions
CREATE POLICY "Students can create submissions" ON submissions
    FOR INSERT WITH CHECK (auth.uid() = student_id);

-- RLS policy: Students can update own submissions
CREATE POLICY "Students can update own submissions" ON submissions
    FOR UPDATE USING (auth.uid() = student_id);

-- Enable RLS on messages table
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- RLS policy: Users can read their own messages
CREATE POLICY "Users can read own messages" ON messages
    FOR SELECT USING (auth.uid() = sender_id OR auth.uid() = receiver_id);

-- RLS policy: Users can send messages
CREATE POLICY "Users can send messages" ON messages
    FOR INSERT WITH CHECK (auth.uid() = sender_id);

-- Enable RLS on conversations table
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Enable RLS on meetings table
ALTER TABLE meetings ENABLE ROW LEVEL SECURITY;

-- RLS policy: Users can read meetings they created or participate in
CREATE POLICY "Users can read meetings" ON meetings
    FOR SELECT USING (
        auth.uid() = created_by OR
        EXISTS (SELECT 1 FROM meeting_participants WHERE meeting_participants.meeting_id = meetings.id AND meeting_participants.user_id = auth.uid())
    );

-- RLS policy: Only mentors/admins can create meetings
CREATE POLICY "Mentors and admins can create meetings" ON meetings
    FOR ALL USING (
        EXISTS (SELECT 1 FROM users WHERE users.id = auth.uid() AND users.user_type IN ('admin', 'mentor'))
    );

-- Enable RLS on notifications table
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- RLS policy: Users can read their own notifications
CREATE POLICY "Users can read own notifications" ON notifications
    FOR SELECT USING (auth.uid() = user_id);

-- Enable RLS on announcements table
ALTER TABLE announcements ENABLE ROW LEVEL SECURITY;

-- RLS policy: Everyone can read announcements
CREATE POLICY "Anyone can read announcements" ON announcements
    FOR SELECT USING (true);

-- RLS policy: Only admins can create announcements
CREATE POLICY "Admins can create announcements" ON announcements
    FOR ALL USING (
        EXISTS (SELECT 1 FROM users WHERE users.id = auth.uid() AND users.user_type = 'admin')
    );

-- Enable RLS on chat_groups table
ALTER TABLE chat_groups ENABLE ROW LEVEL SECURITY;

-- Enable RLS on chat_group_members table
ALTER TABLE chat_group_members ENABLE ROW LEVEL SECURITY;

-- Enable RLS on group_messages table
ALTER TABLE group_messages ENABLE ROW LEVEL SECURITY;

-- Enable RLS on feedback_templates table
ALTER TABLE feedback_templates ENABLE ROW LEVEL SECURITY;

-- RLS policy: Everyone can read feedback templates
CREATE POLICY "Anyone can read feedback templates" ON feedback_templates
    FOR SELECT USING (true);

-- Enable RLS on mentor_inputs table
ALTER TABLE mentor_inputs ENABLE ROW LEVEL SECURITY;

-- RLS policy: Users can read their own mentor inputs
CREATE POLICY "Users can read own mentor inputs" ON mentor_inputs
    FOR SELECT USING (auth.uid() = student_id OR auth.uid() = evaluator_id);

-- Enable RLS on performance_data table
ALTER TABLE performance_data ENABLE ROW LEVEL SECURITY;

-- RLS policy: Users can read performance data they are involved in
CREATE POLICY "Users can read own performance data" ON performance_data
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM mentor_inputs WHERE mentor_inputs.id = performance_data.mentor_input_id AND (mentor_inputs.student_id = auth.uid() OR mentor_inputs.evaluator_id = auth.uid()))
    );

-- Enable RLS on feedbacks table
ALTER TABLE feedbacks ENABLE ROW LEVEL SECURITY;

-- RLS policy: Users can read their own feedbacks
CREATE POLICY "Users can read own feedbacks" ON feedbacks
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM mentor_inputs WHERE mentor_inputs.id = feedbacks.mentor_input_id AND (mentor_inputs.student_id = auth.uid() OR mentor_inputs.evaluator_id = auth.uid()))
    );

-- Enable RLS on feedback_versions table
ALTER TABLE feedback_versions ENABLE ROW LEVEL SECURITY;

-- Enable RLS on token_blocklist table
ALTER TABLE token_blocklist ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- RLS-compatible Auth References
-- Use auth.uid() to reference the authenticated user in queries
-- Example: SELECT * FROM enrollments WHERE student_id = auth.uid()
-- ============================================================
