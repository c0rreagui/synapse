import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from core.session_manager import list_available_sessions

def run_debug():
    try:
        print("Calling list_available_sessions()...")
        sessions = list_available_sessions()
        print(f"Success! Found {len(sessions)} sessions.")
        for s in sessions:
            print(f"- {s.get('id')}: last_error={s.get('last_error_screenshot')}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"CRASH: {e}")

if __name__ == "__main__":
    run_debug()
