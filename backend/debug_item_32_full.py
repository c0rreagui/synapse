import sys
import json
from core.database import SessionLocal
from core.models import ScheduleItem

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

db = SessionLocal()
item = db.query(ScheduleItem).filter(ScheduleItem.id == 32).first()

if item:
    print(f"ID: {item.id}")
    print(f"Status: {item.status}")
    print(f"Error Message: {item.error_message}")
    print(f"Metadata Info: {json.dumps(item.metadata_info, ensure_ascii=False, indent=2)}")
    
else:
    print("Item 32 not found")

db.close()
