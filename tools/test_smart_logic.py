from datetime import datetime, timedelta
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.scheduler import scheduler_service

def test_smart_logic():
    print("🧪 Testing Smart Logic...")
    
    # 1. Setup: Clear existing schedule for test profile
    print("   [Setup] Clearing test profile events...")
    profile_id = "test_smart_logic_profile"
    existing = scheduler_service.load_schedule()
    for e in existing:
        if e['profile_id'] == profile_id:
            scheduler_service.delete_event(e['id'])
            
    # 2. Create Obstacle Event at 14:00
    base_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
    scheduler_service.add_event(profile_id, "video1.mp4", base_time.isoformat())
    print(f"   [Step 1] Created Obstacle at {base_time.strftime('%H:%M')}")
    
    # 3. Test is_slot_available
    print("   [Step 2] Testing is_slot_available...")
    
    # Check exact time (Should be False)
    assert not scheduler_service.is_slot_available(profile_id, base_time), "❌ Slot should be taken!"
    
    # Check +10 mins (Should be False due to 15min buffer)
    check_close = base_time + timedelta(minutes=10)
    assert not scheduler_service.is_slot_available(profile_id, check_close), "❌ Buffer violation not detected!"
    
    # Check +20 mins (Should be True)
    check_far = base_time + timedelta(minutes=20)
    assert scheduler_service.is_slot_available(profile_id, check_far), "❌ Safe slot reported as unavailable!"
    print("   ✅ is_slot_available passed.")
    
    # 4. Test find_next_available_slot
    print("   [Step 3] Testing find_next_available_slot...")
    
    # Start looking at 13:50 (should skip 14:00 obstacle)
    start_look = base_time - timedelta(minutes=10)
    found_iso = scheduler_service.find_next_available_slot(profile_id, start_look)
    found_dt = datetime.fromisoformat(found_iso)
    
    print(f"      - Started looking at: {start_look.strftime('%H:%M')}")
    print(f"      - Found slot at: {found_dt.strftime('%H:%M')}")
    
    # Expect 14:15 (Next 15m increment after 14:00 buffer ends? 
    # 14:00 event buffers 13:45-14:15. 
    # 13:50 check -> conflict (inside 13:45-14:15)
    # 13:50 + 15 = 14:05 -> conflict (inside 13:45-14:15)
    # 14:05 + 15 = 14:20 -> Safe?
    # Let's see behavior. The loop adds 15 mins.
    
    assert found_dt > base_time, "❌ Found slot is before obstacle!"
    assert scheduler_service.is_slot_available(profile_id, found_dt), "❌ Found slot is not actually safe!"
    print("   ✅ find_next_available_slot passed.")
    
    print("\n🎉 ALL TESTS PASSED! Smart Logic is Operational.")

if __name__ == "__main__":
    test_smart_logic()
