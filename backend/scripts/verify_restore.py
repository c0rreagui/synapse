import requests

API_URL = "http://127.0.0.1:8000/api/v1"

def check_data():
    print("[TEST] Checking Restored Data...")
    try:
        # Check Profiles
        res = requests.get(f"{API_URL}/profiles/list")
        profiles = res.json()
        print(f"[INFO] Profiles found: {len(profiles)}")
        for p in profiles:
            print(f" - {p.get('label')} ({p.get('id')})")
            
        # Check Schedule
        res = requests.get(f"{API_URL}/scheduler/list")
        events = res.json()
        print(f"[INFO] Events found: {len(events)}")
        
        if len(profiles) > 0:
            print("[SUCCESS] Data restored successfully.")
        else:
            print("[WARNING] Database valid but empty?")
            
    except Exception as e:
        print(f"[FAIL] Check failed: {e}")

if __name__ == "__main__":
    check_data()
