import asyncio
import os
import sys
import shutil
import logging
from datetime import datetime, timezone

# Setup Path
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Force UTF-8 for console output
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from core.database import SessionLocal
from core.models import ScheduleItem
from core.scheduler import scheduler_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_test():
    print("--- STARTING E2E TEST V8: REGEX FIX ---")
    
    # 1. Setup Test File
    done_dir = os.path.join("backend", "done")
    pending_dir = os.path.join("backend", "data", "pending")
    
    if not os.path.exists(pending_dir):
        os.makedirs(pending_dir)

    source_video = None
    if os.path.exists(done_dir):
        for f in os.listdir(done_dir):
            if f.endswith(".mp4"):
                source_video = os.path.join(done_dir, f)
                break
            
    if not source_video:
        print("No source video found in backend/done to use for test.")
        return

    target_name = "test_privacy_fix_v8.mp4"
    target_path = os.path.join(pending_dir, target_name)
    
    shutil.copy(source_video, target_path)
    print(f"Copied test video to: {target_path}")
    
    # 2. Setup DB Item
    db = SessionLocal()
    try:
        profile_slug = "tiktok_profile_1770135259969"
        
        # Cleanup
        db.query(ScheduleItem).filter(ScheduleItem.video_path.like(f"%{target_name}")).delete()
        db.commit()
        
        print(f"Creating ScheduleItem for {profile_slug}...")
        
        new_item = ScheduleItem(
            profile_slug=profile_slug,
            video_path=f"/app/data/pending/{target_name}",
            scheduled_time=datetime.now(timezone.utc),
            status="pending",
            metadata_info={
                "caption": "[TESTE V8] Regex Fixed - Somente Voce 🔒",
                "privacy_level": "self_only", 
                "smart_captions": False,
                "viral_music_enabled": False
            }
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        
        print(f"Item Created ID: {new_item.id}")
        
        # 3. Execute
        print("Executing Item...")
        result = await scheduler_service.execute_due_item(new_item, db)
        
        print("--- EXECUTION FINISHED ---")
        print(f"Result: {result}")
        print(f"Final Item Status: {new_item.status}")
        
    except Exception as e:
        print(f"TEST EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(run_test())
