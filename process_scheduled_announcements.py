import time
from datetime import datetime
from app import create_app
from app.extensions import afg_db
from app.models import Announcement
from app.api.announcements import send_announcement_notifications

def process_announcements():
    """
    Check for pending scheduled announcements and send notifications.
    """
    app = create_app()
    
    with app.app_context():
        print(f"[{datetime.utcnow()}] Checking for scheduled announcements...")
        
        # Find announcements that are due but haven't been sent
        pending = Announcement.query.filter(
            Announcement.scheduled_for <= datetime.utcnow(),
            Announcement.notification_sent == False
        ).all()
        
        if not pending:
            print("No pending announcements found.")
            return

        print(f"Found {len(pending)} announcements to process.")
        for announcement in pending:
            print(f"Processing announcement ID {announcement.id}: '{announcement.title}'")
            send_announcement_notifications(announcement)
            announcement.notification_sent = True
            
        afg_db.session.commit()
        print("Done.")

if __name__ == "__main__":
    process_announcements()