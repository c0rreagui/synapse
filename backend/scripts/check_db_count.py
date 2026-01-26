import sys
import os
from sqlalchemy import create_engine, text

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.database import SessionLocal
from core.models import Profile, ScheduleItem

def check_counts():
    db = SessionLocal()
    try:
        profile_count = db.query(Profile).count()
        schedule_count = db.query(ScheduleItem).count()
        
        print(f"Profiles count: {profile_count}")
        print(f"Schedule items count: {schedule_count}")
        
        if profile_count > 0:
            print("--- Profiles ---")
            profiles = db.query(Profile).all()
            for p in profiles:
                print(f"ID: {p.id}, Slug: {p.slug}, Label: {p.label}, Active: {p.active}")

        if schedule_count > 0:
            print("--- Schedule Items ---")
            schedule_items = db.query(ScheduleItem).all()
            for s in schedule_items:
                print(f"ID: {s.id}, Profile ID: {s.profile_id}, Day: {s.day_of_week}, Start: {s.start_time}, End: {s.end_time}")
                
    except Exception as e:
        print(f"Error checking DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_counts()
