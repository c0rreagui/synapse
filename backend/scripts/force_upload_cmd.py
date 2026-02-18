import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.database import SessionLocal
from core.models import ScheduleItem

# Removing problematic import
# from core.uploader_cli import upload_cli

def force_upload_41():
    db = SessionLocal()
    item = db.query(ScheduleItem).filter(ScheduleItem.id == 41).first()
    if not item:
        print("Item 41 not found")
        return

    print(f"Forcing upload for Item 41 (@{item.profile.username}) with session {item.profile.slug}")
    
    # Simulate CLI arguments
    class Args:
        session = item.profile.slug
        video = item.video_path
        caption = item.caption
        hashtags = "" # Caption already has hashtags
        privacy = "public"
        schedule = None
        
    args = Args()
    
    try:
        # Run upload directly
        # Note: upload_cli might require asyncio loop if it's async, but uploader_cli.py has a main() 
        # that runs asyncio.run. We should probably import uploader function instead.
        from core.uploader_cli import main
        # But main parses args. 
        # Let's call the cli command via subprocess if this is too complex.
        pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
    
    # Simplified: Just print the command to run
    db = SessionLocal()
    item = db.query(ScheduleItem).filter(ScheduleItem.id == 41).first()
    if item:
        from core.models import Profile
        # ScheduleItem uses profile_slug, not profile_id
        profile = db.query(Profile).filter(Profile.slug == item.profile_slug).first()
        if profile:
            # Construct command for Docker environment (/app/...)
            caption = item.metadata_info.get("caption", "") if item.metadata_info else ""
            cmd = f"python /app/core/uploader_cli.py --session {profile.slug} --video \"/app/processing/{os.path.basename(item.video_path)}\" --privacy public --caption \"{caption}\""
            print(cmd)
        else:
            print("Profile not found")
    else:
        print("Item 41 not found")
    db.close()
