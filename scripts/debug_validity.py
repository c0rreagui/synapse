import sys
import os
import json
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
sys.path.append(BACKEND_DIR)

from core.session_manager import check_cookies_validity, get_session_path

if __name__ == "__main__":
    profile_id = "tiktok_profile_1770135259969"
    path = get_session_path(profile_id)
    print(f"Checking session: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    cookies = data.get("cookies", [])
    if not cookies and isinstance(data, list):
        cookies = data
        
    print(f"Found {len(cookies)} cookies.")
    
    # Debug print the sessionid cookie
    for c in cookies:
        if c.get("name") == "sessionid":
            print("FOUND sessionid cookie:", c)
            
    is_valid = check_cookies_validity(cookies)
    print(f"check_cookies_validity returned: {is_valid}")
    
    # Manual check of logic to see what fails
    required_cookies = ["sessionid"]
    current_time = time.time()
    
    for req in required_cookies:
        found = False
        for c in cookies:
            if c.get("name") == req:
                found = True
                print(f"Checking {req} expiry...")
                expiry = c.get("expirationDate") or c.get("expires")
                print(f"Expiry value: {expiry}, Current time: {current_time}")
                if expiry:
                    if expiry < current_time:
                         print(f"FAIL: {req} expired.")
                    else:
                         print(f"PASS: {req} valid.")
                else:
                    print(f"PASS: {req} has no expiry.")
        if not found:
            print(f"FAIL: {req} missing.")
