
import sys
import os
import json
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from core.session_manager import check_cookies_validity

def test_session():
    session_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'data', 'sessions', 'tiktok_profile_1770307556827.json')
    
    print(f"Testing session file: {session_path}")
    
    if not os.path.exists(session_path):
        print("❌ File not found!")
        return

    try:
        with open(session_path, 'r') as f:
            data = json.load(f)
            
        cookies = data.get('cookies', [])
        if not cookies:
            print("❌ No cookies found in 'cookies' key.")
            return

        is_valid = check_cookies_validity(cookies)
        
        if is_valid:
            print("[OK] Session Validity Check: PASSED")
            # Print expiration of sessionid for confirmation
            for c in cookies:
                if c['name'] == 'sessionid':
                    print(f"   sessionid expiry: {c.get('expirationDate')} (Unix)")
        else:
             print("[FAIL] Session Validity Check: FAILED (Expired or Missing required cookies)")

    except Exception as e:
        print(f"[ERROR] Exception during test: {e}")

if __name__ == "__main__":
    test_session()
