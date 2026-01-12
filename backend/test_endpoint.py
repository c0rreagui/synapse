import urllib.request
import urllib.parse
import json

url = "http://localhost:8000/api/v1/oracle/analyze?username=vibe.corteseclips"
print(f"Testing POST to {url}")

try:
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req) as response:
        print(f"Status: {response.status}")
        data = response.read()
        print(f"Response: {data.decode('utf-8')[:500]}...") # Print first 500 chars
        print("--- SUCCESS ---")
except urllib.error.HTTPError as e:
    print(f"--- FAILED: HTTP {e.code} ---")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"--- FAILED: {e} ---")
