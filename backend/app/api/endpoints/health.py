
from fastapi import APIRouter
import os
import json
import time
from datetime import datetime
from core.config import DATA_DIR

router = APIRouter()

@router.get("/sonar")
def get_sonar_status():
    """
    Returns the real-time status of the background scheduler.
    """
    hb_path = os.path.join(DATA_DIR, "scheduler_heartbeat.json")
    
    status = {
        "status": "offline", # offline, running, stalled
        "latency_seconds": -1,
        "last_beat": None,
        "pid": None
    }
    
    if not os.path.exists(hb_path):
        return status
        
    try:
        with open(hb_path, 'r') as f:
            data = json.load(f)
            
        last_ts = data.get("timestamp", 0)
        now = time.time()
        latency = now - last_ts
        
        status["last_beat"] = data.get("last_beat")
        status["pid"] = data.get("pid")
        status["latency_seconds"] = round(latency, 2)
        
        # Determine health
        if latency < 90: # Loop runs every 60s, so <90 is safe
            status["status"] = "running"
        elif latency < 180:
            status["status"] = "stalled" # Late but maybe busy
        else:
            status["status"] = "offline" # > 3 min delay
            
        return status
        
    except Exception as e:
        status["error"] = str(e)
        return status
