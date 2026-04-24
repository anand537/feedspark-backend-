import threading
from urllib.parse import unquote
# from app.extensions import supabase_client  # Removed: using SQLAlchemy
from datetime import datetime

def _delete_worker(file_path):
    """Internal worker to perform the deletion synchronously"""
    if not supabase_client or not file_path:
        return

    try:
        target_path = file_path
        
        # Handle legacy full URLs if they exist in the DB
        if file_path.startswith('http'):
            # Attempt to extract path after bucket name 'submissions'
            # Pattern: .../submissions/assignments/1/file.pdf
            if '/submissions/' in file_path:
                target_path = unquote(file_path.split('/submissions/', 1)[1])
            else:
                print(f"⚠️ Background Job: Could not extract path from URL: {file_path}")
                return

        current_app.logger.info(f"🗑️ Background Job: Deleting '{target_path}' from storage...")
        # Supabase .remove() expects a list of paths
        supabase_client.storage.from_('submissions').remove([target_path])
        
    except Exception as e:
        current_app.logger.error(f"❌ Background Job Error: Failed to delete file {file_path}: {str(e)}")

def delete_file_async(file_path):
    """
    Trigger a background thread to delete a file from Supabase Storage.
    This ensures the API response is not blocked by the external network call.
    """
    from flask import current_app # Import here to avoid circular dependency if called from app context
    if not file_path:
        return

    thread = threading.Thread(target=_delete_worker, args=(file_path,))
    thread.daemon = True  # Daemon threads exit when the main program exits
    thread.start()

def get_signed_url(file_path: str, bucket_name: str, expires_in: int = 3600):
    """Generate a signed URL for a file in Supabase Storage."""
    from flask import current_app # Import here to avoid circular dependency if called from app context
    if not file_path or not supabase_client:
        return None

    # If it starts with http, it's likely already a public URL or signed URL, return as is
    if file_path.startswith('http'):
        return file_path

    try:
        res = supabase_client.storage.from_(bucket_name).create_signed_url(file_path, expires_in)
        return res.get('signedURL') if isinstance(res, dict) else res
    except Exception as e:
        current_app.logger.error(f"Error generating signed URL for {file_path} in bucket {bucket_name}: {e}")
        return None

def upload_file_to_supabase(file, bucket_name: str, folder_path: str, user_id: int = None):
    """Uploads a file to Supabase Storage and returns its path."""
    from flask import current_app # Import here to avoid circular dependency if called from app context
    if not supabase_client or not file:
        return None

    timestamp = int(datetime.utcnow().timestamp())
    # Generate a unique file path: {folder_path}/{user_id}_{timestamp}_{original_filename}
    filename = file.filename
    file_path = f"{folder_path}/{user_id}_{timestamp}_{filename}" if user_id else f"{folder_path}/{timestamp}_{filename}"
    
    supabase_client.storage.from_(bucket_name).upload(file_path, file.read(), {"content-type": file.content_type})
    current_app.logger.info(f"Uploaded file to Supabase: {bucket_name}/{file_path}")
    return file_path