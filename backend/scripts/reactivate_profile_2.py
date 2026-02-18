
import asyncio
import os
import sys

# Add backend to path (d:\...\Synapse\backend)
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import scripts.script_env # Ensure env is loaded
scripts.script_env.setup_script_env() # Call setup!
from core.database import SessionLocal
from core.models import Profile

def reactivate():
    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.id == 2).first()
        if profile:
            print(f"Profile {profile.slug} (ID: 2) Active: {profile.active}")
            profile.active = True
            db.commit()
            db.refresh(profile)
            print(f"Profile {profile.slug} (ID: 2) REACTIVATED. Current State: {profile.active}")
        else:
            print("Profile ID 2 not found.")
    finally:
        db.close()

if __name__ == "__main__":
    reactivate()
