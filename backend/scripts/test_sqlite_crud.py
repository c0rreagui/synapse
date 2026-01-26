import sys
import os
import asyncio
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.scheduler import scheduler_service
from core.database import SessionLocal
from core.models import ScheduleItem

def test_crud_scheduler():
    print("[TEST] Starting SQLite CRUD Test for Scheduler...")
    
    # 1. CREATE
    print("\n[1] Creating Event via Service...")
    path = "D:/videos/test.mp4"
    time_str = datetime.now().isoformat()
    # add_event(self, profile_id, video_path, scheduled_time, ...)
    # Note: Service returns a dict
    event = scheduler_service.add_event(
        profile_id="test_profile_crud", 
        video_path=path, 
        scheduled_time=time_str,
        viral_music_enabled=True,
        sound_title="Test Sound"
    )
    event_id = event['id']
    print(f"[OK] Event Created: ID={event_id}")

    # 2. READ (Via DB Direct)
    print("\n[2] Verifying in SQLite Database directly...")
    db = SessionLocal()
    item = db.query(ScheduleItem).filter(ScheduleItem.id == int(event_id)).first()
    if item:
        print(f"[OK] Found in DB: ID={item.id}, Profile={item.profile_slug}")
        print(f"   Metadata: {item.metadata_info}")
        if item.metadata_info.get('viral_music_enabled') == True:
            print("   Viral Music Verified: YES")
        else:
            print("[FAIL] Metadata Mismatch!")
    else:
        print("[FAIL] Not found in DB!")
    db.close()

    # 3. READ (Via Service)
    print("\n[3] Verifying via Service load_schedule()...")
    all_events = scheduler_service.load_schedule()
    found = False
    for e in all_events:
        if str(e['id']) == str(event_id):
            print(f"[OK] Found in Service List: {e['id']}")
            found = True
            break
    if not found:
        print("[FAIL] Not found in Service List!")

    # 4. DELETE
    print("\n[4] Deleting via Service...")
    scheduler_service.delete_event(event_id)
    
    # 5. VERIFY DELETE
    db = SessionLocal()
    item_deleted = db.query(ScheduleItem).filter(ScheduleItem.id == int(event_id)).first()
    if not item_deleted:
        print("[OK] Correctly removed from DB.")
    else:
        print("[FAIL] Valid Item still exists in DB!")
    db.close()

def test_crud_profile():
    print("\n[TEST] Starting SQLite CRUD Test for Profile...")
    from core.session_manager import import_session, get_profile_metadata, list_available_sessions
    from core.models import Profile
    
    # 1. CREATE (Import)
    print("\n[1] Importing Profile via Service...")
    # Mock cookie json
    cookies = '[{"name": "test", "value": "123", "domain": ".tiktok.com"}]'
    try:
        pid = import_session("Test User SQLite", cookies)
        print(f"[OK] Profile Imported: {pid}")
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return

    # 2. READ (Via Service - Metadata)
    print("\n[2] Verifying Metadata via Service...")
    meta = get_profile_metadata(pid)
    if meta.get("label") == "Test User SQLite":
        print(f"[OK] Metadata Label matches: {meta['label']}")
    else:
        print(f"[FAIL] Label mismatch: {meta}")

    # 3. READ (Via Service - List)
    print("\n[3] Verifying List via Service...")
    sessions = list_available_sessions()
    found = False
    for s in sessions:
        if s['id'] == pid:
            print(f"[OK] Found in Session List: {s['id']}")
            found = True
            break
    if not found:
        print("[FAIL] Not found in Session List!")
        
    # Cleanup (Manually delete from DB since we don't have delete_profile in session_manager exposed yet?)
    # Session manager doesn't have delete? Let's check. 
    # It seems session_manager doesn't have delete function in the file I read.
    # I'll delete via DB direct for cleanup.
    print("[CLEANUP] Removing test profile...")
    db = SessionLocal()
    db.query(Profile).filter(Profile.slug == pid).delete()
    db.commit()
    db.close()


if __name__ == "__main__":
    test_crud_scheduler()
    test_crud_profile()
