
import requests
import sys

username = sys.argv[1] if len(sys.argv) > 1 else 'vibecortes'
url = f"http://127.0.0.1:8000/api/v1/oracle/full-scan/{username}"

print(f"Triggering scan for {username} @ {url}")
try:
    r = requests.post(url)
    print(f"Status: {r.status_code}")
    print(r.text[:500]) # First 500 chars
except Exception as e:
    print(f"Error: {e}")
