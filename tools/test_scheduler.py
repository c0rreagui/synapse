import requests
import json
import uuid
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1/scheduler"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_scheduler_flow():
    log("[START] Starting Scheduler API Test")

    # 1. List (Should be empty or have existing)
    try:
        res = requests.get(f"{BASE_URL}/list")
        if res.status_code == 404:
            log("❌ Error: Endpoint /list not found (404). Backend might need restart.")
            return False
        
        events = res.json()
        log(f"[OK] Listed {len(events)} events.")
    except Exception as e:
        log(f"[ERROR] Connection Failed: {e}")
        return False

    # 2. Create Event
    new_event = {
        "profile_id": "test_profile_1",
        "video_path": "/tmp/video.mp4",
        "scheduled_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "viral_music_enabled": True
    }
    
    res = requests.post(f"{BASE_URL}/create", json=new_event)
    if res.status_code == 200:
        created_event = res.json()
        event_id = created_event['id']
        log(f"[OK] Created event: {event_id}")
        if created_event.get("viral_music_enabled") == True:
            log("[OK] Viral Music Flag Verified in Response")
        else:
             log("[ERROR] Viral Music Flag MISSING or FALSE in Response")
    else:
        log(f"[ERROR] Failed to create event: {res.text}")
        return False

    # 3. Verify Creation
    res = requests.get(f"{BASE_URL}/list")
    events = res.json()
    found_event = next((e for e in events if e['id'] == event_id), None)
    if found_event:
        log("[OK] Event verified in list.")
        if found_event.get("viral_music_enabled") == True:
             log("[OK] Viral Music Flag Verified in List")
        else:
             log("[ERROR] Viral Music Flag MISSING or FALSE in List")
    else:
        log("[ERROR] Event NOT found in list.")
        return False

    # 4. Delete Event
    res = requests.delete(f"{BASE_URL}/{event_id}")
    if res.status_code == 200:
        log("[OK] Deleted event.")
    else:
        log(f"[ERROR] Failed to delete event: {res.text}")
        return False

    # 5. Verify Deletion
    res = requests.get(f"{BASE_URL}/list")
    events = res.json()
    found = any(e['id'] == event_id for e in events)
    if not found:
        log("[OK] Event deletion confirmed.")
    else:
        log("[ERROR] Event still exists after deletion.")
        return False

    log("[SUCCESS] All Scheduler Tests Passed!")
    return True

if __name__ == "__main__":
    test_scheduler_flow()
