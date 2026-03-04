import os
import asyncio
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from core.logger import logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORTS_DIR = os.path.join(BASE_DIR, "data", "exports")
TTL_HOURS = 120 # 5 days
GC_INTERVAL_HOURS = 6 # Run check every 6 hours

async def start_gc_loop():
    """
    Background worker function that periodically checks the exports directory
    and removes video files older than TTL_HOURS.
    """
    logger.info(f"SYSTEM: Garbage Collector Initialized. TTL: {TTL_HOURS}h, Interval: {GC_INTERVAL_HOURS}h")
    
    # Ensure export dir exists
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
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
    
    if not os.path.exists(EXPORTS_DIR):
        return
        
    for filename in os.listdir(EXPORTS_DIR):
        filepath = os.path.join(EXPORTS_DIR, filename)
        
        # Only target video files
        if not os.path.isfile(filepath) or not filename.endswith('.mp4'):
            continue
            
        file_age_seconds = now - os.path.getmtime(filepath)
        
        if file_age_seconds > ttl_seconds:
            try:
                size = os.path.getsize(filepath)
                os.remove(filepath)
                deleted_count += 1
                bytes_freed += size
                
                # Log using the correct timezone
                sp_time = datetime.fromtimestamp(now, tz=ZoneInfo("America/Sao_Paulo")).strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"[{sp_time}] GC: Deleted {filename} (Age: {file_age_seconds/3600:.1f}h)")
                
                # Note: DB flag logic (EXPIRED flag) is abstracted for now since 
                # tracking specific paths in DB requires DB schema changes on the ClipJob table.
                # Currently handling physical disk removal as priority.
            except Exception as e:
                logger.error(f"GC: Failed to delete {filename}: {e}")
                
    if deleted_count > 0:
        mb_freed = bytes_freed / (1024 * 1024)
        logger.info(f"GC Pass Complete: Removed {deleted_count} old videos, freed {mb_freed:.2f} MB")
