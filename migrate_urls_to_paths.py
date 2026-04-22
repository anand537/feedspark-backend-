import os
from urllib.parse import unquote
from app import create_app
from app.extensions import afg_db
from app.models import Submission

def migrate_public_urls_to_paths():
    """
    Migrates Submission.file_url from full public URLs to relative storage paths.
    Required for switching from Public to Private buckets with Signed URLs.
    """
    # Initialize Flask app context to access the database
    app = create_app()
    
    with app.app_context():
        print("🔄 Starting migration: Public URLs -> Storage Paths")
        
        # Fetch all submissions that have a file_url starting with http
        # This filters out records that are already paths or empty
        submissions = Submission.query.filter(Submission.file_url.like('http%')).all()
        
        if not submissions:
            print("✅ No submissions found with public URLs. Migration not needed.")
            return

        print(f"Found {len(submissions)} submissions with URLs to check...")
        
        updated_count = 0
        bucket_name = "submissions"
        
        # Supabase storage URL pattern usually contains: /storage/v1/object/public/{bucket}/
        # We want to extract everything AFTER the bucket name.
        
        for sub in submissions:
            original_url = sub.file_url
            
            # Check for standard Supabase public URL structure
            # We look for '/public/submissions/' which is standard for public buckets
            marker = f"/public/{bucket_name}/"
            
            if marker in original_url:
                try:
                    # Split the URL at the marker
                    # Example: https://.../public/submissions/assignments/1/file.pdf
                    # Result: assignments/1/file.pdf
                    path_part = original_url.split(marker, 1)[1]
                    
                    # Decode URL encoding (e.g., %20 -> space) to get the actual object key
                    relative_path = unquote(path_part)
                    
                    # Update the record
                    sub.file_url = relative_path
                    updated_count += 1
                    print(f"  [UPDATE] ID {sub.id}: ...{original_url[-30:]} -> {relative_path}")
                    
                except IndexError:
                    print(f"  [SKIP] ID {sub.id}: Could not parse URL format: {original_url}")
            else:
                print(f"  [SKIP] ID {sub.id}: URL does not match Supabase bucket pattern: {original_url}")

        if updated_count > 0:
            print(f"\n💾 Committing changes for {updated_count} records...")
            afg_db.session.commit()
            print("✅ Migration complete! Database now contains relative paths.")
        else:
            print("\nℹ️  No records matched the migration criteria.")

if __name__ == "__main__":
    migrate_public_urls_to_paths()