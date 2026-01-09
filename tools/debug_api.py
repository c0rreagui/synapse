
import requests

API_URL = "http://localhost:8000/api/v1/queue/approve"

payload = {
    "filename": "audit_mass_01.mp4",
    "action": "scheduled",
    "schedule_time": "2026-01-20T15:00"
}

print(f"Enviando: {payload}")
resp = requests.post(API_URL, json=payload)
print(f"Status: {resp.status_code}")
print(f"Body: {resp.text}")
