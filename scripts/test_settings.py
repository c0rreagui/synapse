import requests
import json
import os
import sys

# Constants
API_URL = "http://localhost:8000/api/v1/system/settings"
HEALTH_URL = "http://localhost:8000/api/v1/system/system/health"

def test_settings_api():
    print("🧪 Testing Settings API (SYN-50)...")
    
    # 1. Check Health
    try:
        resp = requests.get(HEALTH_URL)
        if resp.status_code == 200:
            print(f"   ✅ System Health: {resp.json()}")
        else:
            print(f"   ❌ System Health Failed: {resp.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Connection Error (Server might be reloading?): {e}")
        return

    # 2. Get Initial Settings
    try:
        resp = requests.get(API_URL)
        initial = resp.json()
        print("   ✅ GET /settings success")
        # print(json.dumps(initial, indent=2))
    except Exception as e:
        print(f"   ❌ GET /settings failed: {e}")
        return

    # 3. Update Settings
    # We will update a safe field: system.log_level
    new_settings = {
        "system": {
            "log_level": "DEBUG",
            "test_timestamp": "verification_run"
        }
    }
    
    print("\n   Changing Log Level to DEBUG...")
    try:
        resp = requests.post(API_URL, json={"settings": new_settings})
        if resp.status_code == 200:
             print("   ✅ POST /settings success")
             updated_resp = resp.json()
             if updated_resp.get("system", {}).get("log_level") == "DEBUG":
                 print("   ✅ Value Update Verified in Response")
             else:
                 print("   ❌ Value NOT updated in response")
        else:
             print(f"   ❌ POST failed: {resp.status_code} {resp.text}")
             return
    except Exception as e:
        print(f"   ❌ POST failed: {e}")
        return

    # 4. Verify Persistence (GET again)
    resp = requests.get(API_URL)
    final = resp.json()
    if final.get("system", {}).get("log_level") == "DEBUG":
        print("   ✅ Persistence Verified (GET returns new value)")
    else:
        print("   ❌ Persistence Failed")

if __name__ == "__main__":
    test_settings_api()
