# Supabase Schema Connection Assessment

## Executive Summary

**The project is NOT fully connected with the Supabase schema.** There is a significant schema mismatch between the defined SQL schemas and the Python ORM models.

---

## Findings

### 1. Multiple Schema Definitions Conflicting

| Schema File | ID Type | Target |
|------------|--------|--------|
| `app/models/AFG_SCHEMA.sql` | INTEGER (SERIAL) | Original PostgreSQL |
| `app/models/SUPABASE_SCHEMA.sql` | UUID | Supabase migration target |
| Python models in `app/models/*.py` | INTEGER | Aligns with AFG_SCHEMA |

### 2. Python ORM Models Are Incompatible with SUPABASE_SCHEMA.sql

**Current state in app/models/user.py:**
```python
id = afg_db.Column(afg_db.Integer, primary_key=True)
user_type = afg_db.Column(afg_db.String(50), nullable=False)
```

**Expected for Supabase (from SUPABASE_SCHEMA.sql):**
```python
id = afg_db.Column(afg_db.UUID, primary_key=True)
role = afg_db.Column(afg_db.String(50), nullable=False)  # 'admin', 'mentor', 'student'
```

### 3. Field Name Mismatches

| Python Model | SUPABASE_SCHEMA.sql |
|-------------|-------------------|
| `user_type` | `role` |
| `password` | `password_hash` |
| `instructor_id` (Course) | `mentor_id` |

### 4. Database Connection Verified

The project CAN connect to Supabase PostgreSQL (tested via `test_supabase.py`), but uses the INTEGER-based schema, not the UUID-based Supabase schema.

---

## Incompatible Files

### Python Model Files Using INTEGER IDs:
- `app/models/user.py` - `id = afg_db.Column(afg_db.Integer, primary_key=True)`
- `app/models/course.py` - `id = afg_db.Column(afg_db.Integer, primary_key=True)`
- `app/models/announcement.py`
- `app/models/chat_group.py`
- `app/models/feedback.py`
- `app/models/feedback_template.py`
- `app/models/meeting.py`
- `app/models/message.py`
- `app/models/notification.py`
- `app/models/rubric.py`
- `app/models/token_blocklist.py`

### API Files Affected:
- `app/api/courses.py` - Uses `int` for course_id
- `app/api/assignments.py` - Uses `int` for IDs
- `app/api/submissions.py` - Uses `int` for IDs
- `app/api/users.py`
- `app/api/admin.py`
- `app/api/analytics.py`
- `app/api/announcements.py`
- `app/api/chat_groups.py`
- `app/api/feedback.py`
- `app/api/feedback_templates.py`
- `app/api/meetings.py`
- `app/api/messages.py`
- `app/api/mentor.py`
- `app/api/students.py`

---

## What Works

1. **Database Connection**: Configured to work with Supabase PostgreSQL
   - `config.py` sets `SQLALCHEMY_DATABASE_URI` from environment
   - `app/__init__.py` converts `postgresql://` to `postgresql+psycopg2://`
   
2. **Schema SQL Files**: Both `AFG_SCHEMA.sql` and `SUPABASE_SCHEMA.sql` are well-defined

3. **Setup Scripts**: `test_supabase.py` and `setup_supabase.py` work correctly

---

## Missing Components

1. **Migration Tool**: No Flask-Migrate (Alembic) setup
2. **UUID Support**: Python models not updated to use UUID primary keys
3. **Field Alignment**: Field names don't match SUPABASE_SCHEMA.sql
4. **RLS Integration**: Row Level Security policies exist in SQL but not connected to Python

---

## Recommendations

1. **Option A**: Keep INTEGER schema - Continue using AFG_SCHEMA.sql (works but loses Supabase benefits)
2. **Option B**: Migrate to UUID - Update all Python models to use UUID and match SUPABASE_SCHEMA.sql

The project needs a migration strategy to fully connect with the Supabase schema.
