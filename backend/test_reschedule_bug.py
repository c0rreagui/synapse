from datetime import datetime, timedelta
from core.database import SessionLocal
from core.models import ScheduleItem
from core.scheduler import scheduler_service

def test_update_resets_status():
    print("--- TEST RESCHEDULE FLOW ---")
    
    db = SessionLocal()
    item = db.query(ScheduleItem).filter(ScheduleItem.id == 31).first()
    
    if not item:
        print("Item 31 not found.")
        return

    # 1. Setup: Item is FAILED
    item.status = 'failed'
    db.commit()
    print(f"Setup: Item {item.id} status set to '{item.status}'")
    
    # 2. Action: Update Time to +10 mins
    new_time = (datetime.now() + timedelta(minutes=10)).isoformat()
    print(f"Action: Updating scheduled_time to {new_time}")
    
    scheduler_service.update_event(
        str(item.id),
        scheduled_time=new_time
    )
    
    # 3. Verification
    db.refresh(item)
    print(f"Result: Item status is now '{item.status}'")
    
    if item.status == 'pending':
        print("SUCCESS: Status reset to 'pending'.")
    else:
        print(f"FAILURE: Status remained '{item.status}'. Expected 'pending'.")

    db.close()

if __name__ == "__main__":
    test_update_resets_status()
