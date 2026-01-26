import requests
import sys

try:
    print("... Pinging Backend at http://127.0.0.1:8000/api/v1/status...")
    resp = requests.get("http://127.0.0.1:8000/api/v1/status", timeout=5)
    if resp.status_code == 200:
        print("OK: Backend ONLINE!")
        print(f"Response: {resp.json()}")
    else:
        print(f"WARN: Backend returned status {resp.status_code}")
        print(resp.text)
except Exception as e:
    print(f"ERROR: Could not connect to Backend: {e}")
    print("Make sure the server is running: 'uvicorn main:app --reload'")
