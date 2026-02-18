import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import scripts.script_env
scripts.script_env.setup_script_env()

from core.database import get_session
from app.models import ScheduleItem
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

def update_item_31_video():
    session: Session = next(get_session())
    
    try:
        item = session.query(ScheduleItem).filter(ScheduleItem.id == 31).first()
        
        if not item:
            print("Item 31 not found in database.")
            return
            
        print(f"Current video_path: {item.video_path}")
        
        # Use an existing file from pending
        new_path = "/app/data/pending/ptiktok_profile_1770307556827_b52f9ed1.mp4"
        
        item.video_path = new_path
        item.scheduled_time = datetime.now()
        item.status = "pending"
        item.error_message = None
        
        session.commit()
        
        print(f"Updated Item 31:")
        print(f"  video_path: {new_path}")
        print(f"  scheduled_time: {item.scheduled_time}")
        print(f"  status: {item.status}")
        
    finally:
        session.close()

if __name__ == "__main__":
    update_item_31_video()
