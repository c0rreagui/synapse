
import asyncio
import os
import sys
import shutil
import logging
from typing import Dict, Any

# Ensure path is correct
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arq import create_pool
from arq.connections import RedisSettings
from core.database import SessionLocal
from core.models import ScheduleItem
from core.manual_executor import execute_approved_video
from core.consts import ScheduleStatus
from datetime import datetime

# Logging
logger = logging.getLogger("Worker")
logging.basicConfig(level=logging.INFO)

async def startup(ctx):
    logger.info("🚀 Worker Process Starting...")
    # Initialize DB connection test or anything else
    await check_consistency()

async def check_consistency():
    """
    [SYN-DB] Transactional Recovery
    Checks for stuck 'processing' items that might have finished while worker was down.
    """
    logger.info("🕵️ Running DB Consistency Check...")
    db = SessionLocal()
    try:
        # Find items likely stuck
        stuck_items = db.query(ScheduleItem).filter(ScheduleItem.status == 'processing').all()
        
        if not stuck_items:
            logger.info("✅ No stuck items found.")
            return

        from core.config import DONE_DIR, ERRORS_DIR, PROCESSING_DIR
        
        for item in stuck_items:
            filename = os.path.basename(item.video_path)
            logger.info(f"Checking stuck item {item.id}: {filename}")
            
            # Case 1: In DONE? -> Mark Completed
            done_path = os.path.join(DONE_DIR, filename)
            if os.path.exists(done_path):
                logger.info(f"♻️ RECOVERY: Item {item.id} found in DONE. Marking completed.")
                item.status = ScheduleStatus.COMPLETED
                db.commit()
                continue
                
            # Case 2: In ERRORS? -> Mark Failed
            error_path = os.path.join(ERRORS_DIR, filename)
            if os.path.exists(error_path):
                logger.info(f"♻️ RECOVERY: Item {item.id} found in ERRORS. Marking failed.")
                item.status = ScheduleStatus.FAILED
                db.commit()
                continue
                
            # Case 3: Still in Processing?
            # Check for .completed marker
            proc_path = os.path.join(PROCESSING_DIR, filename)
            marker_path = proc_path + ".completed"
            
            if os.path.exists(marker_path):
                 # It finished but move failed?
                 # Should we try to move it? Yes.
                 logger.info(f"♻️ RECOVERY: Item {item.id} found in PROCESSING with .completed marker.")
                 try:
                     if os.path.exists(done_path): os.remove(done_path)
                     shutil.move(proc_path, done_path)
                     item.status = ScheduleStatus.COMPLETED
                     db.commit()
                     if os.path.exists(marker_path): os.remove(marker_path)
                 except Exception as e:
                     logger.error(f"Failed to recover completed item: {e}")
            else:
                 # Real Zombie?
                 # If it's been processing for > 1 hour, maybe fail it?
                 # For now just log usage.
                 logger.warning(f"⚠️ Item {item.id} is in PROCESSING state but file state is ambiguous.")
                 
    except Exception as e:
        logger.error(f"Consistency check failed: {e}")
    finally:
        db.close()

async def shutdown(ctx):
    logger.info("🛑 Worker Process Stopping...")

async def update_job_status(item_id: int, status: str, result: Dict = None):
    """Updates the schedule item status in the DB."""
    db = SessionLocal()
    try:
        item = db.query(ScheduleItem).filter(ScheduleItem.id == item_id).first()
        if item:
            item.status = status
            if result:
                item.error_message = result.get('message')
                if status == ScheduleStatus.COMPLETED:
                    item.published_url = result.get('url')
            item.updated_at = datetime.now()
            db.commit()
    except Exception as e:
        logger.error(f"Failed to update job status in DB: {e}")
    finally:
        db.close()

async def upload_video_task(ctx, item_id: int, video_path: str, metadata: Dict[str, Any]):
    """
    ARQ Task to upload a video.
    """
    logger.info(f"⚡ [JOB START] Upload Task for Item {item_id}")
    
    # 1. Update DB -> Processing
    await update_job_status(item_id, ScheduleStatus.PROCESSING)
    
    local_video_path = video_path # [SYN-FIX] Default to provided path
    
    try:
        # [SYN-FIX] S3 Support
        # If video_path starts with s3://, download it first
        if video_path.startswith("s3://"):
             from core.storage import s3_storage
             import tempfile
             
             # Parse bucket/key
             # Format: s3://bucket/key
             without_scheme = video_path.replace("s3://", "")
             parts = without_scheme.split("/", 1)
             if len(parts) == 2:
                 bucket, key = parts
                 # Create temp file
                 tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                 tmp.close()
                 local_video_path = tmp.name
                 
                 logger.info(f"⬇️ Downloading from S3: {key} -> {local_video_path}")
                 s3_storage.download_file(key, local_video_path)
             else:
                 raise ValueError(f"Invalid S3 URI: {video_path}")

        # 2. Execute Upload
        # execute_approved_video returns a dict with 'status' and 'message' (and 'url' on success)
        result = await execute_approved_video(
            local_video_path,
            is_scheduled=True,
            metadata=metadata,
            processing_id=str(item_id)
        )
        
        if result is None:
             logger.error("❌ EAV returned None! This usually means an unhandled path in manual_executor.")
             result = {"status": "failed", "message": "Internal Error: Executor returned None"}

        status = result.get('status', 'failed')
        
        # 3. Update DB -> Completed/Failed
        final_status = ScheduleStatus.COMPLETED if status in ['success', 'completed', 'ready'] else ScheduleStatus.FAILED
        await update_job_status(item_id, final_status, result)
        
        logger.info(f"✅ [JOB DONE] Item {item_id} finished with status: {final_status}")
        return result

    except asyncio.CancelledError:
        logger.warning(f"⚠️ [JOB TIMEOUT] Item {item_id} was cancelled/timed out.")
        await update_job_status(item_id, ScheduleStatus.FAILED, {"message": "Job Timed Out (Zombie Prevention)"})
        raise

    except Exception as e:
        logger.error(f"❌ [JOB ERROR] Item {item_id} crashed: {e}")
        await update_job_status(item_id, ScheduleStatus.FAILED, {"message": str(e)})
        raise e
        
    finally:
        # Cleanup Temp
        if local_video_path and local_video_path != video_path and os.path.exists(local_video_path):
            try:
                os.unlink(local_video_path)
                logger.info(f"🗑️ Cleaned up temp file: {local_video_path}")
            except Exception as cleanup_err:
                logger.error(f"Failed to cleanup temp file {local_video_path}: {cleanup_err}")

# ARQ Settings
class WorkerSettings:
    functions = [upload_video_task]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379))
    )
    max_jobs = 1  # Limit concurrency to 1 per worker to safe resources (Headless browser usage)
    job_timeout = 600 # 10 minutes hard timeout (prevents zombies)
