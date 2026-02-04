import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.database import SessionLocal
from core.models import ScheduleItem

def list_items():
    db = SessionLocal()
    try:
        items = db.query(ScheduleItem).all()
        print(f"Found {len(items)} items:")
        for i in items:
            print(f"ID: {i.id} | Slug: {i.profile_slug} | Path: {i.video_path} | Time: {i.scheduled_time} | Status: {i.status}")
    except Exception as e:
        print(e)
    finally:
        db.close()

if __name__ == "__main__":
    list_items()
