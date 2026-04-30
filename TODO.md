# TODO: Delete and Recreate Supabase Tables with Data

## Task: Delete all tables on Supabase and create new tables using Supabase schema, then push/store all the data from data.sql to Supabase

## Information Gathered:
- `apply_supabase_sql.py` is a Python script that:
  - Reads DATABASE_URL from environment variables
  - Reads schema from `app/models/SUPABASE_SCHEMA.sql` (22 UUID-based tables)
  - Reads data from `data/data.sql` (large INSERT statements)
  - Drops existing tables using CASCADE
  - Creates new tables from the schema
  - Loads all data from data.sql
  
- The schema includes tables: users, courses, enrollments, assignments, submissions, rubrics, criteria, meetings, meeting_participants, messages, conversations, chat_groups, chat_group_members, group_messages, notifications, feedback_templates, announcements, mentor_inputs, performance_data, feedbacks, feedback_versions, token_blocklist

## Plan:
1. Execute `apply_supabase_sql.py` script
2. Script will automatically:
   - Drop all existing tables (CASCADE)
   - Create new tables from SUPABASE_SCHEMA.sql
   - Load all data from data.sql

## Dependent Files:
- `app/models/SUPABASE_SCHEMA.sql` - schema definition
- `data/data.sql` - data to insert

## Execution Steps:
Run: `python apply_supabase_sql.py`

## Notes:
- Requires DATABASE_URL environment variable to be set
- Script handles SQL parsing including dollar-quoted strings
- Uses multiple passes to handle foreign key dependencies
