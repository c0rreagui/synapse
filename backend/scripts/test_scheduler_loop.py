
import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scheduler import scheduler_service
from core.database import SessionLocal
from core.models import ScheduleItem

async def test_execution():
    print("Testing Scheduler Engine...")
    db = SessionLocal()
    
    # 1. Create Dummy Event (Due 5 mins ago)
    now = datetime.now(timezone.utc)
    past_time = now - timedelta(minutes=5)
    
    dummy_path = os.path.join(os.path.dirname(__file__), "test_dummy_video.mp4")
    # Create valid dummy file so it doesn't fail on file check immediately logic (optional, but good for cleanliness)
    with open(dummy_path, 'w') as f:
        f.write("test")

    print(f"Creating test event due at {past_time.isoformat()}...")
    
    # Manually insert to bypass add_event logic if needed, or just use add_event
    # We use DB direct to simulate "Pending" state
    item = ScheduleItem(
        profile_slug="test_user",
        video_path=dummy_path,
        scheduled_time=past_time,
        status="pending",
        metadata_info={}
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    item_id = item.id
    print(f"Created Item ID: {item_id}")

    try:
        # 2. Run Check
        print("Running check_due_items()...")
        await scheduler_service.check_due_items()
        
        # 3. Verify Status Change
        db.refresh(item)
        print(f"Item Status after check: {item.status}")
        
        if item.status in ['processing', 'completed', 'failed']:
            print("TEST PASSED: Scheduler picked up the item!")
            if item.status == 'failed':
                 # error_log column might not exist in models.py yet, so we just print generic
                 print(f"Note: Item status is failed. Check logs.")
        else:
            print(f"TEST FAILED: Item still {item.status}")

    finally:
        # Cleanup
        print("Cleaning up...")
        db.delete(item)
        db.commit()
        db.close()
        if os.path.exists(dummy_path):
            os.remove(dummy_path)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(test_execution())
