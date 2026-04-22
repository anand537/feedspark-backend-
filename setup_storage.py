import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_storage():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
        return

    print(f"Connecting to Supabase at {url}...")
    supabase = create_client(url, key)
    bucket_name = "submissions"

    try:
        # Try to update existing bucket to be private
        print(f"Configuring bucket '{bucket_name}' to be private...")
        supabase.storage.update_bucket(bucket_name, options={"public": False})
        print("✅ Bucket updated to private!")
    except Exception as e:
        try:
            # If update failed (likely doesn't exist), create it as private
            supabase.storage.create_bucket(bucket_name, options={"public": False})
            print("✅ Private bucket created successfully!")
        except Exception as create_error:
            print(f"ℹ️  Note: {str(create_error)}")

if __name__ == "__main__":
    setup_storage()