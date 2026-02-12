from core.database import SessionLocal
from core.models import ScheduleItem

db = SessionLocal()
items = db.query(ScheduleItem).all()
print(f"Total items: {len(items)}")
for item in items:
    # Check for relevant items
    if "16:29" in str(item.scheduled_time) or item.status == "paused_login_required":
        print(f"ID: {item.id} | Profile: {item.profile_slug} | Time: {item.scheduled_time} | Status: {item.status}")
db.close()
