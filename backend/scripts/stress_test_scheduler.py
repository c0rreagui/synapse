import sys
import os
import time
import asyncio
from datetime import datetime, timedelta

# Add backend root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
# from core.database import init_db # Not exposed
from core.models import ScheduleItem
from core.scheduler import scheduler_service

def stress_test():
    print("🔥 Starting Scheduler Stress Test...")
    
    profile_id = "test_stress_profile"
    
    # 1. Cleaning up previous stress tests
    db = SessionLocal()
    try:
        deleted = db.query(ScheduleItem).filter(ScheduleItem.profile_slug == profile_id).delete()
        db.commit()
        print(f"🧹 Cleaned up {deleted} old test items.")
    except Exception as e:
        print(f"Error cleaning up: {e}")
    finally:
        db.close()
        
    start_time = time.time()
    
    # 2. Burst Creation (50 items)
    items_to_create = 50
    print(f"🚀 Creating {items_to_create} schedule items rapidly...")
    
    base_time = datetime.now()
    
    errors = 0
    created_ids = []
    
    for i in range(items_to_create):
        # Stagger times by 10 mins
        sched_time = base_time + timedelta(minutes=10*i)
        
        try:
            result = scheduler_service.add_event(
                profile_id=profile_id,
                video_path=f"C:\\videos\\stress_{i}.mp4",
                scheduled_time=sched_time.isoformat(),
                sound_title=f"Viral Sound {i}"
            )
            created_ids.append(result["id"])
            if i % 10 == 0:
                print(f"   Created {i+1}...")
        except Exception as e:
            print(f"❌ Failed to create item {i}: {e}")
            errors += 1
            
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✅ Created {len(created_ids)} items in {duration:.2f} seconds.")
    print(f"⚡ Rate: {len(created_ids)/duration:.2f} items/sec")
    
    if errors > 0:
        print(f"⚠️ Encountered {errors} errors during creation.")
        
    # 3. Verification
    print("🔍 Verifying DB Integrity...")
    db = SessionLocal()
    count = db.query(ScheduleItem).filter(ScheduleItem.profile_slug == profile_id).count()
    db.close()
    
    print(f"📊 DB Count for '{profile_id}': {count}")
    
    if count == items_to_create:
        print("✅ SUCCESS: Data integrity confirmed.")
    else:
        print(f"❌ FAILURE: Expected {items_to_create}, found {count}.")

    # 4. Slot Availability Performance Check
    print("⏱️ Checking Slot Availability Performance...")
    
    check_start_time = time.time()
    # Check 100 random slots
    for i in range(100):
        test_time = base_time + timedelta(minutes=5*i) # Some will overlap, some won't
        scheduler_service.is_slot_available(profile_id, test_time)
        
    check_duration = time.time() - check_start_time
    print(f"✅ Checked 100 slots in {check_duration:.4f} seconds.")
    
    # Cleanup
    # db = SessionLocal()
    # db.query(ScheduleItem).filter(ScheduleItem.profile_slug == profile_id).delete()
    # db.commit()
    # db.close()

if __name__ == "__main__":
    stress_test()
