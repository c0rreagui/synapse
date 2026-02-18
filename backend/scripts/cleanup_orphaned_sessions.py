import sys
import os
import shutil

# [HARDENING] Unified Environment Loader
import script_env
script_env.setup_script_env()

from core.database import SessionLocal
from core.models import Profile

def cleanup_orphans():
    print("🧹 Starting Orphaned Session Cleanup...")
    
    # 1. Get valid IDs from DB
    db = SessionLocal()
    profiles = db.query(Profile).all()
    valid_slugs = {p.slug for p in profiles}
    db.close()
    
    print(f"✅ Found {len(valid_slugs)} valid profiles in DB: {valid_slugs}")
    
    # 2. Check filesystem
    sessions_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sessions")
    if not os.path.exists(sessions_dir):
        print("Folder not found.")
        return

    orphans = []
    for filename in os.listdir(sessions_dir):
        if filename.endswith(".json"):
            slug = filename.replace(".json", "")
            if slug not in valid_slugs:
                orphans.append(filename)
    
    if not orphans:
        print("✨ No orphaned sessions found.")
        return

    print(f"⚠️ Found {len(orphans)} orphaned session files: {orphans}")
    
    # 3. Move orphans to backup
    backup_dir = os.path.join(sessions_dir, "orphaned_backup")
    os.makedirs(backup_dir, exist_ok=True)
    
    for orphan in orphans:
        src = os.path.join(sessions_dir, orphan)
        dst = os.path.join(backup_dir, orphan)
        shutil.move(src, dst)
        print(f"Moved {orphan} -> {dst}")
        
    print("🧹 Cleanup complete.")

if __name__ == "__main__":
    cleanup_orphans()
