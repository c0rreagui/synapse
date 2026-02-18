
import script_env
script_env.setup_script_env()
from core.database import SessionLocal
from core.models import ScheduleItem

def debug():
    db = SessionLocal()
    item = db.query(ScheduleItem).filter(ScheduleItem.id == 31).first()
    if item:
        print(f"ID: {item.id}")
        print(f"Status: {item.status}")
        print(f"Error: {item.error_message}")
        print(f"Scheduled Time: {item.scheduled_time}")
        print(f"Updated At: {item.updated_at}")
    else:
        print("Item 31 NOT FOUND")
    db.close()

if __name__ == "__main__":
    debug()
