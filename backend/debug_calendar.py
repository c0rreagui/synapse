
import os
import sys
from sqlalchemy import text

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from core.models import ScheduleItem, Profile

def check_calendar():
    db = SessionLocal()
    print(f"DB URL: {db.bind.url}")
    print("--- CHECKING PROFILES ---")
    
    profiles = db.query(Profile).all()
    print(f"Total Profiles: {len(profiles)}")
    
    for p in profiles:
        print(f"Slug: {p.slug} | Label: {p.label} | Active: {p.active}")
        
        if not p.active:
            print(f"--> Re-activating profile {p.slug}...")
            p.active = True
            db.commit()
            print("    [DONE] Set active=True")

    print("All profiles checked.")

if __name__ == "__main__":
    check_calendar()
