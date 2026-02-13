from core.database import SessionLocal
from core.models import ScheduleItem

db = SessionLocal()
items = db.query(ScheduleItem).filter(ScheduleItem.status == 'pending').all()
print(f"Pending Items Count: {len(items)}")
for item in items:
    print(f"ID: {item.id} | Profile: {item.profile_slug} | Time: {item.scheduled_time}")
db.close()
