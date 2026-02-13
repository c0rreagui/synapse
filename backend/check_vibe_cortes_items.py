from core.database import SessionLocal
from core.models import ScheduleItem

db = SessionLocal()
items = db.query(ScheduleItem).filter(ScheduleItem.profile_slug == "tiktok_profile_1770135259969").all() # Vibe Cortes slug guess or generic query

print(f"Found {len(items)} items for Vibe Cortes")
for i in items:
    print(f"ID: {i.id} | Status: {i.status} | Time: {i.scheduled_time} | Error: {i.error_message}")

db.close()
