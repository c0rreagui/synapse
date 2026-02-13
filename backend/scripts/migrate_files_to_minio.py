
import os
import sys
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.storage import s3_storage
from core.database import SessionLocal
from core.models import ScheduleItem

# Directories to migrate
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIRS = [
    os.path.join(BASE_DIR, "data", "approved"),
    os.path.join(BASE_DIR, "done"),
    os.path.join(BASE_DIR, "errors"),
]

def migrate_files():
    print("--- STARTING MIGRATION: Local Files -> MinIO ---")
    
    # 1. Scan Directories
    files_to_move = []
    for d in DATA_DIRS:
        if os.path.exists(d):
            print(f"Scanning {d}...")
            for root, dirs, files in os.walk(d):
                for file in files:
                    if file.endswith((".mp4", ".json", ".png", ".jpg")):
                        files_to_move.append(os.path.join(root, file))
    
    print(f"Found {len(files_to_move)} files to migrate.")
    
    # 2. Upload to MinIO
    migrated_map = {} # old_path -> new_s3_uri
    
    for local_path in files_to_move:
        try:
            filename = os.path.basename(local_path)
            # Use specific folder in bucket based on source dir?
            # For simplicity, flat or date-based. 
            # Let's use 'archive/' for done, 'queue/' for approved.
            
            prefix = "misc"
            if "approved" in local_path: prefix = "queue"
            if "done" in local_path: prefix = "archive"
            
            s3_key = f"{prefix}/{filename}"
            print(f"Uploading {filename} -> {s3_key}...")
            
            s3_storage.upload_file(local_path, s3_key)
            
            s3_uri = f"s3://{s3_storage.bucket}/{s3_key}"
            migrated_map[local_path] = s3_uri
            
        except Exception as e:
            print(f"Failed to upload {local_path}: {e}")

    # 3. Update Database Records
    print("Updating Database Records...")
    db = SessionLocal()
    try:
        items = db.query(ScheduleItem).all()
        updates = 0
        for item in items:
            if item.video_path and os.path.exists(item.video_path):
                # Try to find exact match
                # Normalize path separators
                p = os.path.abspath(item.video_path)
                
                # Check if we migrated this specific file
                # Since files_to_move contains absolute paths
                if p in migrated_map:
                    item.video_path = migrated_map[p]
                    updates += 1
                else:
                    # Fallback: check basenames
                    # If we migrated a file with same basename, maybe safe to update?
                    # Safer to only update exact matches.
                    pass
        
        db.commit()
        print(f"Updated {updates} DB records to S3 URIs.")
        
    except Exception as e:
        print(f"DB Update Failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_files()
