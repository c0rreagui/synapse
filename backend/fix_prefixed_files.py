
import os
import sys
import glob
import re
from sqlalchemy import text

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from core.models import ScheduleItem
from core.config import DATA_DIR, BASE_DIR

# Directories to search
SEARCH_DIRS = [
    os.path.join(BASE_DIR, "done"),
    os.path.join(DATA_DIR, "approved"),
    os.path.join(DATA_DIR, "pending"),
    os.path.join(BASE_DIR, "errors"),
    os.path.join(BASE_DIR, "processing")
]

def fix_paths():
    print("=== FIXING PREFIXED VIDEO PATHS ===")
    db = SessionLocal()
    
    # 1. Get all items where file is missing
    all_items = db.query(ScheduleItem).all()
    missing_items = []
    
    for item in all_items:
        if item.video_path and not os.path.exists(item.video_path):
            missing_items.append(item)
            
    print(f"Found {len(missing_items)} missing items in DB.")
    
    # 2. Index all available files (with and without prefixes)
    # Map: cleaned_filename -> full_path
    available_files = {}
    
    for d in SEARCH_DIRS:
        if not os.path.exists(d): continue
        
        files = os.listdir(d)
        for f in files:
            if not f.endswith(".mp4"): continue
            
            full_path = os.path.join(d, f)
            
            # Key 1: Exact name
            available_files[f] = full_path
            
            # Key 2: Remove prefix (e.g. 18_filename.mp4 -> filename.mp4)
            # Regex: Start with digits, underscore, then rest
            match = re.match(r"^\d+_(.+)", f)
            if match:
                clean_name = match.group(1)
                available_files[clean_name] = full_path

    print(f"Indexed {len(available_files)} file keys from disk.")

    # 3. Match and Update
    updates = 0
    
    for item in missing_items:
        db_filename = os.path.basename(item.video_path)
        
        if db_filename in available_files:
            new_path = available_files[db_filename]
            
            # Verify it's actually different
            if os.path.normpath(item.video_path) != os.path.normpath(new_path):
                print(f"[FIX] Item {item.id}: {db_filename} -> {os.path.basename(new_path)}")
                print(f"      Path: {new_path}")
                item.video_path = new_path
                updates += 1
        else:
            print(f"[STILL MISSING] Item {item.id}: {db_filename}")

    if updates > 0:
        db.commit()
        print(f"\nSUCCESS: Updated {updates} items.")
    else:
        print("\nNo updates found.")

if __name__ == "__main__":
    fix_paths()
