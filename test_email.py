import os
from dotenv import load_dotenv
from flask_mail import Message
from app import create_app
from app.extensions import mail
import logging

# Load environment variables from .env file
load_dotenv()

# Configure basic logging for the test script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_test_email():
    app = create_app()
    with app.app_context():
        # Retrieve mail configuration from app.config
        mail_server = app.config.get('MAIL_SERVER')
        mail_port = app.config.get('MAIL_PORT')
        mail_use_tls = app.config.get('MAIL_USE_TLS')
        mail_username = app.config.get('MAIL_USERNAME')
        mail_default_sender = app.config.get('MAIL_DEFAULT_SENDER')

        logging.info(f"Mail configuration: Server={mail_server}, Port={mail_port}, TLS={mail_use_tls}, Username={mail_username}, Default Sender={mail_default_sender}")

        if not mail_default_sender:
            logging.error("MAIL_DEFAULT_SENDER is not set in your .env file or config. Please set it to a verified Mailersend sender.")
            return

        # IMPORTANT: Replace with a real email address you can check
        recipient_email = "anandkverma2104@gmail.com" # Ensure this is a real email you can access
        if recipient_email == "your_test_recipient@example.com": # This condition checks against the original placeholder
            logging.warning("Please change 'your_test_recipient@example.com' to a real email address to receive the test email.")
            return

        msg = Message(
            subject="Test Email from Flask App (Mailersend)",
            sender=mail_default_sender,
            recipients=[recipient_email]
        )
        msg.body = "This is a test email sent from your Flask application using Mailersend."
        msg.html = "<h1>Hello from Flask!</h1><p>This is a <strong>test email</strong> sent via Mailersend.</p>"

        try:
            logging.info(f"Attempting to send test email to {recipient_email} from {mail_default_sender}...")
            mail.send(msg)
            logging.info(f"Successfully sent test email to {recipient_email}!")
        except Exception as e:
            logging.error(f"Failed to send test email: {e}", exc_info=True)

if __name__ == "__main__":
    send_test_email()