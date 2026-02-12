import sys
import os
import shutil

# Adjust path to find core modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from core.models import ScheduleItem
from core.config import DATA_DIR, BASE_DIR, APPROVED_DIR, PROCESSING_DIR, DONE_DIR, ERRORS_DIR

PENDING_DIR = os.path.join(DATA_DIR, "pending")

DIRS = {
    "approved": APPROVED_DIR,
    "processing": PROCESSING_DIR,
    "done": DONE_DIR,
    "errors": ERRORS_DIR,
    "pending": PENDING_DIR
}

def restore():
    print(f"=== PLATFORM RESTORE ===")
    db = SessionLocal()
    items = db.query(ScheduleItem).all()
    print(f"Total Database Items: {len(items)}")
    
    updates_count = 0
    restored_files_count = 0
    
    # Pre-scan filesystem to build a map of hash -> file path
    print("Building filesystem index...")
    file_map = {} # hash -> list of full paths
    for name, path in DIRS.items():
        if os.path.exists(path):
            files = os.listdir(path)
            for f in files:
                if not f.endswith('.mp4'): continue # Only care about videos
                
                full_path = os.path.join(path, f)
                parts = os.path.splitext(f)[0].split('_')
                if len(parts) >= 2:
                    file_hash = parts[-1] 
                    # Store by hash because filenames might vary (prefixes)
                    if file_hash not in file_map: file_map[file_hash] = []
                    file_map[file_hash].append(full_path)

    print(f"Indexed {len(file_map)} unique video hashes.")

    for item in items:
        # Extract intent from DB path
        # Expected filename from DB path
        db_filename = os.path.basename(item.video_path) if item.video_path else ""
        
        # Try to find the file
        found_path = None
        
        # 1. Check if path exists as is (unlikely given the /app/data issue)
        if item.video_path and os.path.exists(item.video_path):
            found_path = item.video_path
        
        # 2. Check strict filename match in all dirs
        if not found_path and db_filename:
             for d in DIRS.values():
                 candidate = os.path.join(d, db_filename)
                 if os.path.exists(candidate):
                     found_path = candidate
                     break
        
        # 3. Check hash match
        if not found_path and db_filename:
             parts = os.path.splitext(db_filename)[0].split('_')
             if len(parts) >= 2:
                 fhash = parts[-1]
                 if fhash in file_map:
                     # Pick the best match based on status?
                     # For now just pick the first one found
                     found_path = file_map[fhash][0]

        if found_path:
            # FIX 1: Update DB path if different
            normalized_found = os.path.normpath(found_path)
            normalized_db = os.path.normpath(item.video_path) if item.video_path else ""
            
            if normalized_found != normalized_db:
                print(f"[FIX PATH] Item {item.id}: {item.video_path} -> {normalized_found}")
                item.video_path = normalized_found
                updates_count += 1
            
            # FIX 2: Restore file location based on status
            if item.status in ['pending', 'scheduled', 'approved']:
                current_dir = os.path.dirname(normalized_found)
                # If currently in DONE or ERRORS or PROCESSING, move to APPROVED
                if current_dir == DONE_DIR or current_dir == ERRORS_DIR or current_dir == PROCESSING_DIR:
                    # Target: Approved (ready for pickup)
                    target_path = os.path.join(APPROVED_DIR, os.path.basename(normalized_found))
                    
                    # Move
                    try:
                        shutil.move(normalized_found, target_path)
                        print(f"[RESTORE FILE] Moved {normalized_found} -> {target_path}")
                        item.video_path = target_path
                        restored_files_count += 1
                        updates_count += 1
                    except Exception as e:
                        print(f"[ERROR] Failed to move {normalized_found}: {e}")

        else:
            # Force Fix for /app/data paths even if not found (to correct DB structure)
            if item.video_path and item.video_path.startswith("/app/data/"):
                relative = item.video_path.replace("/app/data/", "").replace("/", os.sep)
                new_path = os.path.join(DATA_DIR, relative)
                print(f"[FORCE FIX PATH] Item {item.id}: {item.video_path} -> {new_path}")
                item.video_path = new_path
                updates_count += 1
            else:
                print(f"[MISSING] Item {item.id} ({item.status}) - File {db_filename} not found.")
            # Verify if it's just a path separator issue
            # If db path starts with /app/data, it might be in D:\APPS...
            # But we searched by HASH, so if it's not in file_map, it's really gone (or no hash).

    db.commit()
    print(f"\n--- DONE ---")
    print(f"Updated DB Paths: {updates_count}")
    print(f"Restored Files to Pipeline: {restored_files_count}")

if __name__ == "__main__":
    restore()
