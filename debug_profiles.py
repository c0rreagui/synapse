import sys
import os

# Add root to path
sys.path.append(os.getcwd())

try:
    from backend.core.session_manager import list_available_sessions, SESSIONS_DIR, BASE_DIR
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"SESSIONS_DIR: {SESSIONS_DIR}")
    print(f"Exists? {os.path.exists(SESSIONS_DIR)}")
    if os.path.exists(SESSIONS_DIR):
        print(f"Contents: {os.listdir(SESSIONS_DIR)}")
    
    profiles = list_available_sessions()
    print(f"Profiles Found: {len(profiles)}")
    for p in profiles:
        print(p)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
