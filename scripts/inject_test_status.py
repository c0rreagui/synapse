import sys
import os

# Add the project root to sys.path so 'core' and other modules can be found
# current script is in root/scripts, we want to add root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)
# Also add backend specifically if needed, but usually project root is enough if imports are 'core.database'
sys.path.append(os.path.join(ROOT_DIR, "backend"))

from core.database import SessionLocal
from core.models import ScheduleItem, Profile

def inject_test_status():
    db = SessionLocal()
    try:
        # 1. Ensure at least one profile is inactive
        profile = db.query(Profile).filter(Profile.username == "vibe.corteseclips").first()
        if profile:
            profile.active = False
            print(f"Profile {profile.username} set to INACTIVE (Active=0)")
        
        # 2. Find a pending/failed/ready item and set to paused_login_required
        item = db.query(ScheduleItem).filter(ScheduleItem.status != 'completed').first()
        if item:
            item.status = "paused_login_required"
            item.error_message = "Test: Session Expired - Login Required"
            db.commit()
            print(f"Schedule Item ID {item.id} (Profile: {item.profile_slug}) status set to 'paused_login_required'")
        else:
            print("No suitable schedule item found to update.")
            
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    inject_test_status()
