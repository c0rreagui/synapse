import script_env
script_env.setup_script_env()

from core.database import SessionLocal
from core.models import ScheduleItem

db = SessionLocal()
item = db.query(ScheduleItem).filter(ScheduleItem.id == 31).first()
if item:
    print(f"Status: {item.status}")
    print(f"Error: {item.error_message}")
else:
    print("Item not found")
db.close()
