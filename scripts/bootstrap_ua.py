
import os
import json

def bootstrap_ua(profile_id, ua):
    path = f"backend/data/sessions/{profile_id}.json"
    if not os.path.exists(path):
         print(f"Error: {path} not found")
         return
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
         data = {"cookies": data, "origins": []}
    
    if "synapse_meta" not in data:
         data["synapse_meta"] = {}
    
    data["synapse_meta"]["user_agent"] = ua
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Updated {profile_id} with UA: {ua}")

if __name__ == "__main__":
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    bootstrap_ua("tiktok_profile_1770135259969", ua)
