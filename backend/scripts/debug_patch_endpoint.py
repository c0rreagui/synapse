import requests
import json
from datetime import datetime, timedelta

API_URL = "http://localhost:8000/api/v1/scheduler"

def debug_patch():
    # 1. List events
    print("Fetching events...")
    try:
        res = requests.get(f"{API_URL}/list")
        if res.status_code != 200:
            print(f"List failed: {res.status_code} - {res.text}")
            return
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    events = res.json()
    if not events:
        print("No events found to test.")
        return

    target = events[0]
    print(f"Targeting event: {target['id']} (Current time: {target['scheduled_time']})")
    
    # 2. Prepare Payload
    # Add 1 hour
    current_dt = datetime.fromisoformat(target['scheduled_time'].replace("Z", "+00:00"))
    new_time = (current_dt + timedelta(hours=1)).isoformat()
    
    payload = {"scheduled_time": new_time}
    print(f"Sending PATCH with payload: {payload}")
    
    # 3. Patch
    try:
        patch_res = requests.patch(f"{API_URL}/{target['id']}", json=payload)
        print(f"PATCH Status: {patch_res.status_code}")
        print(f"PATCH Body: {patch_res.text}")
        
    except Exception as e:
        print(f"PATCH Request failed: {e}")

if __name__ == "__main__":
    debug_patch()
