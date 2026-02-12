
import os
import sys
import asyncio
import json

# Setup paths
sys.path.append(os.path.join(os.getcwd(), "backend"))

from core.session_manager import list_available_sessions

async def debug_profiles():
    print("Testing list_available_sessions()...")
    try:
        sessions = list_available_sessions()
        print(f"Success! Found {len(sessions)} sessions.")
        print(json.dumps(sessions[0] if sessions else {}, indent=2, default=str))
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_profiles())
