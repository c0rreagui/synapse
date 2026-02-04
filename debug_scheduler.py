import asyncio
import os
import sys
import logging

# Setup Path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from core.database import SessionLocal
from core.models import ScheduleItem
from core.scheduler import scheduler_service

# Configure logging to see output
logging.basicConfig(level=logging.DEBUG)

async def debug_execution():
    print("--- STARTING DEBUG EXECUTION ---")
    db = SessionLocal()
    try:
        # Fetch the failed item (ID 1)
        item = db.query(ScheduleItem).filter(ScheduleItem.id == 1).first()
        if not item:
            print("Item ID 1 not found!")
            return

        print(f"Loaded Item 1. Status: {item.status}")
        print(f"Video Path: {item.video_path}")
        
        # Force status to pending for logic to work (though execute_due_item doesn't strictly check prior status, it sets it)
        # item.status = 'pending' 
        
        print("Calling execute_due_item...")
        await scheduler_service.execute_due_item(item, db)
        print("--- EXECUTION FINISHED ---")
        print(f"Final Status: {item.status}")
        print(f"Final Metadata: {item.metadata_info}")
        
    except Exception as e:
        print(f"CRITICAL EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(debug_execution())
