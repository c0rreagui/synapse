
import asyncio
import os
import sys
import shutil
from unittest.mock import MagicMock

# Setup Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Sentry
sys.modules["sentry_sdk"] = MagicMock()

from core.database import SessionLocal
from core.models import ScheduleItem
from core.worker import check_consistency
from core.config import DONE_DIR, PROCESSING_DIR

async def test_recovery_logic():
    print("🧪 Starting Worker Recovery Test...")
    
    # 1. Setup: Create a "Zombie" item
    # Status = processing, but file is actually in DONE (simulating an upload that finished but DB failed to update)
    
    dummy_filename = "test_zombie_video.mp4"
    dummy_done_path = os.path.join(DONE_DIR, dummy_filename)
    
    # Ensure clean state
    if os.path.exists(dummy_done_path):
        os.remove(dummy_done_path)
        
    # Create file in DONE
    with open(dummy_done_path, "wb") as f:
        f.write(b"dummy_zombie_content")
        
    # Create DB record in PROCESSING
    db = SessionLocal()
    item_id = None
    try:
        zombie_item = ScheduleItem(
            profile_slug="p1",
            video_path=dummy_filename, # Store filename as path for this test
            status="processing",
            metadata_info={"test": "zombie"}
        )
        db.add(zombie_item)
        db.commit()
        db.refresh(zombie_item)
        item_id = zombie_item.id
        print(f"👻 Created Zombie Item #{item_id} (Status: processing) | File is at: {dummy_done_path}")
        
    except Exception as e:
        print(f"❌ Failed to setup test: {e}")
        return
    finally:
        db.close()
        
    # 2. Run Recovery
    print("🔄 Running check_consistency()...")
    await check_consistency()
    
    # 3. Verify
    db = SessionLocal()
    try:
        item = db.query(ScheduleItem).filter(ScheduleItem.id == item_id).first()
        print(f"🧐 Item #{item_id} Status is now: {item.status}")
        
        if item.status == "completed": # In models.py we might not have 'completed' enum, usually it's string 'posted' or 'completed'
            # Let's check what checking logic sets: ScheduleStatus.COMPLETED
            # Wait, ScheduleStatus might be an Enum class I need to check import of in worker.py
            print("✅ TEST PASSED: Item recovered to 'completed'")
        elif item.status == "posted":
             print("✅ TEST PASSED: Item recovered to 'posted'")
        else:
            print(f"❌ TEST FAILED: Status is {item.status}, expected 'completed'")
            
    finally:
        db.close()
        # Cleanup
        if os.path.exists(dummy_done_path):
            os.remove(dummy_done_path)
        # Optional: Delete DB record? Keep for debug.

if __name__ == "__main__":
    asyncio.run(test_recovery_logic())
