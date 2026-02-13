from core.database import SessionLocal
from core.models import ScheduleItem

db = SessionLocal()
item = db.query(ScheduleItem).filter(ScheduleItem.id == 52).first()

if item:
    print(f"ID: {item.id}")
    print(f"Status: {item.status}")
    print(f"Path: {item.video_path}")
    print(f"Error: {item.error_message}")
else:
    print("Item 52 not found")

db.close()
