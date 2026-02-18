import script_env
script_env.setup_script_env()

from core.scheduler import Scheduler
from datetime import datetime

scheduler = Scheduler()
# User requested 22:35. Today is Feb 14.
target_time = "2026-02-14T22:35:00"

print(f"Rescheduling Item 31 to {target_time}...")
result = scheduler.update_event("31", scheduled_time=target_time)

if result:
    print(f"✅ Success! New Status: {result['status']}, Time: {result['scheduled_time']}")
else:
    print("❌ Failed to update item 31")
