import script_env
script_env.setup_script_env()

import asyncio
import os
from core.database import SessionLocal
from core.models import ScheduleItem
from core.worker import upload_video_task

async def main():
    ITEM_ID = 31
    db = SessionLocal()
    try:
        item = db.query(ScheduleItem).filter(ScheduleItem.id == ITEM_ID).first()
        if not item:
            print(f"Item {ITEM_ID} not found")
            return
            
        print(f"Manually running task for Item {ITEM_ID}...")
        print(f"Video Path: {item.video_path}")
        
        # Mock Context
        ctx = {}
        
        # Parse metadata
        metadata = item.metadata_info if item.metadata_info else {}
        # metadata = None
        
        # [SYN-FIX] Clean up corrupted path from DB if necessary
        # DB has: /app/data/pending/D:\...
        raw_path = item.video_path
        if "D:\\" in raw_path:
             # Extract the D:\ part
             clean_path = raw_path[raw_path.find("D:\\"):]
             print(f"🧹 Fixed Path: {clean_path}")
        else:
             clean_path = raw_path

        # Run task
        # Note: upload_video_task is async
        result = await upload_video_task(ctx, ITEM_ID, clean_path, metadata)
        
        print(f"✅ Task execution finished. Result: {result}")
        
    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    # Force Windows loop policy if needed
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
