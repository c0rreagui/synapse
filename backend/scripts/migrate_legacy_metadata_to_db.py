import os
import sys
import json

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from core.models import Profile

def migrate_metadata():
    db = SessionLocal()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    profiles_file = os.path.join(base_dir, "data", "profiles.json")
    
    if not os.path.exists(profiles_file):
        print(f"Profiles file not found: {profiles_file}")
        return

    print(f"Reading legacy metadata from: {profiles_file}")
    
    try:
        with open(profiles_file, 'r', encoding='utf-8') as f:
            legacy_data = json.load(f)
            
        count = 0
        for slug, data in legacy_data.items():
            print(f"Processing {slug}...")
            
            # Find profile in DB
            profile = db.query(Profile).filter(Profile.slug == slug).first()
            if not profile:
                print(f"  -> Profile {slug} not found in DB (creating placeholders first if needed)")
                # Iterate logic: if migration 1 ran, it should be there.
                # If not, we could create it here too, but let's assume existence for update focus
                continue
                
            # Update fields
            if "avatar_url" in data:
                profile.avatar_url = data["avatar_url"]
            if "username" in data:
                profile.username = data["username"]
            if "bio" in data:
                profile.bio = data["bio"]
            if "oracle_best_times" in data:
                profile.oracle_best_times = data["oracle_best_times"]
            if "last_seo_audit" in data:
                profile.last_seo_audit = data["last_seo_audit"]
            if "icon" in data:
                profile.icon = data["icon"]
            if "label" in data:
                profile.label = data["label"]
            if "type" in data:
                profile.type = data["type"]
                
            print(f"  -> Updated metadata for {slug}")
            count += 1
            
        db.commit()
        print(f"Successfully updated metadata for {count} profiles.")
        
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate_metadata()
