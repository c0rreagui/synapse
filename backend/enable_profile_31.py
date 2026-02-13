import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.database import SessionLocal
from core.models import ScheduleItem, Profile

db = SessionLocal()
item = db.query(ScheduleItem).filter(ScheduleItem.id == 31).first()
item = db.query(ScheduleItem).filter(ScheduleItem.id == 31).first()
if item:
    print(f"Item 31 belongs to profile: {item.profile_slug}")
    
    # Debug: List all profiles
    profiles = db.query(Profile).all()
    print("Available Profiles:")
    target_profile = None
    for p in profiles:
        print(f"ID: {p.id}, Slug: {p.slug}, Username: {p.username}, Active: {p.active}")
        # Try fuzzy match
        if p.slug == item.profile_slug or p.username == item.profile_slug or str(p.id) == item.profile_slug:
            target_profile = p
            
    if target_profile:
        print(f"Found Match! ID: {target_profile.id}")
        target_profile.active = True # Note: Model uses 'active' not 'is_active' based on models.py line 15
        db.commit()
        print(f"Enabled Profile {target_profile.slug}")
    else:
        print("Still no match found.")
else:
    print("Item 31 not found!")
db.close()
