
import requests
import json
import time

def trigger_delete():
    # 1. Create a dummy profile to ensure we have something to delete
    print("Creating dummy profile...")
    try:
        res = requests.post("http://127.0.0.1:8000/api/v1/profiles/import", json={
            "label": "Boom Profile",
            "cookies_json": '[{"name": "x", "value": "y", "domain": ".tiktok.com"}]'
        })
        if res.status_code == 200:
            profile_id = res.json()["id"]
            print(f"Created: {profile_id}")
        else:
            # Maybe it already exists? Just try to verify via list
            print(f"Create status: {res.status_code}")
            # List profiles
            list_res = requests.get("http://127.0.0.1:8000/api/v1/profiles/list")
            profiles = list_res.json()
            if profiles:
                profile_id = profiles[0]["id"]
                print(f"Using existing: {profile_id}")
            else:
                print("No profiles to delete!")
                return
    except Exception as e:
        print(f"Setup failed: {e}")
        return

    # 2. Delete it
    print(f"Deleting {profile_id}...")
    try:
        del_res = requests.delete(f"http://127.0.0.1:8000/api/v1/profiles/{profile_id}")
        print(f"Delete Status: {del_res.status_code}")
        print(f"Delete Body: {del_res.text}")
    except Exception as e:
        print(f"Delete request failed: {e}")

if __name__ == "__main__":
    trigger_delete()
