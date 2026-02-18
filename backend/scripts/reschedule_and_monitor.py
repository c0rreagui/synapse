import script_env
script_env.setup_script_env()

import time
import sys
from datetime import datetime
from core.database import SessionLocal
from core.models import ScheduleItem, Profile
from core.scheduler import Scheduler

ITEM_ID = 31
TARGET_TIME_STR = "2026-02-14T22:55:00"

def reschedule():
    print(f"[SCRIPT] Rescheduling Item {ITEM_ID} to {TARGET_TIME_STR}...")
    try:
        scheduler = Scheduler()
        result = scheduler.update_event(str(ITEM_ID), scheduled_time=TARGET_TIME_STR)
        if result:
            print(f"[SUCCESS] Reschedule Success: {result['status']} @ {result['scheduled_time']}")
        else:
            print("[ERROR] Reschedule Failed")
    except Exception as e:
        print(f"[ERROR] Exception in reschedule: {e}")

def debug_profile_mismatch(item):
    """Check why manual run thought profile was inactive"""
    print("[DEBUG] Debugging Profile Info...")
    db = SessionLocal()
    try:
        # 1. Profile linked in Item
        print(f"Item Profile Slug: {item.profile_slug}")
        p1 = db.query(Profile).filter(Profile.slug == item.profile_slug).first()
        if p1:
            print(f"Profile [DB Linked] ({p1.slug}): Active={p1.active}, Label={p1.label}")
        else:
            print(f"Profile [DB Linked] ({item.profile_slug}) NOT FOUND")

        # 2. Profile from Filename
        import os
        fname = os.path.basename(item.video_path)
        print(f"Video Filename: {fname}")
        
        import re
        match = re.search(r'p?(tiktok_profile_\d+)', fname)
        if match:
             extracted_slug = match.group(1)
             print(f"Extracted Slug from file: {extracted_slug}")
             
             p2 = db.query(Profile).filter(Profile.slug == extracted_slug).first()
             if p2:
                 print(f"Profile [File Extracted] ({p2.slug}): Active={p2.active}, Label={p2.label}")
             else:
                 print(f"Profile [File Extracted] ({extracted_slug}) NOT FOUND")
        else:
             print("Could not extract slug from filename")

    except Exception as e:
        print(f"[ERROR] Debugging profile failed: {e}")
    finally:
        db.close()

def monitor():
    print("[MONITOR] Starting monitoring...")
    last_status = None
    
    # Run loop
    for i in range(120): # 10 minutes
        db = SessionLocal()
        try:
            item = db.query(ScheduleItem).filter(ScheduleItem.id == ITEM_ID).first()
            
            if not item:
                print("[ERROR] Item disappeared!")
                break
                
            status = item.status
            if status != last_status:
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"[{timestamp}] Status changed: {last_status} -> {status}")
                last_status = status
                
                if status == 'failed':
                    print(f"[FAILED] Error Message: {item.error_message}")
                    debug_profile_mismatch(item)
                    # Don't break immediately, keep monitoring in case of retry or manual fix logic? 
                    # Actually, if failed, it's done usually.
                    break
                if status in ['posted', 'completed']:
                     print(f"[SUCCESS] URL: {item.published_url}")
                     break
            
            if i % 12 == 0: # Every minute approx
                 print(f"[{datetime.now().strftime('%H:%M:%S')}] Current Status: {status}")
                 
        except Exception as e:
            print(f"[ERROR] Monitor loop error: {e}")
        finally:
            db.close()
        
        time.sleep(5)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--item_id", type=int, default=31)
    parser.add_argument("--time", type=str, default="2026-02-14T23:20:00")
    args = parser.parse_args()

    ITEM_ID = args.item_id
    TARGET_TIME_STR = args.time

    reschedule()
    monitor()
