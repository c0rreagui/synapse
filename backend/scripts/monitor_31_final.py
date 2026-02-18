
import script_env
script_env.setup_script_env()
from core.database import SessionLocal
from core.models import ScheduleItem
import time
from datetime import datetime, timedelta
import sys

# Target: 31
ITEM_ID = 31
# Force Immediate Run
now = datetime.now()
target_time = now #.replace(second=0, microsecond=0)

print(f"--- SETUP ---")
print(f"Current Time: {now}")
print(f"Target Time : {target_time}")

def reschedule_and_monitor():
    db = SessionLocal()
    try:
        item = db.query(ScheduleItem).filter(ScheduleItem.id == ITEM_ID).first()
        if not item:
            print("Item 31 not found!")
            return

        print(f"Found Item 31. Current Status: {item.status}")
        
        # Reschedule
        item.scheduled_time = target_time
        item.status = "pending"
        item.error_message = None # Clear any old errors
        db.commit()
        print(f"Rescheduled to {target_time} and set to PENDING.")
        
        # Monitor
        print("Starting Monitor (Ctrl+C to stop)...")
        last_status = "pending"
        while True:
            db.expire_all() # Refresh data
            item = db.query(ScheduleItem).filter(ScheduleItem.id == ITEM_ID).first()
            
            # Print update if status changes or every minute
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Status: {item.status} | Error: {item.error_message}")
            
            if item.status == "completed":
                print("\nSUCCESS! Item is COMPLETED (Posted).")
                break
            
            if item.status == "failed":
                print(f"\nFAILURE! Item FAILED with error: {item.error_message}")
                break
                
            time.sleep(10)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reschedule_and_monitor()
