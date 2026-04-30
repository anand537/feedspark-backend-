#!/usr/bin/env python3
"""Check Supabase database tables and schema."""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("❌ DATABASE_URL not set in .env")
    sys.exit(1)

# Convert to psycopg2 if needed
if database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)

print("=" * 60)
print("SUPABASE DATABASE CHECK")
print("=" * 60)
print(f"Host: db.puwsulbqnnqoclrmlmne.supabase.co")
print(f"Database URL: {'*' * 20} (hidden)")
print()

try:
    from sqlalchemy import create_engine, text, inspect
    
    engine = create_engine(database_url, echo=False)
    
    with engine.connect() as conn:
        # Get PostgreSQL version
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"✅ Connected to PostgreSQL")
        print(f"   Version: {version}")
        print()
        
        # Get current schema
        result = conn.execute(text("SELECT current_schema();"))
        current_schema = result.fetchone()[0]
        print(f"✅ Current Schema: {current_schema}")
        print()
        
        # List all tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print("=" * 60)
        print(f"TABLES IN DATABASE: {len(tables)}")
        print("=" * 60)
        
        if tables:
            for table in sorted(tables):
                # Get row count
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table};"))
                    count = result.fetchone()[0]
                    print(f"  📋 {table}: {count} rows")
                except Exception as e:
                    print(f"  📋 {table}: (error counting)")
            print()
        else:
            print("  ⚠️ No tables found in database!")
            print()
            
        # Check specific important tables
        important_tables = ['users', 'courses', 'enrollments', 'assignments', 'submissions']
        
        print("=" * 60)
        print("IMPORTANT TABLES CHECK")
        print("=" * 60)
        
        for table in important_tables:
            if table in tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table};"))
                count = result.fetchone()[0]
                print(f"  ✅ {table}: {count} rows")
            else:
                print(f"  ❌ {table}: NOT FOUND")
        
        print()
        print("=" * 60)
        print("DATABASE CHECK COMPLETE")
        print("=" * 60)
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
