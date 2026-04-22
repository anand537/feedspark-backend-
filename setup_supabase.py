#!/usr/bin/env python3
"""
Supabase PostgreSQL Migration Setup Wizard
===========================================
Interactive setup guide for migrating to Supabase PostgreSQL

Run this script to complete the migration setup:
    python setup_supabase.py
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"{title:^70}")
    print(f"{'='*70}\n")

def print_step(step_num, title):
    """Print step header"""
    print(f"\n{'─'*70}")
    print(f"STEP {step_num}: {title}")
    print(f"{'─'*70}\n")

def print_success(msg):
    """Print success message"""
    print(f"✓ {msg}")

def print_error(msg):
    """Print error message"""
    print(f"✗ {msg}")

def print_warning(msg):
    """Print warning message"""
    print(f"⚠ {msg}")

def print_info(msg):
    """Print info message"""
    print(f"ℹ {msg}")

def check_env_file():
    """Check if .env file exists"""
    env_file = Path('.env')
    
    if env_file.exists():
        print_success(".env file exists")
        return True
    else:
        print_error(".env file not found")
        
        env_example = Path('.env.example')
        if env_example.exists():
            print_info("Creating .env from .env.example...")
            try:
                with open('.env.example', 'r') as src:
                    content = src.read()
                with open('.env', 'w') as dst:
                    dst.write(content)
                print_success(".env file created from template")
                return True
            except Exception as e:
                print_error(f"Failed to create .env: {e}")
                return False
        else:
            print_error(".env.example not found either")
            return False

def check_database_url():
    """Check if DATABASE_URL is configured"""
    load_dotenv()
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print_error("DATABASE_URL not set in .env")
        return False
    
    if 'db.' in database_url and 'supabase.co' in database_url:
        print_success("DATABASE_URL is configured with Supabase")
        # Mask password
        masked = database_url.split('@')[0] + '@***@' + database_url.split('@')[1]
        print_info(f"Connection: {masked}")
        return True
    else:
        print_warning("DATABASE_URL doesn't look like Supabase format")
        print_info(f"Current: {database_url}")
        return True  # Still allow proceeding

def check_jwt_key():
    """Check if JWT_SECRET_KEY is configured"""
    load_dotenv()
    jwt_key = os.getenv('JWT_SECRET_KEY')
    
    if not jwt_key or jwt_key == 'your-super-secret-key-min-32-chars-recommended':
        print_warning("JWT_SECRET_KEY is default or missing")
        print_info("Using default for development is OK, but set strong key for production")
        return True
    
    if len(jwt_key) < 32:
        print_warning(f"JWT_SECRET_KEY is only {len(jwt_key)} chars (recommended 32+)")
        return True
    
    print_success("JWT_SECRET_KEY is configured")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\nInstalling Python dependencies...\n")
    
    try:
        # Check if requirements.txt exists
        if not Path('requirements.txt').exists():
            print_error("requirements.txt not found")
            return False
        
        # Show what will be installed
        with open('requirements.txt', 'r') as f:
            packages = f.read().strip().split('\n')
            print("Packages to install:")
            for pkg in packages:
                if pkg and not pkg.startswith('#'):
                    print(f"  • {pkg}")
        
        # Install packages
        print("\n")
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            capture_output=False
        )
        
        if result.returncode == 0:
            print_success("Dependencies installed successfully")
            return True
        else:
            print_error("Failed to install dependencies")
            return False
            
    except Exception as e:
        print_error(f"Error during installation: {e}")
        return False

def test_database_connection():
    """Test connection to Supabase"""
    print("\nTesting database connection...\n")
    
    try:
        from sqlalchemy import create_engine, text
        load_dotenv()
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print_error("DATABASE_URL not set")
            return False
        
        # Convert if needed
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
        
        print_info("Connecting to Supabase PostgreSQL...")
        engine = create_engine(database_url, connect_args={'connect_timeout': 5})
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0].split(',')[0]
            print_success(f"Connected! {version}")
            return True
            
    except ImportError:
        print_warning("SQLAlchemy not installed yet. Run step 1 first.")
        return False
    except Exception as e:
        print_error(f"Connection failed: {e}")
        print_info("Troubleshooting:")
        print_info("  1. Check DATABASE_URL in .env is correct")
        print_info("  2. Verify Supabase project is active")
        print_info("  3. Check IP whitelist in Supabase settings")
        return False

def test_flask_app():
    """Test Flask app initialization"""
    print("\nTesting Flask application...\n")
    
    try:
        print_info("Initializing Flask app...")
        from app import create_app
        
        app = create_app()
        print_success("Flask app created successfully")
        
        with app.app_context():
            print_success("App context initialized")
            
            from app.extensions import afg_db
            from sqlalchemy import inspect
            
            inspector = inspect(afg_db.engine)
            tables = inspector.get_table_names()
            
            if tables:
                print_success(f"Database has {len(tables)} table(s):")
                for table in tables:
                    print(f"    • {table}")
            else:
                print_info("No tables yet (will be created on first run)")
        
        return True
        
    except ImportError as e:
        print_warning(f"App not ready yet: {e}")
        return False
    except Exception as e:
        print_error(f"Flask app test failed: {e}")
        return False

def run_automated_tests():
    """Run automated test suite"""
    print("\nRunning automated tests...\n")
    
    test_files = [
        'test_supabase_connection.py',
        'test_auth_manual.py'
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"\nRunning {test_file}...")
            print(f"{'─'*50}")
            result = subprocess.run([sys.executable, test_file])
            if result.returncode != 0:
                print_warning(f"{test_file} had some issues")
        else:
            print_info(f"{test_file} not found (optional)")

def show_next_steps():
    """Show next steps"""
    print_header("SETUP COMPLETE! 🎉")
    
    print("Your application is now ready to use Supabase PostgreSQL!\n")
    
    print("NEXT STEPS:\n")
    print("1. Start the Flask application:")
    print("   $ python run.py\n")
    
    print("2. In another terminal, test the API:")
    print("   $ python test_auth_manual.py\n")
    
    print("3. You can also use Postman for manual testing:")
    print("   • Import: postman_collection.json\n")
    
    print("4. Monitor your database:")
    print("   • Visit: https://app.supabase.com\n")
    
    print("DOCUMENTATION:\n")
    print("• SUPABASE_MIGRATION_GUIDE.md - Complete setup guide")
    print("• MIGRATION_STATUS.md - Migration status overview")
    print("• AUTHENTICATION_GUIDE.md - Authentication system details\n")

def main():
    """Run setup wizard"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║     Supabase PostgreSQL Migration Setup Wizard                ║
    ║   Auto-Feedback Generator Backend                            ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    all_passed = True
    
    # Step 1: Environment Setup
    print_step(1, "Environment Configuration")
    if not check_env_file():
        print_error("Please set up .env file manually")
        return False
    check_database_url()
    check_jwt_key()
    
    # Step 2: Install Dependencies
    print_step(2, "Install Python Dependencies")
    if not install_dependencies():
        print_error("Failed to install dependencies")
        print_info("Try running: pip install -r requirements.txt")
        all_passed = False
    
    # Step 3: Database Connection
    print_step(3, "Test Database Connection")
    if not test_database_connection():
        print_warning("Database connection failed")
        print_info("Fix the connection and try again")
        all_passed = False
    
    # Step 4: Flask App
    print_step(4, "Test Flask Application")
    if not test_flask_app():
        print_warning("Flask app test had issues")
        print_info("Some issues are expected if not all dependencies installed")
        
    # Step 5: Run Tests (Optional)
    print_step(5, "Run Automated Tests (Optional)")
    print("Would you like to run automated tests? (y/n): ", end="")
    if input().lower() == 'y':
        run_automated_tests()
    
    # Show results
    if all_passed:
        show_next_steps()
        return True
    else:
        print_header("SETUP PARTIALLY COMPLETE")
        print("Some steps had issues. Please review the messages above.")
        print("Try running the following to diagnose:")
        print("  python test_supabase_connection.py")
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
