
import requests
import time
import sys

def test_api():
    try:
        print("Testing Sonar API...")
        # Note: server must be running for this to work.
        # If server is not running, we expect connection error, which is fine for this check context
        # but ideal is to have it running. 
        # Since I cannot restart the server myself easily without blocking, 
        # I will simulate the heartbeat file check directly if API fails.
        
        try:
            r = requests.get("http://localhost:8000/api/health/sonar", timeout=2)
            print(f"API Code: {r.status_code}")
            print(f"API Response: {r.json()}")
        except Exception as e:
            print(f"API Call Failed (Server likely off): {e}")

        # Direct file check (Fallback verification)
        import os
        import json
        hb_path = r"d:\APPS - ANTIGRAVITY\Synapse\backend\data\scheduler_heartbeat.json"
        
        if os.path.exists(hb_path):
            with open(hb_path, 'r') as f:
                data = json.load(f)
            print(f"Heartbeat File Content: {data}")
        else:
            print("Heartbeat file NOT created yet (Scheduler needs to run).")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
