
import script_env
script_env.setup_script_env()
from core.database import SessionLocal
from core.models import ScheduleItem
from core.scheduler import Scheduler
import time

ITEM_ID = 31

def check():
    db = SessionLocal()
    item = db.query(ScheduleItem).filter(ScheduleItem.id == ITEM_ID).first()
    print(f"Current Error: {item.error_message}")
    db.close()

def clear():
    print("Clearing error...")
    db = SessionLocal()
    item = db.query(ScheduleItem).filter(ScheduleItem.id == ITEM_ID).first()
    item.error_message = None
    item.status = 'processing' # Set to processing to trigger zombie check
    # Set time to past to trigger zombie check logic
    from datetime import datetime, timedelta
    # zombie_threshold is 1h ago. So scheduled_time must be < 1h ago.
    # Set to 2 hours ago.
    item.scheduled_time = datetime.now() - timedelta(hours=2)
    db.commit()
    db.close()


import asyncio

async def trigger_async():
    print("Triggering Scheduler (Host)...")
    s = Scheduler()
    await s.check_due_items()

if __name__ == "__main__":
    check()
    clear()
    check()
    asyncio.run(trigger_async())
    check()
