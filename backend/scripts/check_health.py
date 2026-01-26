
import requests
import sys

try:
    print("Checking Backend Health...")
    resp = requests.get("http://127.0.0.1:8000/api/v1/oracle/status", timeout=2)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Backend unreachable: {e}")
