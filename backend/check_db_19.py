from core.database import SessionLocal
from core.models import ScheduleItem

db = SessionLocal()
# Try finding 19 (can be int or string depending on DB version)
item = db.query(ScheduleItem).filter(ScheduleItem.id == 19).first()

if item:
    print(f"ID: {item.id}")
    print(f"Status: {item.status}")
    print(f"Video Path: {item.video_path}")
    print(f"Scheduled Time: {item.scheduled_time}")
    print(f"Error Message: {item.error_message}")
    print(f"Metadata: {item.metadata_info}")
else:
    print("Item 19 not found check string '19'")
    item_str = db.query(ScheduleItem).filter(ScheduleItem.id == "19").first()
    if item_str:
        print(f"Found as string ID: {item_str.id}")
        print(f"Status: {item_str.status}")
    else:
        print("Item 19 definitely not found")

db.close()
