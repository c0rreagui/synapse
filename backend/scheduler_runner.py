import asyncio
import os
import sys
from datetime import datetime

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.logger import logger
from core.scheduler import Scheduler

async def main():
    logger.log("info", "Starting Standalone Scheduler Service...", "scheduler")
    print(f"[SCHEDULER] Service Initialized at {datetime.now()}")
    
    scheduler = Scheduler()
    try:
        await scheduler.start_loop()
    except Exception as e:
        logger.log("critical", f"Scheduler Service Crashed: {e}", "scheduler")
        print(f"[SCHEDULER] CRITICAL ERROR: {e}")
        # In Docker, we want to exit so it restarts
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.log("info", "Scheduler Stopped by User", "scheduler")
        print("[SCHEDULER] Stopped.")
