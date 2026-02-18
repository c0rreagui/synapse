import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import scripts.script_env
scripts.script_env.setup_script_env()

from core.database import SessionLocal
from core.models import ScheduleItem

db = SessionLocal()
try:
    item = db.query(ScheduleItem).filter(ScheduleItem.id == 31).first()
    if item:
        print(f"BEFORE: {item.video_path}")
        
        # Extract just the filename
        old_path = item.video_path
        filename = "ptiktok_profile_1770135259969_ec1ec4e1.mp4"
        new_path = f"/app/data/pending/{filename}"
        
        item.video_path = new_path
        db.commit()
        db.refresh(item)
        
        print(f"AFTER: {item.video_path}")
        print("Fixed Item 31 video path.")
    else:
        print("Item 31 not found.")
finally:
    db.close()
