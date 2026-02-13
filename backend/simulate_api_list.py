from core.scheduler import scheduler_service
import json

# Force a reload from DB
items = scheduler_service.load_schedule()

found = False
for item in items:
    if str(item['id']) == '52':
        print(f"ID: {item['id']}")
        print(f"Status: {item['status']}")
        print(f"Path: {item['video_path']}")
        print(f"Error: {item['error_message']}")
        found = True
        break

if not found:
    print("Item 52 not found in load_schedule()")
