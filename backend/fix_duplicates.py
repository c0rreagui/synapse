
import os
import sys
from collections import defaultdict

# Setup paths
sys.path.append(os.path.join(os.getcwd(), "backend"))

from core.database import SessionLocal
from core.models import ScheduleItem

def fix_duplicates():
    db = SessionLocal()
    try:
        # Fetch all pending items
        items = db.query(ScheduleItem).filter(ScheduleItem.status == 'pending').all()
        
        # Group by unique signature
        grouped = defaultdict(list)
        for item in items:
            # Signature: Profile + Video Path + Time
            sig = (item.profile_slug, item.video_path, item.scheduled_time)
            grouped[sig].append(item)
            
        deleted_count = 0
        
        for sig, item_list in grouped.items():
            if len(item_list) > 1:
                # keep the one with lowest ID (created first) or highest ID? 
                # usually keep first created.
                item_list.sort(key=lambda x: x.id)
                keep = item_list[0]
                remove = item_list[1:]
                
                print(f"Duplicate Group Found for {sig}: Keeping ID {keep.id}, Removing IDs {[x.id for x in remove]}")
                
                for r in remove:
                    db.delete(r)
                    deleted_count += 1
        
        if deleted_count > 0:
            db.commit()
            print(f"SUCCESS: Removed {deleted_count} duplicate items.")
        else:
            print("No duplicates found.")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_duplicates()
