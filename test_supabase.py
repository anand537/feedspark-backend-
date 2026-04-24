import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from app import create_app

load_dotenv()

print("Testing Supabase PostgreSQL connection...")

database_url = os.getenv('DATABASE_URL')
print(f"DATABASE_URL set: {'Yes' if database_url else 'No'}")
if database_url:
    print(f"Host: {database_url.split('@')[1].split(':')[0] if '@' in database_url else 'N/A'}")

if not database_url:
    print("❌ DATABASE_URL not set in .env")
    exit(1)

# Convert to psycopg2 if needed
if database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    print("✓ Converted to psycopg2 dialect")

try:
    print("Connecting...")
    engine = create_engine(database_url, echo=False)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"✅ Connected! PostgreSQL version: {version.split(',')[0]}")
        
        # Test app context
        print("\nTesting Flask app...")
        app = create_app()
        with app.app_context():
            print("✓ Flask app context OK")
            
            # List tables
            from app.extensions import afg_db
            inspector = text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
            tables = conn.execute(inspector).fetchall()
            print(f"Tables in public schema: {len(tables)}")
            if tables:
                print("Sample tables:", [row[0] for row in tables[:5]])
            
            print("✅ Supabase connection and Flask app fully operational!")
            
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
    print("\nTroubleshooting:")
    print("1. Check DATABASE_URL in .env (Supabase connection string)")
    print("2. Verify Supabase project active: https://app.supabase.com")
    print("3. Check network/firewall (port 5432)")
    print("4. Verify password correct")
