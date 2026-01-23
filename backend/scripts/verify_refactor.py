import sys
import os

# Adds backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

def test_imports():
    print("Testing imports...")
    try:
        from core.session_manager import list_available_sessions
        from core.scheduler import scheduler_service
        print("✅ Imports successful.")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return

    print("Testing Session Manager (DB)...")
    try:
        sessions = list_available_sessions()
        print(f"✅ Found {len(sessions)} profiles from DB.")
        for s in sessions:
            print(f"   - {s['label']} ({s['id']})")
    except Exception as e:
        print(f"❌ Session Manager failed: {e}")

    print("Testing Scheduler (DB)...")
    try:
        schedule = scheduler_service.load_schedule()
        print(f"✅ Found {len(schedule)} schedule items.")
    except Exception as e:
        print(f"❌ Scheduler failed: {e}")

if __name__ == "__main__":
    test_imports()
