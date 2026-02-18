import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.database import SessionLocal
from core.models import ScheduleItem

def check_internal():
    db = SessionLocal()
    items = db.query(ScheduleItem).filter(ScheduleItem.id.in_([41, 42])).all()
    print(f"--- DB CHECK INSIDE DOCKER ---")
    for i in items:
        print(f"ID {i.id}: Status={i.status} Time={i.scheduled_time}")
    print(f"------------------------------")
    db.close()

if __name__ == "__main__":
    check_internal()
