
import os
import sys
from datetime import datetime, timedelta

# Setup paths
sys.path.append(os.path.join(os.getcwd(), "backend"))

from core.database import SessionLocal
from core.models import ScheduleItem

def check_dupes():
    db = SessionLocal()
    try:
        # Get items from the last 24 hours (approx by ID or just last 50)
        items = db.query(ScheduleItem).order_by(ScheduleItem.id.desc()).limit(50).all()
        
        print(f"Found {len(items)} items (Last 50):")
        for item in items:
            print(f"ID: {item.id} | Profile: {item.profile_slug} | Time: {item.scheduled_time} | Status: {item.status} | Path: {os.path.basename(item.video_path)}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_dupes()
