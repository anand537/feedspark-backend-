from datetime import datetime, timedelta
import io
import csv
from app import create_app
from app.extensions import afg_db
from app.models import Meeting, MeetingParticipant, User
from app.utils.email_utils import send_attendance_report_email, send_absent_notification_email

def process_attendance():
    """
    Background job to mark students as 'absent' if they didn't join
    by the time the meeting ended.
    """
    app = create_app()
    
    with app.app_context():
        now = datetime.utcnow()
        print(f"[{now}] Checking for ended meetings to process attendance...")
        
        # Find meetings that started in the past and haven't been processed yet
        candidates = Meeting.query.filter(
            Meeting.attendance_processed == False,
            Meeting.scheduled_at < now
        ).all()
        
        count = 0
        for meeting in candidates:
            # Calculate end time with a 15-minute buffer for late joins
            end_time = meeting.scheduled_at + timedelta(minutes=meeting.duration + 15)
            
            if now > end_time:
                print(f"Processing meeting ID {meeting.id}: '{meeting.title}'")
                
                participants = MeetingParticipant.query.filter_by(meeting_id=meeting.id).all()
                attendance_data = []

                for p in participants:
                    student = User.query.get(p.user_id)
                    
                    # If they haven't joined (or explicitly marked present), mark as absent
                    if not p.joined_at and p.status == 'pending':
                        p.status = 'absent'
                        # Notify student about absence
                        if student and student.email:
                            try:
                                send_absent_notification_email(student.email, student.name, meeting.title, meeting.scheduled_at.strftime('%Y-%m-%d %H:%M'))
                                print(f"   -> Sent absence notification to {student.email}")
                            except Exception as e:
                                print(f"   -> Failed to send absence email: {e}")
                    
                    # Collect data for report
                    attendance_data.append({
                        'name': student.name if student else "Unknown",
                        'email': student.email if student else "Unknown",
                        'status': p.status,
                        'joined_at': p.joined_at.strftime('%Y-%m-%d %H:%M:%S') if p.joined_at else "Not Joined"
                    })
                
                # Send email to mentor
                mentor = User.query.get(meeting.created_by)
                if mentor and mentor.email:
                    try:
                        si = io.StringIO()
                        cw = csv.writer(si)
                        cw.writerow(['Name', 'Email', 'Status', 'Joined At'])
                        for row in attendance_data:
                            cw.writerow([row['name'], row['email'], row['status'], row['joined_at']])
                        
                        send_attendance_report_email(mentor.email, mentor.name, meeting.title, meeting.scheduled_at.strftime('%Y-%m-%d %H:%M'), si.getvalue())
                        print(f"   -> Sent attendance report to {mentor.email}")
                    except Exception as e:
                        print(f"   -> Failed to send report: {e}")

                meeting.attendance_processed = True
                meeting.status = 'completed' # Auto-complete the meeting status
                count += 1
        
        if count > 0:
            afg_db.session.commit()
            print(f"✅ Successfully processed attendance for {count} meetings.")
        else:
            print("No meetings ready for processing.")

if __name__ == "__main__":
    process_attendance()