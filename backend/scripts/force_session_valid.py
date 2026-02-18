
import sys
import os
import json
import time

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import SESSIONS_DIR

def extend_cookies(slug):
    path = os.path.join(SESSIONS_DIR, f"{slug}.json")
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cookies = []
        if isinstance(data, list):
            cookies = data
        elif isinstance(data, dict):
            cookies = data.get("cookies", [])
        
        # Future timestamp (1 year from now)
        future_time = time.time() + 31536000
        
        count = 0
        for c in cookies:
            if "expires" in c:
                c["expires"] = future_time
                count += 1
            if "expirationDate" in c:
                c["expirationDate"] = future_time
                count += 1
                
        # Save back
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        print(f"Extended {count} cookies for {slug}")
        
    except Exception as e:
        print(f"Error extending cookies for {slug}: {e}")

if __name__ == "__main__":
    extend_cookies("tiktok_profile_1770135259969") # Vibe Cortes
    extend_cookies("tiktok_profile_1770307556827") # Opiniao Viral
