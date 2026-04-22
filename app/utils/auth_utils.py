import secrets
import string
from datetime import datetime, timedelta
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import redis_client

# Configuration for dynamic OTP rate limiting
MAX_FAILED_OTP_ATTEMPTS = 5 # Max attempts before lockout
OTP_LOCKOUT_SECONDS = 900   # 15 minutes lockout

# Configuration for dynamic Password rate limiting
MAX_FAILED_PASSWORD_ATTEMPTS = 5 # Max attempts before lockout
PASSWORD_LOCKOUT_SECONDS = 900   # 15 minutes lockout

# Configuration for dynamic Password rate limiting
MAX_FAILED_PASSWORD_ATTEMPTS = 5 # Max attempts before lockout
PASSWORD_LOCKOUT_SECONDS = 900   # 15 minutes lockout


def generate_secure_otp(length=6, alphanumeric=False):
    """
    Generates a cryptographically secure random OTP.
    """
    if alphanumeric:
        characters = string.ascii_uppercase + string.digits
    else:
        characters = string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def store_otp(user_id: int, otp_code: str, purpose: str = "verification", expiration_seconds: int = None) -> bool:
    """
    Stores a hashed OTP in Redis with an expiration.
    The key format is 'otp:{user_id}:{purpose}'.
    """
    if expiration_seconds is None:
        expiration_seconds = current_app.config.get('OTP_EXPIRATION_SECONDS', 300)

    # Hash the OTP before storing it
    hashed_otp = generate_password_hash(otp_code)
    
    redis_key = f"otp:{user_id}:{purpose}"
    try:
        redis_client.setex(redis_key, expiration_seconds, hashed_otp)
        return True
    except Exception as e:
        current_app.logger.error(f"Error storing OTP for user {user_id}: {e}")
        return False

def verify_otp(user_id: int, purpose: str, submitted_otp: str) -> bool:
    """
    Verifies a submitted OTP against the stored hash in Redis.
    Invalidates the OTP after a successful or failed attempt (to prevent replay attacks).
    """
    redis_key = f"otp:{user_id}:{purpose}"
    stored_hashed_otp = redis_client.get(redis_key)

    if not stored_hashed_otp:
        # OTP not found or expired
        return False

    # Invalidate the OTP immediately to ensure single-use
    redis_client.delete(redis_key)

    # Check the submitted OTP against the stored hash
    if check_password_hash(stored_hashed_otp.decode('utf-8'), submitted_otp):
        return True
    else:
        return False

def increment_failed_otp_attempt(user_id: int, purpose: str):
    """
    Increments the failed OTP attempt counter for a user and purpose.
    Sets an expiration for the counter if it's the first attempt.
    """
    key = f"failed_otp_attempts:{user_id}:{purpose}"
    try:
        # Increment the counter
        attempts = redis_client.incr(key)
        
        # Set expiration if it's the first attempt, or if it was reset
        if attempts == 1:
            redis_client.expire(key, OTP_LOCKOUT_SECONDS) # Counter expires after lockout period
        
        current_app.logger.warning(f"User {user_id} failed OTP attempt for {purpose}. Attempts: {attempts}")
        return attempts
    except Exception as e:
        current_app.logger.error(f"Error incrementing failed OTP attempts for user {user_id}: {e}")
        return -1 # Indicate error

def get_failed_otp_attempts(user_id: int, purpose: str) -> int:
    """Retrieves the current number of failed OTP attempts for a user and purpose."""
    key = f"failed_otp_attempts:{user_id}:{purpose}"
    attempts = redis_client.get(key)
    return int(attempts) if attempts else 0

def reset_failed_otp_attempts(user_id: int, purpose: str):
    """Resets the failed OTP attempt counter for a user and purpose."""
    key = f"failed_otp_attempts:{user_id}:{purpose}"
    redis_client.delete(key)
    current_app.logger.info(f"Reset failed OTP attempts for user {user_id} and {purpose}.")

def increment_failed_password_attempt(user_id: int):
    """
    Increments the failed password attempt counter for a user.
    Sets an expiration for the counter if it's the first attempt.
    """
    key = f"failed_password_attempts:{user_id}"
    try:
        # Increment the counter
        attempts = redis_client.incr(key)
        
        # Set expiration if it's the first attempt, or if it was reset
        if attempts == 1:
            redis_client.expire(key, PASSWORD_LOCKOUT_SECONDS) # Counter expires after lockout period
        
        current_app.logger.warning(f"User {user_id} failed password attempt. Attempts: {attempts}")
        return attempts
    except Exception as e:
        current_app.logger.error(f"Error incrementing failed password attempts for user {user_id}: {e}")
        return -1 # Indicate error

def get_failed_password_attempts(user_id: int) -> int:
    """Retrieves the current number of failed password attempts for a user."""
    key = f"failed_password_attempts:{user_id}"
    attempts = redis_client.get(key)
    return int(attempts) if attempts else 0

def reset_failed_password_attempts(user_id: int):
    """Resets the failed password attempt counter for a user."""
    key = f"failed_password_attempts:{user_id}"
    redis_client.delete(key)
    current_app.logger.info(f"Reset failed password attempts for user {user_id}.")

def increment_failed_password_attempt(user_id: int):
    """
    Increments the failed password attempt counter for a user.
    Sets an expiration for the counter if it's the first attempt.
    """
    key = f"failed_password_attempts:{user_id}"
    try:
        # Increment the counter
        attempts = redis_client.incr(key)
        
        # Set expiration if it's the first attempt, or if it was reset
        if attempts == 1:
            redis_client.expire(key, PASSWORD_LOCKOUT_SECONDS) # Counter expires after lockout period
        
        current_app.logger.warning(f"User {user_id} failed password attempt. Attempts: {attempts}")
        return attempts
    except Exception as e:
        current_app.logger.error(f"Error incrementing failed password attempts for user {user_id}: {e}")
        return -1 # Indicate error

def get_failed_password_attempts(user_id: int) -> int:
    """Retrieves the current number of failed password attempts for a user."""
    key = f"failed_password_attempts:{user_id}"
    attempts = redis_client.get(key)
    return int(attempts) if attempts else 0

def reset_failed_password_attempts(user_id: int):
    """Resets the failed password attempt counter for a user."""
    key = f"failed_password_attempts:{user_id}"
    redis_client.delete(key)
    current_app.logger.info(f"Reset failed password attempts for user {user_id}.")