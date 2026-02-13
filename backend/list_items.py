from core.database import SessionLocal
from core.models import ScheduleItem
from datetime import datetime

db = SessionLocal()
items = db.query(ScheduleItem).all()

print("--- FAILED ITEMS ---")
found = False
for item in items:
    if item.status == 'failed':
        print(f"ID: {item.id} | Slug: {item.profile_slug} | Time: {item.scheduled_time} | Status: {item.status}")
        found = True

if not found:
    print("No failed items found.")

print("\n--- ITEMS FOR 2026-02-12 ---")
for item in items:
    if item.scheduled_time and item.scheduled_time.strftime('%Y-%m-%d') == '2026-02-12':
         print(f"ID: {item.id} | Slug: {item.profile_slug} | Time: {item.scheduled_time} | Status: {item.status}")

db.close()
