# Store configuration variables (API keys, debug mode)
import os
from datetime import timedelta

# Load environment variables for security
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or 'a-very-secret-key'
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    
    # Supabase PostgreSQL Configuration
    # SQLALCHEMY_DATABASE_URI is the variable Flask-SQLAlchemy uses
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    # Redis Configuration for JWT Blacklist (can be same as REDIS_URL or different)
    JWT_REDIS_URL = os.environ.get('JWT_REDIS_URL', os.environ.get('REDIS_URL', 'redis://localhost:6379/1'))

    # Database Configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True for SQL query logging

    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # Gmail SMTP Configuration
    GMAIL_USER = os.environ.get('GMAIL_USER')
    GMAIL_PASS = os.environ.get('GMAIL_PASS')
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

    # Redis Configuration for OTPs and Caching
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    # OTP Expiration (in seconds)
    OTP_EXPIRATION_SECONDS = int(os.environ.get('OTP_EXPIRATION_SECONDS', 300)) # 5 minutes

    # Swagger/OpenAPI Configuration
    SWAGGER = {
        'title': 'Auto-Feedback Generator API',
        'uiversion': 3,
        'openapi': '3.0.2',
        'specs_route': '/apidocs/'
    }
