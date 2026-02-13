from core.database import SessionLocal
from core.models import ScheduleItem

db = SessionLocal()
item = db.query(ScheduleItem).filter(ScheduleItem.id == 31).first()

if item:
    print(f"Current Status: {item.status}")
    item.status = 'failed'
    item.error_message = "Manual Reset for Browser Test"
    db.commit()
    print("Reset item 31 to 'failed' status.")
else:
    print("Item 31 not found.")

db.close()
