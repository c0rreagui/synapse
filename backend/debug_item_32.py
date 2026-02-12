from core.database import SessionLocal
from core.models import ScheduleItem
import os

db = SessionLocal()
item = db.query(ScheduleItem).filter(ScheduleItem.id == 32).first()

if item:
    print(f"ID: {item.id}")
    print(f"Video Path (DB): {item.video_path}")
    print(f"File Exists? {os.path.exists(item.video_path)}")
else:
    print("Item 32 not found")

db.close()
