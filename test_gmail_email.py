#!/usr/bin/env python3
"""
Test Gmail SMTP Email Functionality
====================================
Test script to verify Gmail SMTP integration in email_utils.py

Run this script to test email sending:
    python test_gmail_email.py
"""

import os
import sys
from dotenv import load_dotenv
from app import create_app  # Assuming 'app' is the Flask app instance
from app.utils.email_utils import send_welcome_email, send_verification_email, send_otp_email
from app.utils.auth_utils import generate_secure_otp # Import from new auth_utils
import logging

# Load environment variables from .env file
load_dotenv()

# Configure basic logging for the test script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_gmail_email():
    """Test Gmail SMTP email sending"""
    app = create_app()

    with app.app_context():
        # Check Gmail configuration
        gmail_user = app.config.get('GMAIL_USER')
        gmail_pass = app.config.get('GMAIL_PASS')

        if not gmail_user or not gmail_pass:
            logging.error("GMAIL_USER or GMAIL_PASS not set in .env file")
            logging.info("Please set GMAIL_USER and GMAIL_PASS in your .env file")
            logging.info("GMAIL_USER should be your Gmail address")
            logging.info("GMAIL_PASS should be your 16-character App Password (not regular password)")
            return False

        logging.info(f"Gmail user: {gmail_user}")
        logging.info("Gmail password: [HIDDEN]")

        # Test recipient - change this to a real email you can check
        test_recipient = "anandkverma2104@gmail.com"  # Replace with your test email

        if test_recipient == "your_test_recipient@example.com":
            logging.warning("Please change 'your_test_recipient@example.com' to a real email address")
            return False

        try:
            logging.info(f"Sending test welcome email to {test_recipient}...")

            # Test send_welcome_email
            send_welcome_email(
                user_email=test_recipient,
                user_name="Test User",
                password="testpassword123"
            )

            logging.info("Welcome email sent successfully!")

            # Wait a moment, then test verification email
            import time
            time.sleep(2)

            logging.info(f"Sending test verification email to {test_recipient}...")

            # Test send_verification_email
            send_verification_email(
                user_email=test_recipient,
                token="test-verification-token-123"
            )

            logging.info("Verification email sent successfully!")

            # Wait a moment, then test OTP email
            import time
            time.sleep(2)

            # Generate a secure OTP for testing purposes
            generated_otp = generate_secure_otp(length=6) # You can adjust length and alphanumeric
            logging.info(f"Sending test OTP email to {test_recipient}...")

            # Test send_otp_email
            send_otp_email(
                user_email=test_recipient,
                user_name="Test User",
                otp_code=generated_otp
            )

            logging.info("OTP email sent successfully!")
            logging.info("Check your email inbox (and spam folder) for the test emails.")
            return True

        except Exception as e:
            logging.error(f"Failed to send test email: {e}", exc_info=True)
            return False

if __name__ == "__main__":
    success = test_gmail_email()
    sys.exit(0 if success else 1)
