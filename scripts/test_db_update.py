
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.session_manager import update_profile_info

def test_update():
    profile_id = "tiktok_profile_1770135259969"
    info = {
        "nickname": "Vibe Cortes (Updated)",
        "active": True
    }
    success = update_profile_info(profile_id, info)
    print(f"Update Success: {success}")

if __name__ == "__main__":
    test_update()
