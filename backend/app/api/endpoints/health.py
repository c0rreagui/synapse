
from fastapi import APIRouter, Depends
import os
import json
import time
from datetime import datetime
from sqlalchemy import text
from core.database import SessionLocal
from core.queue_manager import QueueManager
from core.storage import s3_storage
from core.config import DATA_DIR
import logging
import subprocess
import httpx

router = APIRouter()
logger = logging.getLogger("Health")

def check_db():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True, "connected"
    except Exception as e:
        return False, str(e)

async def check_redis():
    try:
        pool = await QueueManager.get_pool()
        # Arq pool doesn't strictly have ping, but we can check health
        # or use raw redis connection. 
        # For arq, generally if we can get pool, we are good?
        # Let's try to enqueue a dummy or just use the pool's internal redis
        # Arq doesn't expose raw redis easily without creating a job?
        # Actually QueueManager.get_pool() returns an ArqRedis instance
        await pool.ping()
        return True, "connected"
    except Exception as e:
        return False, str(e)

def check_minio():
    try:
        # Check if bucket exists
        s3_storage.client.head_bucket(Bucket=s3_storage.bucket)
        return True, "connected"
    except Exception as e:
        return False, str(e)

def check_scheduler():
    hb_path = os.path.join(DATA_DIR, "scheduler_heartbeat.json")
    if not os.path.exists(hb_path):
        return False, "no_heartbeat_file"
        
    try:
        with open(hb_path, 'r') as f:
            data = json.load(f)
        last_ts = data.get("timestamp", 0)
        latency = time.time() - last_ts
        if latency < 120:
            return True, f"running_latency_{int(latency)}s"
        return False, f"stalled_latency_{int(latency)}s"
    except Exception as e:
        return False, str(e)

def check_ffmpeg():
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            timeout=5
        )
        if result.returncode == 0:
            return True, "installed"
        return False, f"error_code_{result.returncode}"
    except FileNotFoundError:
        return False, "not_found"
    except Exception as e:
        return False, str(e)

async def check_twitch():
    try:
        async with httpx.AsyncClient() as client:
            # Pinging Twitch API without credentials returns 401 Unauthorized
            # which proves network connectivity to Twitch is healthy.
            response = await client.get("https://api.twitch.tv/helix/games/top", timeout=5)
            if response.status_code in (200, 401) or response.status_code < 500:
                return True, "reachable"
            else:
                return False, f"unreachable_{response.status_code}"
    except Exception as e:
        return False, str(e)

@router.get("/")
async def health_check():
    """
    Comprehensive System Health Check
    """
    db_ok, db_msg = check_db()
    redis_ok, redis_msg = await check_redis()
    minio_ok, minio_msg = check_minio()
    sched_ok, sched_msg = check_scheduler()
    ffmpeg_ok, ffmpeg_msg = check_ffmpeg()
    twitch_ok, twitch_msg = await check_twitch()
    
    status = "healthy" if all([db_ok, redis_ok, minio_ok, ffmpeg_ok, twitch_ok]) else "unhealthy"
    
    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": {"ok": db_ok, "message": db_msg},
            "redis": {"ok": redis_ok, "message": redis_msg},
            "minio": {"ok": minio_ok, "message": minio_msg},
            "scheduler": {"ok": sched_ok, "message": sched_msg},
            "ffmpeg": {"ok": ffmpeg_ok, "message": ffmpeg_msg},
            "twitch_api": {"ok": twitch_ok, "message": twitch_msg}
        }
    }

@router.get("/sonar")
def get_sonar_status():
    """Legacy Endpoint for Scheduler"""
    ok, msg = check_scheduler()
    return {
        "status": "running" if ok else "offline",
        "details": msg
    }
