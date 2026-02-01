import sys
import os
import json

# Force UTF-8 for console output
sys.stdout.reconfigure(encoding='utf-8')

# Add backend to path
sys.path.append(os.getcwd())

try:
    from core.session_manager import list_available_sessions
    print("Listing sessions...")
    sessions = list_available_sessions()
    print("Sessions found:")
    print(json.dumps(sessions, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
