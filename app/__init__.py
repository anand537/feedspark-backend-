import os
from flask import Flask
from dotenv import load_dotenv
import logging
import json
import time
import uuid
from flask import g, request, jsonify

# Import extensions from the central extensions file
from app.extensions import afg_db, jwt, mail, cors, socketio, limiter, redis_client, jwt_redis_blocklist # Import redis_client and jwt_redis_blocklist
from app.swagger import init_swagger
from flask_jwt_extended import get_jwt_identity, decode_token # For logging user_id

load_dotenv()

def create_app(config_class='config.Config'):
    app = Flask(__name__)
    
    # Load configuration from config.py
    app.config.from_object(config_class)
    
    # The DATABASE_URL from Supabase starts with postgresql:// 
    # but SQLAlchemy needs postgresql+psycopg2://. This ensures it's correct.
    database_url = app.config.get('SQLALCHEMY_DATABASE_URI')
    if database_url and database_url.startswith('postgresql://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    
    # --- Structured Logging Configuration ---
    def configure_logging(app):
        # Create a custom logger for access logs
        access_logger = logging.getLogger('access_logger')
        access_logger.setLevel(logging.INFO)
        access_logger.propagate = False # Prevent logs from going to root logger

        # Create a stream handler
        handler = logging.StreamHandler()

        # Create a JSON formatter. JsonFormatter automatically includes 'extra' fields.
        # The format string can be simple, as 'extra' fields will be added to the JSON output.
        from pythonjsonlogger import jsonlogger
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(message)s',
            json_indent=2 if app.debug else None # Indent for readability in debug mode
        )
        handler.setFormatter(formatter)
        access_logger.addHandler(handler)

        app.access_logger = access_logger # Attach to app for easy access

    def mask_sensitive_data(data, sensitive_keys=['password', 'otp', 'current_password', 'new_password', 'confirm_new_password', 'access_token', 'refresh_token']):
        """Recursively masks sensitive data in dictionaries and lists."""
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if key in sensitive_keys:
                    masked_data[key] = '[MASKED]'
                else:
                    masked_data[key] = mask_sensitive_data(value, sensitive_keys)
            return masked_data
        elif isinstance(data, list):
            return [mask_sensitive_data(item, sensitive_keys) for item in data]
        return data

    configure_logging(app)

    @app.before_request
    def before_request_log():
        g.request_start_time = time.time()
        g.request_id = str(uuid.uuid4())

        user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                # Decode without full verification for logging purposes only
                # allow_expired=True and allow_unverified=True are for logging only,
                # Flask-JWT-Extended will perform full verification later in jwt_required().
                decoded_token = decode_token(token, allow_expired=True, allow_unverified=True)
                user_id = decoded_token.get('sub')
            except Exception:
                user_id = '[Invalid/Unverifiable Token]'

        request_body_logged = {}
        if request.is_json:
            try:
                request_body_logged = mask_sensitive_data(request.get_json())
            except Exception:
                request_body_logged = '[Invalid JSON Body]'
        elif request.form:
            request_body_logged = mask_sensitive_data(request.form.to_dict())
        elif request.data:
            if len(request.data) > 1024: # Limit size for logging
                request_body_logged = f'[Binary/Large Data, size: {len(request.data)} bytes]'
            else:
                try:
                    request_body_logged = request.data.decode('utf-8', errors='ignore')
                except Exception:
                    request_body_logged = '[Undecodable Data]'

        app.access_logger.info(
            'API Request',
            extra={
                'request_id': g.request_id,
                'method': request.method,
                'path': request.path,
                'ip_address': request.remote_addr,
                'user_id': user_id,
                'request_body': request_body_logged,
                'request_headers': {k: '[MASKED]' if k.lower() == 'authorization' else v for k, v in request.headers.items()}
            }
        )

    @app.after_request
    def after_request_log(response):
        duration_ms = int((time.time() - g.request_start_time) * 1000)

        user_id = None
        try:
            user_id = get_jwt_identity(optional=True)
        except Exception:
            pass # If JWT processing failed earlier, get_jwt_identity might still error

        response_body_logged = {}
        if response.is_json:
            try:
                # response.get_json() consumes the stream, so read from response.data
                response_body_logged = mask_sensitive_data(json.loads(response.data.decode('utf-8', errors='ignore')))
            except Exception:
                response_body_logged = '[Invalid JSON Body]'
        elif response.data:
            if len(response.data) > 1024: # Limit size for logging
                response_body_logged = f'[Binary/Large Data, size: {len(response.data)} bytes]'
            else:
                try:
                    response_body_logged = response.data.decode('utf-8', errors='ignore')
                except Exception:
                    response_body_logged = '[Undecodable Data]'

        app.access_logger.info(
            'API Response',
            extra={
                'request_id': g.request_id,
                'method': request.method,
                'path': request.path,
                'ip_address': request.remote_addr,
                'user_id': user_id,
                'status_code': response.status_code,
                'duration_ms': duration_ms,
                'response_body': response_body_logged
            }
        )
        return response

    @app.teardown_request
    def teardown_request_log(exception=None):
        if exception:
            # Ensure request_id is available even if before_request failed early
            request_id = getattr(g, 'request_id', 'N/A')
            user_id = None
            try:
                user_id = get_jwt_identity(optional=True)
            except Exception:
                pass

            app.access_logger.error(
                'Unhandled Exception',
                exc_info=exception,
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.path,
                    'ip_address': request.remote_addr,
                    'user_id': user_id,
                    'error_type': type(exception).__name__,
                    'error_message': str(exception)
                }
            )

    # Initialize Flask extensions with the app
    afg_db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    jwt_redis_blocklist.init_app(app) # Initialize JWT Redis blocklist
    redis_client.init_app(app) # Initialize redis_client
    cors.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    limiter.init_app(app)
    
    # Initialize AI clients
    from app.services.assignment_ai import init_ai_clients
    init_ai_clients(app)

    # Initialize Swagger
    init_swagger(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.file_routes import file_bp
    from app.routes.routes import bp as main_bp
    from app.routes.api import api_bp
    from app.routes.ai_routes import ai_bp
    from app.routes.health import health_bp
    from app.routes.notification_routes import notification_bp
    from app.routes.chatbot import chatbot_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(chatbot_bp)

    # The db.create_all() call has been removed.
    # Database initialization should be handled by a migration tool (like Flask-Migrate)
    # or a dedicated script like 'app/models/create_tables.py'.
    # Running it here can cause issues and is not recommended for production.

    # Register SocketIO events
    from app import socket_events

    return app
