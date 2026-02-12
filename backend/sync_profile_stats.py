
import os
import sys
import json
import logging

# Setup paths
sys.path.append(os.path.join(os.getcwd(), "backend"))

from core.database import SessionLocal
from core.models import Profile, ScheduleItem
from core.session_manager import list_available_sessions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_profiles():
    db = SessionLocal()
    try:
        # 1. Get all session files (Source of Truth for Auth/Avatar)
        sessions = list_available_sessions()
        
        print(f"Found {len(sessions)} sessions on disk.")
        
        for session in sessions:
            slug = session.get('id')
            label = session.get('label')
            avatar = session.get('avatar_url')
            username = session.get('username')
            
            # 2. Find or Create in DB
            profile = db.query(Profile).filter(Profile.slug == slug).first()
            
            if not profile:
                print(f"CREATE Profile in DB: {slug}")
                profile = Profile(
                    slug=slug,
                    label=label,
                    username=username,
                    avatar_url=avatar,
                    active=True
                )
                db.add(profile)
            else:
                # Update existing
                if avatar and avatar != profile.avatar_url:
                    print(f"UPDATE Avatar for {slug}")
                    profile.avatar_url = avatar
                
                if username and username != profile.username:
                    profile.username = username
                    
                if label and label != profile.label:
                    profile.label = label
                    
            # 3. Calculate Real Stats from DB
            # Count 'posted' or 'completed' items
            upload_count = db.query(ScheduleItem).filter(
                ScheduleItem.profile_slug == slug,
                ScheduleItem.status.in_(['posted', 'completed', 'published'])
            ).count()
            
            # Update metadata in JSON (so frontend sees it immediately if it uses JSON)
            # But the Source of Truth for frontend "list" is session_manager.list_available_sessions
            # which reads JSON.
            
            # UPDATE JSON SIDE
            from core.session_manager import update_profile_metadata
            update_profile_metadata(slug, {"uploads_count": upload_count})
            print(f"SYNC Stats for {slug}: {upload_count} uploads")
            
        db.commit()
        print("SYNC COMPLETE.")
        
    except Exception as e:
        print(f"Error syncing: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    sync_profiles()
