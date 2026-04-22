import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from flask import render_template, current_app
import threading # Import datetime and timedelta
from app.utils.auth_utils import generate_secure_otp # Import from new auth_utils
from datetime import datetime, timedelta

def send_async_email(app, message):
    """Send email asynchronously using Gmail SMTP"""
    with app.app_context():
        try:
            # Connect to Gmail's SMTP server
            print("Connecting to Gmail server...")
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()  # Upgrade the connection to secure

            # Login and Send
            server.login(app.config['GMAIL_USER'], app.config['GMAIL_PASS'])
            print("Login successful!")

            server.send_message(message)
            print(f"Email sent successfully to {message['To']}!")

            server.quit()

        except Exception as e:
            print(f"Error: {e}")

def send_email(subject, recipients, template, attachments=None, **kwargs):
    """Send email using Gmail SMTP with template"""
    # Use current_app if available, otherwise create new app instance
    try:
        app = current_app._get_current_object()
    except RuntimeError:
        from app import create_app
        app = create_app()

    # Check if Gmail is configured
    if not app.config.get('GMAIL_USER') or not app.config.get('GMAIL_PASS'):
        print("Email not configured - skipping email send")
        return

    # Setup the email headers
    message = MIMEMultipart()
    message["From"] = app.config['GMAIL_USER']
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject

    # Add the body HTML from template
    html = render_template(template, **kwargs)
    message.attach(MIMEText(html, "html"))

    # Add attachments if provided
    if attachments:
        for filename, content_type, data in attachments:
            main_type, sub_type = content_type.split('/', 1)
            part = MIMEBase(main_type, sub_type)
            part.set_payload(data)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            message.attach(part)

    # Send email asynchronously to avoid blocking
    thread = threading.Thread(target=send_async_email, args=(app, message))
    thread.start()

def send_welcome_email(user_email, user_name, password=None):
    """Send welcome email to new user"""
    send_email(
        subject="Welcome to Auto Feedback Generator!",
        recipients=[user_email],
        template="emails/welcome.html",
        user_name=user_name,
        password=password
    )

def send_verification_email(user_email, token):
    """Send email verification link"""
    send_email(
        subject="Verify Your Email",
        recipients=[user_email],
        template="emails/verify_email.html",
        token=token
    )

def send_feedback_notification_email(mentor_email, mentor_name, student_name, assignment_title):
    """Send notification to mentor when feedback is ready"""
    send_email(
        subject="New Feedback Available for Review",
        recipients=[mentor_email],
        template="emails/feedback_notification.html",
        mentor_name=mentor_name,
        student_name=student_name,
        assignment_title=assignment_title
    )

def send_submission_confirmation_email(student_email, student_name, assignment_title):
    """Send confirmation to student when submission is received"""
    send_email(
        subject="Submission Received Successfully",
        recipients=[student_email],
        template="emails/submission_confirmation.html",
        student_name=student_name,
        assignment_title=assignment_title
    )

def send_password_reset_email(user_email, reset_token):
    """Send password reset email"""
    send_email(
        subject="Password Reset Request",
        recipients=[user_email],
        template="emails/password_reset.html",
        reset_token=reset_token
    )

def send_generic_notification_email(user_email, user_name, title, message):
    """Send a generic notification email"""
    send_email(
        subject=title,
        recipients=[user_email],
        template="emails/generic_notification.html",
        user_name=user_name,
        notification_title=title,
        notification_message=message
    )

def send_attendance_report_email(mentor_email, mentor_name, meeting_title, meeting_date, csv_content):
    """Send attendance report with CSV attachment"""
    send_email(
        subject=f"Attendance Report: {meeting_title}",
        recipients=[mentor_email],
        template="emails/attendance_report.html",
        mentor_name=mentor_name,
        meeting_title=meeting_title,
        meeting_date=meeting_date,
        attachments=[(f"attendance_report.csv", "text/csv", csv_content)]
    )

def send_absent_notification_email(student_email, student_name, meeting_title, meeting_date):
    """Send notification to student marked as absent"""
    send_email(
        subject=f"Absence Recorded: {meeting_title}",
        recipients=[student_email],
        template="emails/absent_notification.html",
        student_name=student_name,
        meeting_title=meeting_title,
        meeting_date=meeting_date
    )

def send_otp_email(user_email, user_name, otp_code):
    """Send OTP email for verification"""
    # Calculate expiration time for the email template
    otp_expiration_seconds = current_app.config.get('OTP_EXPIRATION_SECONDS', 300) # Default to 300 seconds (5 minutes)
    expiration_minutes = otp_expiration_seconds // 60
    send_email(
        subject="Your One-Time Password",
        recipients=[user_email],
        template="emails/otp.html",
        user_name=user_name,
        otp_code=otp_code,
        expiration_minutes=expiration_minutes, # Pass expiration minutes to template
        current_year=datetime.now().year # Pass current year for footer
    )
