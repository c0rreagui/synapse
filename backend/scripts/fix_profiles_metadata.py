
import sys
import os

# [HARDENING] Unified Environment Loader
import script_env
script_env.setup_script_env()

import json
import sqlite3

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import DATA_DIR, SESSIONS_DIR
from core.database import SessionLocal
from core.models import Profile

def update_json(slug, new_meta):
    path = os.path.join(SESSIONS_DIR, f"{slug}.json")
    if not os.path.exists(path):
        print(f"❌ Session file not found: {path}")
        return

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if "synapse_meta" not in data:
            data["synapse_meta"] = {}
            
        # Update meta
        for k, v in new_meta.items():
            data["synapse_meta"][k] = v
            
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"Updated JSON for {slug}")
    except Exception as e:
        print(f"Error updating JSON {slug}: {e}")

def fix_profiles():
    db = SessionLocal()
    try:
        # 1. Vibe Cortes
        slug_vc = "tiktok_profile_1770135259969"
        vc = db.query(Profile).filter(Profile.slug == slug_vc).first()
        if vc:
            vc.active = True
            vc.username = "vibe.corteseclips"
            vc.label = "Vibe Cortes"
            print(f"DB Updated: Vibe Cortes -> Active, vibe.corteseclips")
            
            update_json(slug_vc, {
                "display_name": "Vibe Cortes", 
                "username": "vibe.corteseclips"
            })
        else:
            print(f"Profile not found in DB: {slug_vc}")

        # 2. Opinião Viral
        slug_ov = "tiktok_profile_1770307556827"
        ov = db.query(Profile).filter(Profile.slug == slug_ov).first()
        if ov:
            ov.active = True
            ov.username = "opiniaoviral"
            ov.label = "Opinião Viral"
            print(f"DB Updated: Opinião Viral -> Active, opiniaoviral")
            
            update_json(slug_ov, {
                "display_name": "Opinião Viral", 
                "username": "opiniaoviral"
            })
        else:
            print(f"Profile not found in DB: {slug_ov}")

        db.commit()
        print("DB Changes Committed.")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_profiles()
