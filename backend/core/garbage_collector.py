import os
import asyncio
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from core.logger import logger
from core.database import SessionLocal
from core.models import ClipJob, PendingApproval
from datetime import timedelta, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORTS_DIR = os.path.join(BASE_DIR, "data", "exports")
CLIPPER_OUTPUT_DIR = os.path.join(BASE_DIR, "data", "clipper", "output")
PENDING_DIR = os.path.join(BASE_DIR, "data", "pending")

TTL_HOURS = 120 # 5 days
GC_INTERVAL_HOURS = 6 # Run check every 6 hours

async def start_gc_loop():
    """
    Background worker function that periodically checks the exports directory
    and removes video files older than TTL_HOURS.
    """
    logger.info(f"SYSTEM: Garbage Collector Initialized. TTL: {TTL_HOURS}h, Interval: {GC_INTERVAL_HOURS}h")
    
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    os.makedirs(CLIPPER_OUTPUT_DIR, exist_ok=True)
    os.makedirs(PENDING_DIR, exist_ok=True)
    
    while True:
        try:
            _run_gc_pass()
        except Exception as e:
            logger.error(f"Error in Garbage Collector loop: {e}")
            
        # Wait for next interval
        await asyncio.sleep(GC_INTERVAL_HOURS * 3600)

def _run_gc_pass():
    now = time.time()
    ttl_seconds = TTL_HOURS * 3600
    deleted_count = 0
    bytes_freed = 0
    
    dirs_to_check = [EXPORTS_DIR, CLIPPER_OUTPUT_DIR, PENDING_DIR]
    
    for directory in dirs_to_check:
        if not os.path.exists(directory):
            continue
            
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            
            if not os.path.isfile(filepath) or not filename.endswith('.mp4'):
                continue
                
            file_age_seconds = now - os.path.getmtime(filepath)
            
            if file_age_seconds > ttl_seconds:
                try:
                    size = os.path.getsize(filepath)
                    os.remove(filepath)
                    deleted_count += 1
                    bytes_freed += size
                    
                    sp_time = datetime.fromtimestamp(now, tz=ZoneInfo("America/Sao_Paulo")).strftime('%Y-%m-%d %H:%M:%S')
                    logger.info(f"[{sp_time}] GC: Deleted {filename} from {os.path.basename(directory)} (Age: {file_age_seconds/3600:.1f}h)")
                except Exception as e:
                    logger.error(f"GC: Failed to delete {filename}: {e}")
                    
    if deleted_count > 0:
        mb_freed = bytes_freed / (1024 * 1024)
        logger.info(f"GC Pass Complete: Removed {deleted_count} old videos, freed {mb_freed:.2f} MB")
        
    # Limpeza no Banco
    _clean_database_records()

def _clean_database_records():
    db = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        threshold = now_utc - timedelta(hours=TTL_HOURS)
        
        deleted_jobs = db.query(ClipJob).filter(
            ClipJob.status == 'failed',
            ClipJob.created_at < threshold
        ).delete()
        
        pending_threshold = now_utc - timedelta(days=30)
        deleted_pending = db.query(PendingApproval).filter(
            PendingApproval.status == 'pending',
            PendingApproval.created_at < pending_threshold
        ).delete()
        
        db.commit()
        if deleted_jobs > 0 or deleted_pending > 0:
            logger.info(f"DB GC Complete: Removed {deleted_jobs} failed jobs and {deleted_pending} stale pending approvals.")
    except Exception as e:
        logger.error(f"DB GC Error: {e}")
        db.rollback()
    finally:
        db.close()
