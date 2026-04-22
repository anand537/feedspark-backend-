# Auto-Feedback Backend - Complete System Design Mind Map

```
📊 AUTO-FEEDBACK GENERATOR BACKEND SYSTEM DESIGN
═══════════════════════════════════════════════════════════════════════════════

┌──────────────────────────────────────────────────────────────────────────────┐
│                           🏗️ ARCHITECTURE OVERVIEW                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  🎯 PURPOSE: AI-powered automated feedback system for education             │
│     • Generate personalized feedback using AI                                │
│     • Manage courses, assignments, rubrics, meetings                         │
│     • Real-time chat, announcements, notifications                           │
│     • Role-based: super-admin, mentor, student                              │
│                                                                              │
│  🛠️ TECH STACK:                                                             │
│     ├─ Flask (Python) + SQLAlchemy (PostgreSQL/Supabase)                    │
│     ├─ JWT Authentication + Redis (blocklist/caching)                       │
│     ├─ OpenAI GPT-3.5-turbo (AI feedback generation)                        │
│     ├─ Socket.IO (real-time chat)                                           │
│     ├─ Gmail SMTP (emails) + Supabase Storage (files)                       │
│     └─ Rate limiting, CORS, Swagger API docs                                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                                📁 FILE STRUCTURE                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ROOT DIRECTORY (d:/project/auto_feedback_generator/auto-feedback-backend)   │
│  ├─ .env, .gitignore, config.py, requirements.txt, run.py                    │
│  ├─ setup_*.py (storage/supabase), test_*.py, process_*.py (cron jobs)      │
│  ├─ pyproject.toml, pytest.ini, uv.lock                                     │
│  └─ data/ (CSV samples), docs/, instance/, logs/, tests/, uploads/          │
│                                                                              │
│  📂 app/ (Core Flask Application)                                            │
│  ├─ __init__.py (create_app(), logging, blueprints registration)            │
│  ├─ extensions.py (db, jwt, mail, socketio, redis, limiter)                 │
│  ├─ ai.py (OpenAI GPT integration - generate_feedback_ai())                 │
│  ├─ decorators.py (role_required())                                         │
│  ├─ socket_events.py (@socketio.on connect/authenticate)                    │
│  ├─ swagger.py (init_swagger())                                             │
│  │                                                                              │
│  📂 api/ (REST API Blueprints - /api/* JWT protected)                        │
│  ├─ analytics.py, announcements.py (CRUD + notifications)                   │
│  ├─ assignments.py (CRUD), chat_groups.py (create/send messages)            │
│  ├─ courses.py, feedback_templates.py, feedback.py (AI generation)          │
│  ├─ meetings.py, messages.py, submissions.py, users.py (CRUD + role access) │
│                                                                              │
│  📂 models/ (SQLAlchemy Models - Supabase/PostgreSQL)                        │
│  ├─ __init__.py (imports all), AFG_SCHEMA.sql                               │
│  ├─ announcement.py, chat_group.py, course.py (Assignment/Submission)       │
│  ├─ feedback_template.py, feedback.py (MentorInput/PerformanceData/Version) │
│  ├─ meeting.py (MeetingParticipant), message.py, notification.py            │
│  ├─ rubric.py (Criterion), token_blocklist.py, user.py                      │
│  └─ create_tables.py                                                        │
│                                                                              │
│  📂 routes/ (Main Blueprints)                                                │
│  ├─ __init__.py, ai_routes.py (/generate-feedback), api.py                  │
│  ├─ auth.py (register/login/OTP/JWT), file_routes.py (rubric upload)        │
│  ├─ health.py (/health), notification_routes.py (CRUD/mark-read)            │
│  └─ routes.py (/)                                                           │
│                                                                              │
│  📂 services/                                                                │
│  ├─ __init__.py, ai_service.py, notification_service.py                     │
│                                                                              │
│  📂 static/js/index.js, templates/ (base.html, login.html, emails/*.html)    │
│                                                                              │
│  📂 utils/                                                                   │
│  ├─ auth_utils.py (OTP/password attempts), email_utils.py (SMTP templates)  │
│  ├─ storage_utils.py (Supabase upload/delete/signed_url)                    │
│  └─ validation.py (validate_password())                                     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                           🔑 KEY FUNCTIONS BY MODULE                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  🏠 app/__init__.py                                                          │
│     └─ create_app() - Initializes Flask + all extensions + blueprints       │
│                                                                              │
│  🤖 app/ai.py                                                                │
│     └─ generate_feedback_ai() - OpenAI GPT-3.5-turbo for personalized fb    │
│                                                                              │
│  🛡️ app/utils/auth_utils.py                                                  │
│     ├─ generate_secure_otp(), store_otp(), verify_otp()                     │
│     └─ increment_failed_*_attempt(), reset_failed_*_attempts()              │
│                                                                              │
│  📧 app/utils/email_utils.py                                                 │
│     ├─ send_email(), send_async_email() - Gmail SMTP                        │
│     ├─ send_welcome_email(), send_otp_email(), send_feedback_notification() │
│     └─ send_attendance_report_email() (CSV attach)                          │
│                                                                              │
│  💾 app/utils/storage_utils.py                                               │
│     ├─ upload_file_to_supabase(), get_signed_url()                          │
│     └─ delete_file_async()                                                   │
│                                                                              │
│  👥 app/api/users.py                                                         │
│     ├─ get_users(), get_user(), create_user() (w/ auto-password)            │
│     └─ update_user(), delete_user() (super-admin only)                      │
│                                                                              │
│  📝 app/api/feedback.py                                                      │
│     ├─ create_feedback() - AI gen + PerformanceData + notifications         │
│     ├─ update/regenerate/revert/delete_feedback(), get_versions()           │
│     └─ generate_assignment_feedback_endpoint() (batch students)             │
│                                                                              │
│  🔔 app/services/notification_service.py                                     │
│     └─ create_notification()                                                 │
│                                                                              │
│  💬 app/socket_events.py                                                     │
│     ├─ @socketio.on('connect'), handle_authenticate()                       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                              🔄 DATA FLOW DIAGRAM                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Student submits → Assignment ─────┐                                         │
│                                    │                                         │
│  Mentor scores → Rubric ──→        │ → PerformanceData → AI_feedback_gen()    │
│  (criteria:score/remarks)          │     → Feedback (versions) → Email       │
│                                    │                                         │
│  Template selected ────────────────┘                                         │
│                                                                              │
│  Chat: socketio.connect() → authenticate → send_group_message()              │
│                                                                              │
│  Announcements → process_scheduled_announcements.py (cron) → notify          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                                🚀 API ENDPOINTS                              │
├──────────────────────────────────────────────────────────────────────────────┤
│  / (main), /health, /swagger                                                 │
│                                                                              │
│  AUTH: /auth/* (register, login, otp, jwt ops)                               │
│                                                                              │
│  USERS: /api/users (GET/POST/PUT/DELETE - role-based)                        │
│                                                                              │
│  FEEDBACK: /api/feedback (POST create/regenerate, GET versions/history)      │
│                                                                              │
│  COURSES/ASSIGNMENTS/SUBMISSIONS: CRUD ops                                   │
│                                                                              │
│  CHAT: /api/chat_groups/* (create/get/send messages)                         │
│                                                                              │
│  ANNOUNCEMENTS: /api/announcements (POST/GET/PUT/DELETE)                     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                                🧪 DEPLOYMENT & OPS                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Setup: setup_supabase.py → test_db → run.py                                 │
│                                                                              │
│  Cron: process_meeting_attendance.py, process_scheduled_announcements.py     │
│                                                                              │
│  Tests: pytest (tests/conftest.py, test_api_endpoints.py)                    │
│                                                                              │
│  Storage: uploads/rubric_files/ → Supabase signed URLs                       │
│                                                                              │
│  Logging: JSON structured logs (access_logger)                               │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                                📈 SYSTEM CAPACITY                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Users: super-admin > mentor > student (RBAC via decorators)                 │
│                                                                              │
│  Scale: Supabase (DB+Storage), Redis (sessions/blocklist), Gmail (email)     │
│                                                                              │
│  Real-time: Socket.IO for chat                                                │
│                                                                              │
│  AI: OpenAI GPT-3.5-turbo (cost-optimized)                                   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 🎉 Key Benefits of This Mind Map
- **One-time full scan complete** - No need to re-scan project
- **Visual navigation** - Folders → Files → Key Functions
- **Reduces confusion** - Clear data flows, roles, endpoints
- **Future-proof** - Easy to reference/modify specific modules
- **Error reduction** - Exact function names/locations

