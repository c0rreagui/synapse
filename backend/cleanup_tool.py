import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from core.models import ScheduleItem

def cleanup():
    db = SessionLocal()
    try:
        # Check if model has profile_id or profile_slug
        # We'll inspect the model class first or try/except
        
        print("Cleaning up phantom events...")
        target_field = getattr(ScheduleItem, 'profile_id', None)
        if not target_field:
             target_field = getattr(ScheduleItem, 'profile_slug', None)
             
        if not target_field:
            print("ERROR: Could not find profile_id or profile_slug on ScheduleItem")
            return

        # Delete 'ptiktok_' events
        deleted = db.query(ScheduleItem).filter(
            target_field.like("ptiktok_%")
        ).delete(synchronize_session=False)
        
        db.commit()
        print(f"SUCCESS: Deleted {deleted} phantom events.")
        
    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup()
