
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from core.database import SessionLocal

def inspect_db():
    db = SessionLocal()
    try:
        print("--- PENDING ITEMS SUMMARY ---")
        # Count items by profile_slug where status is pending
        result = db.execute(text("SELECT profile_slug, COUNT(*) FROM schedule WHERE status='pending' GROUP BY profile_slug"))
        for row in result:
            print(f"Profile: {row[0]} | Count: {row[1]}")

        print("\n--- FAILED ITEM (Around 18:40) ---")
        # Search for items failed recently or scheduled around 18:40 today (2026-02-05)
        # Using a broader window to be safe
        start_search = "2026-02-05 18:00:00"
        end_search = "2026-02-05 19:00:00"
        
        query = text(f"SELECT id, profile_slug, scheduled_time, status, video_path FROM schedule WHERE scheduled_time BETWEEN '{start_search}' AND '{end_search}'")
        result = db.execute(query)
        
        found = False
        for row in result:
            found = True
            print(f"ID: {row[0]} | Profile: {row[1]} | Time: {row[2]} | Status: {row[3]} | Video: {os.path.basename(row[4])}")
            
        if not found:
            print("No items found scheduled between 18:00 and 19:00.")

        print("\n--- ACTIVE PROFILES IN DB ---")
        result = db.execute(text("SELECT id, slug, label, active FROM profiles"))
        for row in result:
            print(f"ID: {row[0]} | Slug: {row[1]} | Label: {row[2]} | Active: {row[3]}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_db()
