import json
import sys
import os
from datetime import datetime

# Fix path to import core modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.database import engine, SessionLocal, Base
from core.models import Profile, ScheduleItem, Audit

def migrate():
    print("Starting Migration: JSON -> SQLite")
    
    # 1. Create Tables
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # 2. Migrate Profiles
    profiles_path = os.path.join(os.path.dirname(__file__), "../data/profiles.json")
    if os.path.exists(profiles_path):
        with open(profiles_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        print(f"Found {len(data)} profiles in JSON.")
        
        for slug, p_data in data.items():
            # Check if exists
            existing = db.query(Profile).filter(Profile.slug == slug).first()
            if existing:
                print(f"   Skipping {slug} (already exists)")
                continue
                
            print(f"   Migrating {slug}...")
            
            # Extract basic fields
            new_profile = Profile(
                slug=slug,
                username=p_data.get("username", slug),
                label=p_data.get("label", slug),
                icon=p_data.get("icon", "User"),
                type=p_data.get("type", "cuts"),
                active=p_data.get("active", True),
                avatar_url=p_data.get("avatar_url"),
                bio=p_data.get("bio"),
                oracle_best_times=p_data.get("oracle_best_times", []),
                last_seo_audit=p_data.get("last_seo_audit", {})
            )
            db.add(new_profile)
            
    # Commit profiles first
    db.commit()
    
    # 3. Migrate Schedule
    schedule_path = os.path.join(os.path.dirname(__file__), "../data/schedule.json")
    if os.path.exists(schedule_path):
        with open(schedule_path, "r", encoding="utf-8") as f:
            s_data = json.load(f)
            
        print(f"Found {len(s_data)} schedule items.")
        
        for item in s_data:
            new_item = ScheduleItem(
                profile_slug=item.get("profile_slug", "unknown"),
                video_path=item.get("video_path"),
                scheduled_time=datetime.fromisoformat(item.get("scheduled_time")) if item.get("scheduled_time") else None,
                status=item.get("status", "pending"),
                metadata_info=item.get("metadata", {})
            )
            db.add(new_item)
            
    db.commit()
    db.close()
    print("Migration Complete!")

if __name__ == "__main__":
    migrate()
