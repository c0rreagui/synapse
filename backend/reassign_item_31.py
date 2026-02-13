from core.database import SessionLocal
from core.models import ScheduleItem

db = SessionLocal()
item = db.query(ScheduleItem).filter(ScheduleItem.id == 31).first()
if item:
    print(f"Item 31 old profile: {item.profile_slug}")
    # Assign to opiniaoviral (ID 2, Slug tiktok_profile_1770307556827)
    item.profile_slug = "tiktok_profile_1770307556827"
    db.commit()
    print(f"Item 31 new profile: {item.profile_slug}")
else:
    print("Item 31 not found!")
db.close()
