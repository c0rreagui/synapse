
import sys
import os
import asyncio
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from core.database import SessionLocal
from core.models import ScheduleItem
from core.scheduler import Scheduler

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)

async def force_execution():
    print("--- FORCING EXECUTION OF ITEM 4 ---")
    
    db = SessionLocal()
    try:
        # Get Item 4
        item = db.query(ScheduleItem).filter(ScheduleItem.id == 4).first()
        if not item:
            print("[FAIL] Item 4 not found in DB.")
            return

        print(f"Item Found: {item.id} | Status: {item.status} | Profile: {item.profile_slug}")
        print(f"Video Path: {item.video_path}")
        
        # Instantiate Scheduler
        scheduler = Scheduler()
        
        # Manually trigger execution
        print("[>] Triggering execute_due_item...")
        await scheduler.execute_due_item(item, db)
        
        print("[OK] Execution signal sent (check console for real-time logs).")
        
        # Refresh item to see result
        db.refresh(item)
        print(f"Final Status: {item.status}")
        if item.error_message:
            print(f"Error Message: {item.error_message}")

    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(force_execution())
