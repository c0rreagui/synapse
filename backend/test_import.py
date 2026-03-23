
import sys
import os
import traceback

# Ensure the backend directory is in the path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

print(f"DEBUG: sys.path includes {backend_dir}")

try:
    print("DEBUG: Attempting to import upload_video_monitored from core.uploader_monitored")
    from core.uploader_monitored import upload_video_monitored
    print("SUCCESS: Import successful!")
except Exception as e:
    print(f"FAILURE: Import failed: {str(e)}")
    traceback.print_exc()
