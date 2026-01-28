import sys
import os

print(f"CWD: {os.getcwd()}")
print(f"Path: {sys.path}")

try:
    print("Attempting: from backend.core.session_manager import list_available_sessions")
    from backend.core.session_manager import list_available_sessions
    print("SUCCESS: session_manager imported")
except Exception as e:
    print(f"FAIL: session_manager: {e}")
    import traceback
    traceback.print_exc()

try:
    print("Attempting: from backend.core.status_manager import status_manager")
    from backend.core.status_manager import status_manager
    print("SUCCESS: status_manager imported")
except Exception as e:
    print(f"FAIL: status_manager: {e}")
    traceback.print_exc()

try:
    print("Attempting: from backend.core.ingestion import ingestion_service")
    from backend.core.ingestion import ingestion_service
    print("SUCCESS: ingestion_service imported")
except Exception as e:
    print(f"FAIL: ingestion_service: {e}")
    traceback.print_exc()

