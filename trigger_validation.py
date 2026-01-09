import urllib.request
import json
import time

BASE_URL = "http://localhost:8000/api/v1/profiles/validate"
PROFILES = ["tiktok_profile_01", "tiktok_profile_02"]

for pid in PROFILES:
    print(f"Triggering validation for {pid}...")
    try:
        req = urllib.request.Request(f"{BASE_URL}/{pid}", method="POST")
        with urllib.request.urlopen(req, timeout=120) as response:
            data = json.loads(response.read().decode())
            print(f"SUCCESS {pid}: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"FAILED {pid}: {e}")
