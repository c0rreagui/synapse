import requests
import time

print("Fetching approved items...")
res = requests.get('http://localhost:8000/api/v1/items?status=approved')
if res.status_code == 200:
    items = res.json().get('items', [])
    if items:
        item = items[0]
        print(f"Found approved item: {item['id']} for profile {item['profile_id']}")
        
        # Approving the item to trigger immediate upload queue
        queue_res = requests.post('http://localhost:8000/api/v1/queue/approve', json={
            "id": item['id'],
            "action": "immediate",
            "viral_music_enabled": False,
            "privacy_level": "self_only",
            "target_profile_id": item['profile_id'] or "tiktok_profile_01"
        })
        print(f"Queue response: {queue_res.status_code} - {queue_res.text}")
    else:
        print("No 'approved' items found.")
else:
    print(f"Failed to fetch items: {res.status_code} - {res.text}")
