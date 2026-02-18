import script_env
script_env.setup_script_env()

import time
import sys
from core.database import SessionLocal
from core.models import ScheduleItem

ITEM_ID = 31

print(f"Monitoring Item {ITEM_ID}...")
last_status = None

for i in range(120): # Monitor for 10 minutes (5s interval)
    db = SessionLocal()
    try:
        item = db.query(ScheduleItem).filter(ScheduleItem.id == ITEM_ID).first()
        if item:
            status = item.status
            # Print only on change
            if status != last_status:
                print(f"[{time.strftime('%H:%M:%S')}] Status changed: {last_status} -> {status}")
                if status == 'failed':
                     print(f"❌ FAILED! Error: {item.error_message}")
                     break
                if status == 'completed':
                     print(f"✅ COMPLETED! URL: {item.published_url}")
                     break
                last_status = status
            
            # Heartbeat every minute
            if i % 12 == 0:
                 print(f"[{time.strftime('%H:%M:%S')}] Current Status: {status} (Next check in 5s)")
        else:
            print(f"Item {ITEM_ID} not found!")
            break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()
    
    time.sleep(5)
