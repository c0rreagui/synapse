
import sys
import os
from sqlalchemy import text
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from core.database import SessionLocal

def fix_db():
    db = SessionLocal()
    try:
        print("--- FIXING DB STATE ---")
        
        # 1. Activate Opinião Viral (slug=tiktok_profile_1770307556827)
        slug = "tiktok_profile_1770307556827"
        print(f"Activating profile {slug}...")
        db.execute(text(f"UPDATE profiles SET active=1 WHERE slug='{slug}'"))
        
        # 2. Reschedule Failed Item (ID 4)
        # Set to 2 mins from now to give time for scheduler to pick it up
        new_time = (datetime.now() + timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M:%S')
        item_id = 4
        
        print(f"Rescheduling Item {item_id} to {new_time}...")
        db.execute(text(f"UPDATE schedule SET status='pending', scheduled_time='{new_time}', error_message=NULL WHERE id={item_id}"))
        
        db.commit()
        print("✅ DB Updates Committed.")
        
        # Verify
        result = db.execute(text(f"SELECT id, status, scheduled_time FROM schedule WHERE id={item_id}"))
        for row in result:
             print(f"Item {row[0]} Status: {row[1]} | Time: {row[2]}")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_db()
