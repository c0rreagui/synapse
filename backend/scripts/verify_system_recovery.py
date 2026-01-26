import requests
import sqlite3
import os
import sys

# Add parent dir to path to import core modules if needed, 
# although we should rely on API for external test.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_URL = "http://127.0.0.1:8000/api/v1"
DB_PATH = "../synapse.db"

def test_health():
    print(f"[TEST] Checking Backend Health at {API_URL}/status...")
    try:
        res = requests.get(f"{API_URL}/status")
        if res.status_code == 200:
            print("[OK] Backend is Online")
            return True
        else:
            print(f"[FAIL] Backend returned {res.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Connection failed: {e}")
        return False

def test_db_direct():
    print(f"[TEST] Checking Database at {DB_PATH}...")
    try:
        if not os.path.exists(DB_PATH):
            print("[FAIL] DB file not found")
            return False
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check profiles table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profiles'")
        if cursor.fetchone():
            print("[OK] Table 'profiles' exists")
        else:
            print("[FAIL] Table 'profiles' MISSING")
            return False
            
        conn.close()
        return True
    except Exception as e:
        print(f"[FAIL] DB Check failed: {e}")
        return False

def test_create_profile():
    print("[TEST] Creating Test Profile via API...")
    payload = {
        "label": "Test User",
        "cookies": "[]"  # Valid JSON string required
    }
    try:
        # First check if exists
        res = requests.get(f"{API_URL}/profiles/list")
        existing = [p for p in res.json() if p['label'] == "Test User"]
        if existing:
            print("[INFO] Profile already exists, skipping create.")
            return True

        res = requests.post(f"{API_URL}/profiles/import", json=payload)
        if res.status_code in [200, 201]:
            print("[OK] Profile Created Successfully")
            return True
        else:
            print(f"[FAIL] Failed to create profile: {res.text}")
            return False
    except Exception as e:
        print(f"[FAIL] Profile API failed: {e}")
        return False

def test_schedule_event():
    print("[TEST] Scheduling Video via API...")
    # We need a profile ID first.
    try:
        res = requests.get(f"{API_URL}/profiles/list")
        profiles = res.json()
        if not profiles:
            print("[FAIL] No profiles found to schedule for.")
            return False
            
        profile_id = profiles[0]['id']
        
        # Use a dummy video path
        payload = {
            "profile_id": profile_id,
            "video_path": "C:/Fake/Path/video.mp4",
            "scheduled_time": "2026-01-27T10:00:00",
            "viral_music_enabled": False
        }
        
        res = requests.post(f"{API_URL}/scheduler/create", json=payload)
        if res.status_code == 200:
            print("[OK] Event Scheduled Successfully")
            return True
        elif res.status_code == 409:
            print("[OK] Conflict Logic Working (Received 409 as expected if slot taken)")
            return True
        else:
            print(f"[FAIL] Schedule failed: {res.text}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Scheduler API failed: {e}")
        return False

if __name__ == "__main__":
    print("=== SYNAPSE RECOVERY VERIFICATION ===")
    health = test_health()
    db = test_db_direct()
    
if __name__ == "__main__":
    print("=== SYNAPSE RECOVERY VERIFICATION ===")
    health = test_health()
    db = test_db_direct()
    
    # Run API tests even if DB check fails, to confirm end-to-end flow
    if health:
        prof = test_create_profile()
        if prof:
            test_schedule_event()
    
    print("=== END ===")
