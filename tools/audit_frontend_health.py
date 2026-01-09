
import requests

BASE_URL = "http://localhost:3000"

ROUTES = [
    "/",
    "/logs",
    "/metrics",
    "/factory",
    "/config" # Se existir, se não 404
]

print("🎨 Frontend SSR Health Check")

for route in ROUTES:
    url = f"{BASE_URL}{route}"
    try:
        resp = requests.get(url)
        print(f"  Route {route}: {resp.status_code}")
        
        # Check title basic
        if "<title>" in resp.text:
             start = resp.text.find("<title>") + 7
             end = resp.text.find("</title>")
             print(f"    Title: {resp.text[start:end]}")
        else:
             print("    ⚠️ No title found (CSR only?)")
             
    except Exception as e:
        print(f"  ❌ Failed to reach {url}: {e}")
