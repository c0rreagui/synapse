
import os
import sys
import shutil
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.scheduler import Scheduler
from core.config import DATA_DIR

def recover_schedule():
    print("--- STARTING SCHEDULE RECOVERY ---")
    
    pending_dir = os.path.join(DATA_DIR, "pending")
    approved_dir = os.path.join(DATA_DIR, "approved")
    
    # Ensure dirs exist
    os.makedirs(pending_dir, exist_ok=True)
    os.makedirs(approved_dir, exist_ok=True)
    
    # 1. Move everything from APPROVED -> PENDING (Reset state)
    approved_files = [f for f in os.listdir(approved_dir) if f.endswith(".mp4") or f.endswith(".json")]
    for f in approved_files:
        src = os.path.join(approved_dir, f)
        dst = os.path.join(pending_dir, f)
        shutil.move(src, dst)
        print(f"MOVED {f} from Approved -> Pending")
        
    # 2. Iterate PENDING and Schedule
    scheduler = Scheduler()
    
    pending_files = [f for f in os.listdir(pending_dir) if f.endswith(".mp4")]
    print(f"Found {len(pending_files)} pending videos.")
    
    # Start scheduling from NOW + 15 mins
    sp_tz = ZoneInfo("America/Sao_Paulo")
    next_time = datetime.now(sp_tz) + timedelta(minutes=15)
    
    count = 0
    for video_file in pending_files:
        video_path = os.path.join(pending_dir, video_file)
        json_path = video_path + ".json"
        
        # Default metadata
        meta = {}
        caption = ""
        profile_slug = "unknown"
        
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as jf:
                    meta = json.load(jf)
                    caption = meta.get("caption", "")
                    # Extract profile from metadata or filename
                    profile_slug = meta.get("profile_id", "")
            except Exception as e:
                print(f"Error reading JSON for {video_file}: {e}")
        
        # Fallback profile extraction from filename if missing
        # Format: ptiktok_profile_TIMESTAMP_HASH.mp4
        if not profile_slug and "ptiktok_profile_" in video_file:
             parts = video_file.split("_")
             if len(parts) >= 3:
                 profile_slug = f"{parts[0]}_{parts[1]}_{parts[2]}" # ptiktok_profile_123...
        
        if not profile_slug:
            print(f"Skipping {video_file}: Could not determine profile.")
            continue
            
        # Add hashtags to caption if present
        if "oracle_analysis" in meta and "hashtags" in meta["oracle_analysis"]:
            hashtags = " ".join(meta["oracle_analysis"]["hashtags"])
            if hashtags and hashtags not in caption:
                caption += f"\n\n{hashtags}"

        print(f"Scheduling {video_file} for {next_time} (Profile: {profile_slug})")
        
        try:
            scheduler.add_event(
                profile_id=profile_slug,
                video_path=video_path,
                scheduled_time=next_time.isoformat(),
                caption=caption,
                privacy_level=meta.get("privacy_level", "public"),
                viral_music_enabled=meta.get("viral_music_enabled", False)
            )
            count += 1
            # Increment time by 30 mins
            next_time += timedelta(minutes=30)
            
        except Exception as e:
            print(f"FAILED to schedule {video_file}: {e}")

    print(f"--- RECOVERY COMPLETE. Scheduled {count} items. ---")

if __name__ == "__main__":
    recover_schedule()
