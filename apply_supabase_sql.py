import os
import re
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

load_dotenv()
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    raise SystemExit('DATABASE_URL is not set in .env')

schema_path = Path('app/models/SUPABASE_SCHEMA.sql')
data_path = Path('data/data.sql')
if not schema_path.exists() or not data_path.exists():
    raise SystemExit('Required SQL files are missing')

schema_sql = schema_path.read_text(encoding='utf-8')
data_sql = data_path.read_text(encoding='utf-8')

if db_url.startswith('postgresql+psycopg2://'):
    db_url = 'postgresql://' + db_url.split('postgresql+psycopg2://', 1)[1]


def strip_comments(sql_text):
    lines = []
    for line in sql_text.splitlines():
        if line.strip().startswith('--'):
            continue
        lines.append(line)
    return '\n'.join(lines)


def split_sql(sql_text):
    """Split SQL into individual statements, handling $$ dollar-quoted strings."""
    statements = []
    current = []
    i = 0
    state = None
    dollar_tag = None
    
    while i < len(sql_text):
        ch = sql_text[i]
        
        if state is None:
            # Not in a quoted context
            if ch == "'":
                current.append(ch)
                state = 'single'
            elif ch == '"':
                current.append(ch)
                state = 'double'
            elif ch == '$':
                # Try to match a dollar quote like $$, $func$, etc.
                m = re.match(r'\$[A-Za-z0-9_]*\$', sql_text[i:])
                if m:
                    dollar_tag = m.group(0)
                    current.append(dollar_tag)
                    i += len(dollar_tag) - 1  # Will be incremented at end of loop
                    state = 'dollar'
                else:
                    current.append(ch)
            elif ch == ';':
                current.append(ch)
                stmt = ''.join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []
            else:
                current.append(ch)
                
        elif state == 'single':
            current.append(ch)
            if ch == "'":
                # Check for escaped quote ''
                if i + 1 < len(sql_text) and sql_text[i + 1] == "'":
                    current.append("'")
                    i += 1
                else:
                    state = None
                    
        elif state == 'double':
            current.append(ch)
            if ch == '"':
                state = None
                
        elif state == 'dollar':
            current.append(ch)
            # Check if we've reached the closing dollar tag
            if sql_text[i:i+len(dollar_tag)] == dollar_tag:
                current.append(dollar_tag[1:])  # Append rest of tag
                i += len(dollar_tag) - 1  # Will be incremented at end of loop
                state = None
                
        i += 1
    
    leftover = ''.join(current).strip()
    if leftover:
        statements.append(leftover)
    
    return statements


def execute_statements(cursor, statements, max_passes=15):
    remaining = list(statements)
    for attempt in range(1, max_passes + 1):
        if not remaining:
            return
        next_round = []
        progress = False
        print(f'Pass {attempt}: executing {len(remaining)} statements...')
        for idx, stmt in enumerate(remaining, 1):
            try:
                cursor.execute(stmt)
                progress = True
            except psycopg2.errors.InsufficientPrivilege as exc:
                # Skip statements requiring elevated privileges
                if 'session_replication_role' in str(exc) or 'replication' in str(exc).lower():
                    print(f'Skipping privileged statement (replication): {stmt[:50]}...')
                    progress = True
                else:
                    raise
            except psycopg2.errors.ForeignKeyViolation as exc:
                # Defer foreign key violations until dependencies are loaded
                next_round.append(stmt)
            except psycopg2.Error as exc:
                text = str(exc).lower()
                if 'does not exist' in text or 'undefined table' in text or 'undefined column' in text or ('relation' in text and 'does not exist' in text):
                    next_round.append(stmt)
                else:
                    raise
        if not progress:
            raise RuntimeError(f'No progress after pass {attempt}. Remaining statements: {len(remaining)}')
        remaining = next_round
    if remaining:
        raise RuntimeError(f'Could not execute all statements after {max_passes} passes. Remaining: {len(remaining)}')


schema_sql = strip_comments(schema_sql)
data_sql = strip_comments(data_sql)
schema_statements = split_sql(schema_sql)
data_statements = split_sql(data_sql)

CREATE_TABLE_RE = re.compile(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z0-9_]+)', re.IGNORECASE)

def extract_table_names(statements):
    names = []
    for stmt in statements:
        m = CREATE_TABLE_RE.search(stmt)
        if m:
            names.append(m.group(1))
    return names


def drop_existing_tables(cursor, table_names):
    if not table_names:
        return
    print('Dropping existing tables to perform a clean reload...')
    for name in reversed(table_names):
        cursor.execute(sql.SQL('DROP TABLE IF EXISTS {} CASCADE').format(sql.Identifier(name)))
        print(f'Dropped table {name}')

print('Connecting to Supabase database...')
conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

existing_tables = extract_table_names(schema_statements)
if existing_tables:
    drop_existing_tables(cur, existing_tables)

print('Applying SUPABASE_SCHEMA.sql...')
execute_statements(cur, schema_statements)
print('Schema applied successfully.')

print('Applying data/data.sql...')
execute_statements(cur, data_statements)
print('Data loaded successfully.')

cur.close()
conn.close()
