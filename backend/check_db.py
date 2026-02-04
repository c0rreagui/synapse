import sys
import os
import json

# Add current directory to path
sys.path.append(os.getcwd())

from core.database import SessionLocal
from core.models import Profile

def check_db():
    db = SessionLocal()
    try:
        profiles = db.query(Profile).all()
        print(f"Total Profiles in DB: {len(profiles)}")
        for p in profiles:
            print(f"--- Profile: {p.slug} ---")
            print(f"Label: {p.label}")
            print(f"Username: {p.username}")
            print(f"Avatar URL: {p.avatar_url}")
            print(f"Active: {p.active}")
            print(f"Audit Metadata: {json.dumps(p.last_seo_audit, indent=2)}")
            print("---------------------------")
            
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_db()
