import os
import sys
import json
import glob

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from core.models import Profile

def migrate_sessions():
    db = SessionLocal()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sessions_dir = os.path.join(base_dir, "data", "sessions")
    
    print(f"Scanning for sessions in: {sessions_dir}")
    
    json_files = glob.glob(os.path.join(sessions_dir, "*.json"))
    print(f"Found {len(json_files)} session files.")
    
    count = 0
    for file_path in json_files:
        try:
            filename = os.path.basename(file_path)
            slug = os.path.splitext(filename)[0]
            
            # Check if exists
            existing = db.query(Profile).filter(Profile.slug == slug).first()
            if existing:
                print(f"Skipping {slug} (already in DB)")
                continue
                
            # Determine label/type based on filename heuristics
            label = slug
            p_type = "imported"
            icon = "👤"
            
            if "profile_01" in slug:
                label = "Cortes Virais"
                p_type = "cuts"
                icon = "✂️"
            elif "profile_02" in slug:
                label = "Main Account"
                p_type = "main"
                icon = "🔥"
            
            new_profile = Profile(
                slug=slug,
                label=label,
                username=None, # Will need validation
                icon=icon,
                type=p_type,
                active=True
            )
            
            db.add(new_profile)
            print(f"Migrating {slug}...")
            count += 1
            
        except Exception as e:
            print(f"Error migrating {file_path}: {e}")
            
    try:
        db.commit()
        print(f"Successfully migrated {count} profiles.")
    except Exception as e:
        db.rollback()
        print(f"DB Commit Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate_sessions()
