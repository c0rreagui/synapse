import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import scripts.script_env
scripts.script_env.setup_script_env()

from core.database import get_db_session
from app.models import ScheduleItem, TikTokProfile
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

def create_test_item():
    session: Session = next(get_db_session())
    
    try:
        # Get Profile ID 2 (tiktok_profile_1770307556827)
        profile = session.query(TikTokProfile).filter(TikTokProfile.id == 2).first()
        
        if not profile:
            print("Profile ID 2 not found!")
            return
            
        print(f"Using Profile: {profile.session_name} (ID: {profile.id}, Active: {profile.active})")
        
        # Create new test item
        new_item = ScheduleItem(
            profile_id=profile.id,
            video_path="/app/data/pending/ptiktok_profile_1770307556827_b52f9ed1.mp4",
            scheduled_time=datetime.now(),
            status="pending",
            metadata={
                "viral_music": True,
                "caption": "TESTE FINAL - Live Schedule Verification",
                "hashtags": ["fyp", "viral", "teste"],
                "privacy_level": "private"
            }
        )
        
        session.add(new_item)
        session.commit()
        session.refresh(new_item)
        
        print(f"\\nCreated Test Item {new_item.id}:")
        print(f"  Profile: {profile.session_name}")
        print(f"  video_path: {new_item.video_path}")
        print(f"  scheduled_time: {new_item.scheduled_time}")
        print(f"  status: {new_item.status}")
        
        return new_item.id
        
    finally:
        session.close()

if __name__ == "__main__":
    create_test_item()
