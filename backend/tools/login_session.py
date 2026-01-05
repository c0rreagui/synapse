import asyncio
import sys
import os

# Add backend to path to allow imports if running from root or backend dir
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.browser import launch_browser, close_browser
from core.session_manager import save_session

async def login_and_capture(session_name: str, url: str):
    print(f"--- LOGIN SESSION TOOL ---")
    print(f"Target: {url}")
    print(f"Session Name: {session_name}")
    print("Launching browser... (Headless: False)")
    
    p = None
    browser = None
    
    try:
        p, browser, context, page = await launch_browser(headless=False)
        
        print(f"Navigating to {url}...")
        await page.goto(url, timeout=60000)
        
        print("\n" + "="*50)
        print("ACTION REQUIRED:")
        print("1. The browser window is open.")
        print("2. Please log in manually to your account.")
        print("3. Resolve any CAPTCHAs or 2FA.")
        print("4. When you reach the dashboard/home page, come back here.")
        print("="*50 + "\n")
        
        # Use run_in_executor to avoid blocking the event loop while waiting for input
        await asyncio.get_event_loop().run_in_executor(None, input, "Press ENTER here when login is complete and you want to save the session...")
        
        print("\nSaving session state...")
        success = await save_session(context, session_name)
        
        if success:
            print(f"SUCCESS: Session saved to backend/data/sessions/{session_name}.json")
        else:
            print("ERROR: Failed to save session.")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        
    finally:
        print("Closing browser...")
        if p and browser:
            await close_browser(p, browser)
        print("Done.")

if __name__ == "__main__":
    # Default config
    SESSION_NAME = "tiktok_profile_01"
    TARGET_URL = "https://www.tiktok.com/login"
    
    # Allow args override if needed
    if len(sys.argv) > 1:
        SESSION_NAME = sys.argv[1]
    
    asyncio.run(login_and_capture(SESSION_NAME, TARGET_URL))
