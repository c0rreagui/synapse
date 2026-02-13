import time
import sys
import os
from datetime import datetime

# Adjust path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from core.database import SessionLocal
from core.models import ScheduleItem

def monitor_item_31():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting monitor for Item 31 (Target: 20:10)")
    
    last_status = None
    timeout_min = 10 
    end_time = time.time() + (timeout_min * 60)
    
    while time.time() < end_time:
        db = SessionLocal()
        item = db.query(ScheduleItem).filter(ScheduleItem.id == 31).first()
        
        if not item:
            print("Item 31 not found!")
            break
            
        current_status = item.status
        if current_status != last_status:
             print(f"[{datetime.now().strftime('%H:%M:%S')}] Status Change: {last_status} -> {current_status}")
             if current_status == 'failed':
                 print(f"FAILURE DETAILS: {item.error_message}")
             last_status = current_status
        else:
             # Heartbeat every minute if no change
             if int(time.time()) % 60 == 0:
                 print(f"[{datetime.now().strftime('%H:%M:%S')}] Status: {current_status}")
                 
        if current_status in ['completed', 'posted']:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] SUCCESS: Item published!")
            print(f"URL: {item.published_url}")
            break
            
        if current_status == 'failed' and "Session" not in (item.error_message or ""):
             # If failed but NOT session error, we stop? No, user wants to know result.
             # If session error, we know it will fail, but user wants to see it happened at 20:10.
             pass

        db.close()
        time.sleep(5)

if __name__ == "__main__":
    monitor_item_31()
