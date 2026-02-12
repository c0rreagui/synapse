import sys
import os

# Setup Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # synapse root
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
sys.path.append(BACKEND_DIR)

from core.session_manager import update_profile_status

if __name__ == "__main__":
    profile_id = "tiktok_profile_1770135259969"
    success = update_profile_status(profile_id, True)
    if success:
        print(f"Successfully set {profile_id} to ACTIVE.")
    else:
        print(f"Failed to update {profile_id}.")
