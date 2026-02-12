
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.database import SessionLocal
from core.models import Profile

def list_profiles():
    db = SessionLocal()
    try:
        profiles = db.query(Profile).all()
        print(f"Total Profiles: {len(profiles)}")
        for p in profiles:
            print(f"ID: {p.id} | Slug: {p.slug} | Label: {p.label} | Active: {p.active}")
    finally:
        db.close()

if __name__ == "__main__":
    list_profiles()
