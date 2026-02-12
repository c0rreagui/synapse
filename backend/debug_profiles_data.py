
import sys
import os
import asyncio
import json

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.session_manager import list_available_sessions
from core.database import SessionLocal
from core.models import Profile

def debug_profiles():
    print("=== DEBUGGING PROFILE DATA ===")
    
    # 1. Check DB Raw
    db = SessionLocal()
    profiles_db = db.query(Profile).all()
    print(f"\n[DB] Found {len(profiles_db)} profiles in SQLite:")
    for p in profiles_db:
        print(f"  - Slug: {p.slug}")
        print(f"    Label: {p.label}")
        print(f"    Active: {p.active}")
        print(f"    Stats: {p.last_seo_audit}")
    db.close()

    # 2. Check Manager Output (What API sends)
    print("\n[MANAGER] list_available_sessions output:")
    try:
        sessions = list_available_sessions()
        print(json.dumps(sessions, indent=2, default=str))
    except Exception as e:
        print(f"ERROR calling list_available_sessions: {e}")

if __name__ == "__main__":
    debug_profiles()
