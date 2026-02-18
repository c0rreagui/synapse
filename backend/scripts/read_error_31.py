import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.database import SessionLocal
from core.models import ScheduleItem

db = SessionLocal()
item = db.query(ScheduleItem).filter(ScheduleItem.id == 31).first()
if item:
    print(f"ID: {item.id}")
    print(f"Status: {item.status}")
    print(f"Error: {item.error_message}")
else:
    print("Item 31 not found")
db.close()
