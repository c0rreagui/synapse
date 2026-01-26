import requests

try:
    print("Hitting refresh endpoint...")
    resp = requests.post("http://127.0.0.1:8000/api/v1/profiles/refresh-avatar/123") # Dummy ID
    print(f"Status: {resp.status_code}")
    print("Response Body:")
    print(resp.text)
except Exception as e:
    print(e)
