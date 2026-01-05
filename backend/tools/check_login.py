import asyncio
import sys
import os

# Add backend to path to allow imports if running from root or backend dir
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.browser import launch_browser, close_browser
from core.session_manager import get_session_path

async def check_login(session_name: str, url: str):
    print(f"--- CHECK LOGIN TOOL ---")
    print(f"Target: {url}")
    print(f"Session Name: {session_name}")
    
    session_path = get_session_path(session_name)
    if not os.path.exists(session_path):
        print(f"ERROR: Session file not found at {session_path}")
        return

    print(f"Loading session from {session_path}")
    print("Launching browser... (Headless: False for verification)")
    
    p = None
    browser = None
    
    try:
        # Launch with storage_state
        p, browser, context, page = await launch_browser(
            headless=False, 
            storage_state=session_path
        )
        
        print(f"Navigating to {url}...")
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        
        # Wait for potential redirects or loading
        print("Waiting 5s for page load...")
        await page.wait_for_timeout(5000)
        
        # Take screenshot
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
        filename = "login_proof.png"
        filepath = os.path.join(static_dir, filename)
        
        await page.screenshot(path=filepath, full_page=True)
        print(f"Screenshot saved to {filepath}")
        
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
    TARGET_URL = "https://www.tiktok.com/upload"
    
    # Allow args override if needed
    if len(sys.argv) > 1:
        SESSION_NAME = sys.argv[1]
    
    asyncio.run(check_login(SESSION_NAME, TARGET_URL))
