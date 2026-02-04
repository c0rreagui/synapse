import sys
import os
import asyncio
import json

# Setup path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.session_manager import import_session, get_profile_metadata
from core.profile_validator import validate_profile

async def test_import():
    print("--- Testing Import Session ---")
    try:
        # Mock cookies
        cookies = '[{"name": "test", "value": "test", "domain": ".tiktok.com"}]'
        
        # Test 1: Import with just Label (Old way compatible?)
        print("1. Importing with Label + Cookies...")
        pid1 = import_session("Debug Profile 1", cookies)
        print(f"   Success: {pid1}")
        
        # Test 2: Import with Username/Avatar (New way)
        print("2. Importing with Full Metadata...")
        pid2 = import_session("Debug Profile 2", cookies, username="debug_user", avatar_url="http://fake.url/img.png")
        print(f"   Success: {pid2}")
        
        return pid1
    except Exception as e:
        print(f"!!! IMPORT ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_validation(profile_id):
    if not profile_id: return
    print(f"\n--- Testing Validation (Refresh) for {profile_id} ---")
    try:
        # This calls the direct function, simulating what validator_cli doing
        result = await validate_profile(profile_id)
        print(f"   Result: {result}")
    except Exception as e:
        print(f"!!! VALIDATION ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    pid = asyncio.run(test_import())
    if pid:
        asyncio.run(test_validation(pid))
