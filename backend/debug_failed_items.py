from core.database import SessionLocal
from core.models import ScheduleItem

db = SessionLocal()
failed_items = db.query(ScheduleItem).filter(ScheduleItem.status == 'failed').order_by(ScheduleItem.id.desc()).limit(5).all()

print(f"Found {len(failed_items)} failed items:")
for item in failed_items:
    print(f"ID: {item.id} | Status: {item.status} | Scheduled: {item.scheduled_time}")
    print(f"Error Message: {item.error_message}")
    print("-" * 50)

db.close()
