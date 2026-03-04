import asyncio
import sys
import os
import time
# Force UTF-8 for Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from core.database import SessionLocal
from core.models import ScheduleItem
from app.api.endpoints.scheduler import scheduler_service
from core.logger import logger

async def test_repost_full():
    print("--- TEST REPOST FULL FLOW ---")
    
    db = SessionLocal()
    item = db.query(ScheduleItem).filter(ScheduleItem.id == 31).first()
    
    if not item:
        print("Item 31 not found. Cannot proceed.")
        return

    # 1. Reset Status
    item.status = 'failed'
    item.error_message = None
    db.commit()
    print("Reset status to 'failed' for testing.")
    db.close()

    # 2. Trigger Repost
    print("Triggering repost_event(31, mode='now')...")
    try:
        start_time = time.time()
        result = scheduler_service.retry_event("31", mode="now")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error calling retry_event: {e}")
        return

    # 3. Monitor Status
    print("Monitoring status for COMPLETION (Timeout 60s)...")
    last_status = None
    
    for i in range(60):
        await asyncio.sleep(1)
        db = SessionLocal()
        item = db.query(ScheduleItem).filter(ScheduleItem.id == 31).first()
        
        if item.status != last_status:
            print(f"[{i+1}s] Status Changed: {last_status} -> {item.status}")
            last_status = item.status
        
        if item.status == 'completed':
            print("SUCCESS: Item execution COMPLETED!")
            print(f"Published URL: {item.published_url}")
            db.close()
            return
        elif item.status == 'failed':
             print(f"FAILURE: Item status is FAILED.")
             print(f"Error Message: {item.error_message}")
             db.close()
             return
        
        db.close()
        
    print("TIMEOUT: Item did not complete within 60s.")
    print("Checking logs for clues...")
    
    # Check last logs
    logs = logger.get_logs(limit=10)
    for l in logs:
        print(f"LOG: {l['timestamp']} [{l['level']}] {l['message']}")

if __name__ == "__main__":
    asyncio.run(test_repost_full())
