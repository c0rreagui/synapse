
import sys
import os
from sqlalchemy import text
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from core.database import SessionLocal

def check_status():
    db = SessionLocal()
    try:
        print("--- CHECKING ITEM 4 & PROFILE ---")
        
        # Check Item 4
        result = db.execute(text("SELECT id, status, scheduled_time, error_message, profile_slug FROM schedule WHERE id=4"))
        item = result.fetchone()
        if item:
            print(f"ITEM 4: Status={item[1]} | Time={item[2]} | Profile={item[4]}")
            print(f"ERROR MSG: {item[3]}")
        else:
            print("Item 4 not found.")

        # Check Profile
        if item:
            slug = item[4]
            p_result = db.execute(text(f"SELECT slug, label, active FROM profiles WHERE slug='{slug}'"))
            prof = p_result.fetchone()
            if prof:
                 print(f"PROFILE: {prof[0]} ({prof[1]}) | Active={prof[2]}")
            else:
                 print(f"Profile {slug} not found.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_status()
