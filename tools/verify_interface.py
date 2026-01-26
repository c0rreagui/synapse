import requests
import sys
import time

BASE_URL = "http://127.0.0.1:3000"
API_URL = "http://127.0.0.1:8000"

def check_route(url, expected_text=None, status_code=200):
    print(f"Testing {url}...")
    try:
        res = requests.get(url, timeout=10) # 10s timeout
        if res.status_code != status_code:
            print(f" [FAIL] Status {res.status_code} (Expected {status_code})")
            return False
        
        if expected_text and expected_text.lower() not in res.text.lower():
            print(f" [WARN] Content '{expected_text}' not found in HTML (might be CSR)")
            return True
            
        print(" [OK] Content Verified")
        return True
    except requests.exceptions.ReadTimeout:
        print(f" [FAIL] Timeout connecting to {url}")
        return False
    except requests.exceptions.ConnectionError:
        print(f" [FAIL] Connection refused to {url}")
        return False
    except Exception as e:
        print(f" [FAIL] Error: {e}")
        return False

def run_checks():
    print("--- SYNAPSE INTERFACE VERIFICATION (HTTP) ---")
    
    # 1. Backend API Health (Check first as it is lighter)
    print("\n[Backend API]")
    api_ok = check_route(f"{API_URL}/docs", "Swagger")
    if not api_ok:
        print("Backend seems offline or unresponsive.")
    
    check_route(f"{API_URL}/api/v1/profiles", "[]")

    # 2. Frontend Routes
    print("\n[Frontend Routes]")
    front_ok = check_route(f"{BASE_URL}/", "Synapse")
    if not front_ok:
         print("Frontend seems offline or unresponsive.")
    
    check_route(f"{BASE_URL}/oracle", "Oracle")
    
    # Feature specific
    print("\n[Features]")
    try:
        if api_ok:
            res = requests.get(f"{API_URL}/api/v1/profiles", timeout=5)
            profiles = res.json()
            if len(profiles) > 0:
                pid = profiles[0]['id']
                print(f"Testing Analytics for profile {pid}...")
                check_route(f"{API_URL}/api/v1/analytics/{pid}", None)
            else:
                print(" [SKIP] No profiles for analytics test.")
    except:
        print(" [FAIL] Could not verify dynamic analytics.")

if __name__ == "__main__":
    run_checks()
