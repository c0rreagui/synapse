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
        print(f"ID: {item.id}")
        print(f"Profile: {item.profile_slug}")
        print(f"Status: {item.status}")
        print(f"Video Path: {item.video_path}")
        print(f"Video Path Type: {type(item.video_path)}")
        print(f"Video Path Length: {len(item.video_path) if item.video_path else 0}")
    else:
        print("Item 31 not found.")
finally:
    db.close()
