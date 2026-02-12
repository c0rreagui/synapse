#!/usr/bin/env python3
"""
repair_session_cli.py - CLI for interactive session repair

Opens a headful browser with the profile's cookies so the user can manually
log in and fix authentication issues (CAPTCHA, expired session, etc).
"""

import sys
import asyncio
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.browser import launch_browser, close_browser
from core.session_manager import get_session_path, save_session, update_profile_status, update_profile_metadata
from core.network_utils import get_upload_url

async def repair_session(profile_id: str):
    """Opens interactive browser for session repair."""
    print(f"[REPAIR] Starting repair session for: {profile_id}")
    
    session_path = get_session_path(profile_id)
    if not os.path.exists(session_path):
        print(f"[REPAIR] ERROR: Session file not found: {session_path}")
        return {"status": "error", "message": "Session file not found"}
    
    p = None
    browser = None
    
    try:
        # Launch headful (visible) browser
        p, browser, context, page = await launch_browser(
            headless=False,  # Visible for user interaction
            storage_state=session_path
        )
        
        # Navigate to TikTok Studio
        print(f"[REPAIR] Navigating to TikTok Studio...")
        try:
            await page.goto(get_upload_url(), timeout=60000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"[REPAIR] Navigation warning (continuing): {e}")
        
        print("[REPAIR] Browser opened. Please log in manually.")
        print("[REPAIR] Close the browser window when done to save the session.")
        
        # Wait for user to close the browser
        # The browser context will capture the login automatically
        try:
            await page.wait_for_timeout(600000)  # 10 minutes max
        except Exception:
            pass  # Browser closed by user
        
        # Save the updated session
        print("[REPAIR] Saving updated session...")
        await save_session(context, profile_id)
        
        # Clear error screenshot and reactivate profile
        update_profile_metadata(profile_id, {"last_error_screenshot": None})
        update_profile_status(profile_id, True)
        
        print("[REPAIR] Session saved successfully!")
        return {"status": "success", "message": "Session repaired"}
        
    except Exception as e:
        print(f"[REPAIR] ERROR: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if p:
            await close_browser(p, browser)

def main():
    if len(sys.argv) < 2:
        print("Usage: python repair_session_cli.py <profile_id>")
        sys.exit(1)
    
    profile_id = sys.argv[1]
    result = asyncio.run(repair_session(profile_id))
    print(f"[REPAIR] Result: {result}")

if __name__ == "__main__":
    main()
