
import asyncio
import sys
import os

# Setup Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core import session_manager
from core.oracle.seo_engine import seo_engine
from core.oracle import oracle

async def run_debug():
    print("Starting Audit Debug...")
    
    # List sessions to get a valid ID
    sessions = session_manager.list_available_sessions()
    if not sessions:
        print("❌ No profiles found.")
        return

    profile_id = sessions[0]["id"]
    print(f"Testing with Profile ID: {profile_id} ({sessions[0].get('label')})")
    
    try:
        metadata = session_manager.get_profile_metadata(profile_id)
        if not metadata:
            print("Metadata not found")
            return
            
        print("Metadata loaded. Testing Visual Cortex (Screenshot)...")
        # Test 1: Screenshot (Mocking valid username if needed)
        username = metadata.get("username")
        if not username:
             print("No username in metadata, skipping screenshot test.")
        else:
             try:
                # We might need to ensure browser is headless/stealth
                print(f"   Navigating to @{username}...")
                path = await oracle.sense.capture_profile_screenshot(username)
                print(f"   Screenshot success: {path}")
             except Exception as e:
                print(f"   Screenshot FAILED: {e}")
                import traceback
                traceback.print_exc()

        print("Testing SEO Engine Audit...")
        # Test 2: SEO Engine
        result = seo_engine.audit_profile(metadata)
        print("SEO Audit Success!")
        # print(result.keys())
        
    except Exception as e:
        print(f"GLOBAL FAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(run_debug())
