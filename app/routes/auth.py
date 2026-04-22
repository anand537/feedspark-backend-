from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter.util import get_remote_address
from app.extensions import afg_db, jwt, limiter # Import limiter
from app.models import User # Assuming User model is defined in app/models.py, and User.id is int
from app.utils.email_utils import send_otp_email # Assuming send_otp_email is defined
from app.utils.auth_utils import generate_secure_otp, store_otp, verify_otp, \
    increment_failed_otp_attempt, get_failed_otp_attempts, reset_failed_otp_attempts, \
    MAX_FAILED_OTP_ATTEMPTS, OTP_LOCKOUT_SECONDS # Import new functions and constants
from app.utils.storage_utils import get_signed_url, upload_file_to_supabase, delete_file_async # Import storage utilities
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt # Import JWT functions
from app.extensions import jwt_redis_blocklist # Import the JWT Redis blocklist client
from app.utils.validation import validate_password # Assuming you have password validation
 
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# --- Custom Key Functions for Rate Limiting ---
def get_email_from_request():
    """Extracts email from request JSON for rate limiting."""
    if request.is_json:
        email = request.json.get('email')
        if email:
            return email
    return request.remote_addr # Fallback to IP if email not found or not JSON

def get_user_id_from_request():
    """Extracts user_id from request JSON for rate limiting."""
    if request.is_json:
        user_id = request.json.get('user_id')
        if user_id:
            return str(user_id) # Ensure it's a string for the key
    return request.remote_addr # Fallback to IP if user_id not found or not JSON


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("1 per minute", key_func=get_email_from_request, error_message="Too many registration attempts for this email. Please wait a minute.")
@limiter.limit("5 per hour", key_func=get_remote_address, error_message="Too many registration attempts from this IP. Please try again later.")
def register_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user_name = data.get('user_name', 'New User') # Assuming user_name might be provided

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    # Validate password strength
    password_errors = validate_password(password)
    if password_errors:
        return jsonify({"message": "Password does not meet requirements", "errors": password_errors}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "User with that email already exists"}), 409

    try:
        # Create user but mark as unverified initially
        new_user = User(
            email=email,
            password_hash=generate_password_hash(password),
            is_verified=False # User is not verified until OTP is confirmed
        )
        afg_db.session.add(new_user)
        afg_db.session.commit()
        
        # Generate and store OTP for registration verification
        otp_code = generate_secure_otp(length=6)
        if not store_otp(new_user.id, otp_code, purpose='registration'):
            # Log error, but don't expose too much detail to the user
            current_app.logger.error(f"Failed to store OTP for new user {new_user.id}")
            return jsonify({"message": "User registered, but failed to send verification email. Please try requesting OTP again."}), 500

        # Send OTP email
        send_otp_email(user_email=email, user_name=user_name, otp_code=otp_code)
        current_app.logger.info(f"OTP sent to {email} for registration verification.")

        return jsonify({
            "message": "Registration successful! Please check your email for the OTP to verify your account.",
            "user_id": new_user.id # Return user_id for subsequent OTP verification
        }), 201

    except Exception as e:
        afg_db.session.rollback()
        current_app.logger.error(f"Error during user registration: {e}", exc_info=True)
        return jsonify({"message": "An error occurred during registration"}), 500

@auth_bp.route('/register/verify-otp', methods=['POST'])
@limiter.limit("5 per 15 minutes", key_func=get_user_id_from_request, error_message="Too many OTP verification attempts. Please request a new OTP.")
def verify_registration_otp():
    data = request.get_json()
    user_id = data.get('user_id')
    submitted_otp = data.get('otp')

    if not user_id or not submitted_otp:
        return jsonify({"message": "User ID and OTP are required"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # --- Dynamic Rate Limiting: Check failed attempts ---
    failed_attempts = get_failed_otp_attempts(user.id, 'registration')
    if failed_attempts >= MAX_FAILED_OTP_ATTEMPTS:
        return jsonify({
            "message": f"Too many failed OTP attempts. Please wait {OTP_LOCKOUT_SECONDS // 60} minutes before trying again or request a new OTP."
        }), 429

    if verify_otp(user.id, 'registration', submitted_otp):
        user.is_verified = True
        afg_db.session.commit()
        reset_failed_otp_attempts(user.id, 'registration') # Reset on success
        return jsonify({"message": "Account verified successfully!"}), 200
    else:
        increment_failed_otp_attempt(user.id, 'registration') # Increment on failure
        return jsonify({"message": "Invalid or expired OTP"}), 401

@auth_bp.route('/forgot-password', methods=['POST'])
# Note: For forgot-password, the rate limits are primarily on the request itself (by email/IP)
# The dynamic lockout based on failed OTP attempts happens in /reset-password
# This is because we don't want to reveal if an email exists by locking out here.
@limiter.limit("1 per minute", key_func=get_email_from_request, error_message="Too many password reset requests for this email. Please wait a minute.")
@limiter.limit("5 per hour", key_func=get_remote_address, error_message="Too many password reset requests from this IP. Please try again later.")
def forgot_password():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"message": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        # For security, always return a generic message even if user not found
        return jsonify({"message": "If an account with that email exists, a password reset OTP has been sent."}), 200

    # Generate and store OTP for password reset
    otp_code = generate_secure_otp(length=6)
    if not store_otp(user.id, otp_code, purpose='password_reset'):
        current_app.logger.error(f"Failed to store OTP for password reset for user {user.id}")
        return jsonify({"message": "Failed to initiate password reset. Please try again."}), 500

    # Send OTP email
    send_otp_email(user_email=user.email, user_name=user.email, otp_code=otp_code) # Use email as name if no name field
    current_app.logger.info(f"Password reset OTP sent to {user.email}.")

    return jsonify({
        "message": "If an account with that email exists, a password reset OTP has been sent.",
        "user_id": user.id # Return user_id for subsequent OTP verification
    }), 200

@auth_bp.route('/reset-password', methods=['POST'])
@limiter.limit("5 per 15 minutes", key_func=get_user_id_from_request, error_message="Too many password reset OTP attempts. Please request a new OTP.")
def reset_password():
    data = request.get_json()
    user_id = data.get('user_id')
    submitted_otp = data.get('otp')
    new_password = data.get('new_password')

    if not user_id or not submitted_otp or not new_password:
        return jsonify({"message": "User ID, OTP, and new password are required"}), 400

    # Validate new password strength
    password_errors = validate_password(new_password)
    if password_errors:
        return jsonify({"message": "New password does not meet requirements", "errors": password_errors}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # --- Dynamic Rate Limiting: Check failed attempts ---
    failed_attempts = get_failed_otp_attempts(user.id, 'password_reset')
    if failed_attempts >= MAX_FAILED_OTP_ATTEMPTS:
        return jsonify({
            "message": f"Too many failed OTP attempts. Please wait {OTP_LOCKOUT_SECONDS // 60} minutes before trying again or request a new OTP."
        }), 429

    if verify_otp(user.id, 'password_reset', submitted_otp):
        # OTP is valid, update password
        user.set_password(new_password)
        afg_db.session.commit()
        reset_failed_otp_attempts(user.id, 'password_reset') # Reset on success
        return jsonify({"message": "Password reset successfully!"}), 200
    else:
        increment_failed_otp_attempt(user.id, 'password_reset') # Increment on failure
        return jsonify({"message": "Invalid or expired OTP"}), 401

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute", key_func=get_email_from_request, error_message="Too many login attempts for this email. Please wait a minute.")
@limiter.limit("10 per hour", key_func=get_remote_address, error_message="Too many login attempts from this IP. Please try again later.")
def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    otp = data.get('otp')
    otp_purpose = data.get('otp_purpose', 'login') # Default purpose for OTP login

    if not email:
        return jsonify({"message": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        # Generic message to avoid user enumeration
        return jsonify({"message": "Invalid credentials"}), 401

    if not user.is_verified:
        return jsonify({"message": "Account not verified. Please verify your email."}), 403

    # --- Dynamic Rate Limiting: Check failed password attempts ---
    failed_password_attempts = get_failed_password_attempts(user.id)
    if failed_password_attempts >= MAX_FAILED_PASSWORD_ATTEMPTS:
        return jsonify({
            "message": f"Too many failed password attempts. Please wait {PASSWORD_LOCKOUT_SECONDS // 60} minutes before trying again."
        }), 429

    authenticated = False
    if password:
        # Password-based login
        if user.check_password(password): # Assumes User model has check_password method
            authenticated = True
            reset_failed_password_attempts(user.id) # Reset on successful password login
        else:
            # Increment failed password attempts
            increment_failed_password_attempt(user.id)
            # Note: The generic "Invalid credentials" message is used to prevent
            # user enumeration, even if we track attempts internally.
            # The lockout message will be returned by the check above on subsequent attempts.

            current_app.logger.warning(f"Failed password login attempt for user {user.id}")
            return jsonify({"message": "Invalid credentials"}), 401
    elif otp:
        # OTP-based login (e.g., passwordless login, or after a successful password reset OTP verification)
        
        # Check if the user is currently locked out for this OTP purpose
        failed_attempts = get_failed_otp_attempts(user.id, otp_purpose)
        if failed_attempts >= MAX_FAILED_OTP_ATTEMPTS:
            return jsonify({
                "message": f"Too many failed OTP attempts. Please wait {OTP_LOCKOUT_SECONDS // 60} minutes or request a new OTP."
            }), 429

        if verify_otp(user.id, otp_purpose, otp):
            authenticated = True
            reset_failed_otp_attempts(user.id, otp_purpose) # Reset on success
        else:
            increment_failed_otp_attempt(user.id, otp_purpose) # Increment on failure
            return jsonify({"message": "Invalid or expired OTP"}), 401
    else:
        return jsonify({"message": "Password or OTP is required"}), 400

    if authenticated:
        # Generate JWTs upon successful authentication
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        return jsonify(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user.id,
            email=user.email
        ), 200
    else:
        return jsonify({"message": "Authentication failed"}), 401

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Allows an authenticated user to change their password.
    Requires current password for verification and a new password.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_new_password = data.get('confirm_new_password')

    if not current_password or not new_password or not confirm_new_password:
        return jsonify({"message": "Current password, new password, and confirmation are required"}), 400

    if new_password != confirm_new_password:
        return jsonify({"message": "New password and confirmation do not match"}), 400

    # Verify current password
    if not user.check_password(current_password):
        return jsonify({"message": "Incorrect current password"}), 401

    # Validate new password strength
    password_errors = validate_password(new_password)
    if password_errors:
        return jsonify({"message": "New password does not meet requirements", "errors": password_errors}), 400

    user.set_password(new_password)
    afg_db.session.commit()

    return jsonify({"message": "Password changed successfully"}), 200

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    """
    Allows an authenticated user to update their own profile (name, bio, profile image).
    Supports both application/json and multipart/form-data.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    # Determine if request is JSON or multipart/form-data
    if request.is_json:
        data = request.get_json()
        files = {} # No files in JSON request
    else:
        data = request.form
        files = request.files

    # Update name
    if 'name' in data and data['name']:
        user.name = data['name']

    # Update bio
    if 'bio' in data: # Allow bio to be cleared
        user.bio = data['bio']

    # Handle profile image upload
    if 'profile_image' in files:
        profile_image_file = files['profile_image']
        if profile_image_file.filename != '':
            # Delete old profile image if it exists
            if user.profile_image_url:
                delete_file_async(user.profile_image_url)
            
            try:
                # Upload new image to Supabase 'profile_images' bucket
                # Folder path for profile images could be 'users/{user_id}/profile'
                new_image_path = upload_file_to_supabase(
                    profile_image_file, 
                    bucket_name='profile_images', 
                    folder_path=f'users/{user.id}/profile',
                    user_id=user.id
                )
                user.profile_image_url = new_image_path
            except Exception as e:
                current_app.logger.error(f"Failed to upload profile image for user {user.id}: {e}", exc_info=True)
                return jsonify({"message": f"Failed to upload profile image: {str(e)}"}), 500
        else:
            # If an empty file input is sent, it might mean user wants to remove image
            if user.profile_image_url:
                delete_file_async(user.profile_image_url)
                user.profile_image_url = None

    afg_db.session.commit()

    return jsonify({
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "bio": user.bio,
        "profile_image_url": get_signed_url(user.profile_image_url, 'profile_images') if user.profile_image_url else None
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required() # This decorator ensures only authenticated users can access this route
def get_current_user():
    """
    Retrieves the profile of the currently authenticated user.
    """
    current_user_id = get_jwt_identity() # Get the user_id from the JWT payload
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    # Return relevant user data (avoid sending sensitive info like password_hash)
    return jsonify({
        "id": user.id,
        "email": user.email,
        "name": user.name, # Include name
        "bio": user.bio, # Include bio
        "profile_image_url": get_signed_url(user.profile_image_url, 'profile_images') if user.profile_image_url else None, # Include signed URL for image
        "is_verified": user.is_verified
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True) # Requires a valid refresh token
def refresh_token():
    """
    Endpoint for refreshing an access token using a refresh token.
    Implements refresh token rotation and blacklisting of the old refresh token.
    """
    current_user_id = get_jwt_identity()
    jti = get_jwt()["jti"] # Get JTI of the current refresh token

    # Blacklist the old refresh token
    # The token will be valid until its natural expiration, but cannot be used again
    # to generate new access tokens.
    try:
        # Get the expiration time of the current refresh token
        # This is important so the blacklist entry expires at the same time as the token would have
        from datetime import datetime, timezone
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        # Calculate remaining seconds
        expires_in = (target_timestamp - now).total_seconds()

        if expires_in > 0:
            jwt_redis_blocklist.setex(jti, int(expires_in), "true")
            current_app.logger.info(f"Blacklisted old refresh token JTI: {jti}")
        else:
            current_app.logger.warning(f"Refresh token JTI {jti} already expired, not blacklisting.")

    except Exception as e:
        current_app.logger.error(f"Error blacklisting refresh token {jti}: {e}", exc_info=True)
        return jsonify({"message": "Error processing refresh token"}), 500

    # Generate a new access token and a new refresh token
    new_access_token = create_access_token(identity=current_user_id)
    new_refresh_token = create_refresh_token(identity=current_user_id)

    return jsonify(
        access_token=new_access_token,
        refresh_token=new_refresh_token
    ), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required() # Requires a valid access token to logout
def logout_user():
    """Endpoint for logging out a user by blacklisting their access token."""
    jti = get_jwt()["jti"] # Get JTI of the current access token
    token_type = get_jwt()["type"]

    # Blacklist the access token
    # The token will be valid until its natural expiration, but cannot be used again
    # to access protected routes.
    try:
        from datetime import datetime, timezone
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        expires_in = (target_timestamp - now).total_seconds()

        if expires_in > 0:
            jwt_redis_blocklist.setex(jti, int(expires_in), "true")
            current_app.logger.info(f"Blacklisted {token_type} token JTI: {jti}")
        else:
            current_app.logger.warning(f"{token_type} token JTI {jti} already expired, not blacklisting.")

        # Note: For a complete logout, if the client also holds a refresh token,
        # it should ideally send that to be blacklisted as well, or the server
        # should manage the association. This logout only blacklists the token
        # used to call this endpoint (typically an access token).

        return jsonify({"message": f"{token_type.capitalize()} token revoked successfully"}), 200
    except Exception as e:
        current_app.logger.error(f"Error blacklisting token {jti}: {e}", exc_info=True)
        return jsonify({"message": "Error revoking token"}), 500

@auth_bp.route('/resend-otp', methods=['POST'])
@limiter.limit("1 per minute", key_func=get_email_from_request, error_message="Too many OTP resend requests for this email. Please wait a minute.")
@limiter.limit("5 per hour", key_func=get_remote_address, error_message="Too many OTP resend requests from this IP. Please try again later.")
def resend_otp():
    data = request.get_json()
    email = data.get('email')
    purpose = data.get('purpose') # e.g., 'registration', 'password_reset'

    if not email or not purpose:
        return jsonify({"message": "Email and purpose are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        # For security, always return a generic message even if user not found
        return jsonify({"message": "If an account with that email exists, a new OTP has been sent."}), 200

    # Check if the user is currently locked out for this purpose
    failed_attempts = get_failed_otp_attempts(user.id, purpose)
    if failed_attempts >= MAX_FAILED_OTP_ATTEMPTS:
        return jsonify({
            "message": f"Too many failed OTP attempts. Please wait {OTP_LOCKOUT_SECONDS // 60} minutes before requesting a new OTP."
        }), 429

    # Generate a new OTP
    otp_code = generate_secure_otp(length=6)

    # Store the new OTP (this will overwrite any existing one for this user/purpose)
    if not store_otp(user.id, otp_code, purpose=purpose):
        current_app.logger.error(f"Failed to store new OTP for user {user.id} for purpose {purpose}")
        return jsonify({"message": "Failed to resend OTP. Please try again."}), 500

    send_otp_email(user_email=user.email, user_name=user.email, otp_code=otp_code) # Use email as name if no name field
    current_app.logger.info(f"New OTP sent to {user.email} for {purpose}.")

    return jsonify({"message": "If an account with that email exists, a new OTP has been sent."}), 200