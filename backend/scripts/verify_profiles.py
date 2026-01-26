
import requests
try:
    print("Fetching profiles...")
    r = requests.get("http://127.0.0.1:8000/api/v1/profiles/list")
    print(r.status_code)
    try:
        print(r.json())
    except:
        print(r.text)
except Exception as e:
    print(f"Error: {e}")
