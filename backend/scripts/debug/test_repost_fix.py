import asyncio
import os
import sys
from datetime import datetime

# Force UTF-8 output for Windows consoles
sys.stdout.reconfigure(encoding='utf-8')

# Adjust path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from core.models import ScheduleItem
from core.scheduler import scheduler_service

async def test_repost():
    print("--- TEST REPOST FIX ---")
    
    # 1. Reset Item 31 to 'failed' to simulate starting state
    db = SessionLocal()
    item = db.query(ScheduleItem).filter(ScheduleItem.id == 31).first()
    
    if not item:
        print("Item 31 not found. Cannot proceed.")
        return

    print(f"Current Status: {item.status}")
    item.status = 'failed'
    db.commit()
    print("Reset status to 'failed' for testing.")
    db.close()

    # 2. Trigger Repost
    print("Triggering repost_event(31, mode='now')...")
    try:
        # We need to simulate the async context
        result = scheduler_service.retry_event("31", mode="now")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error calling retry_event: {e}")
        return

    # 3. Monitor for Status Change
    print("Monitoring status change (timeout 10s)...")
    for i in range(10):
        await asyncio.sleep(1)
        db = SessionLocal()
        item = db.query(ScheduleItem).filter(ScheduleItem.id == 31).first()
        print(f"[{i+1}s] Status: {item.status}")
        
        if item.status == 'processing':
            print("SUCCESS: Item moved to 'processing'!")
            db.close()
            return
        elif item.status == 'completed':
             print("SUCCESS: Item execution completed!")
             db.close()
             return
            
        db.close()
        
    print("TIMEOUT: Item did not move to processing state.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_repost())
