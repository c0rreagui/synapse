import asyncio
import sys
import os
import json

# Add backend to path to allow imports if running from root or backend dir
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.browser import launch_browser, close_browser
from core.session_manager import get_session_path, save_session

async def convert_and_verify(session_name: str, target_url: str):
    print(f"--- COOKIE CONVERTER TOOL ---")
    print(f"Session: {session_name}")
    
    session_path = get_session_path(session_name)
    if not os.path.exists(session_path):
        print(f"ERROR: Session file not found at {session_path}")
        return

    print(f"Reading raw cookies from {session_path}")
    try:
        with open(session_path, 'r', encoding='utf-8') as f:
            raw_cookies = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return

    # Basic check if it's a list (Raw) or dict (Storage State)
    if isinstance(raw_cookies, dict) and "cookies" in raw_cookies:
        print("File already seems to be in Storage State format.")
        # We can still proceed to verify it works, but sanitization might differ.
        sanitized_cookies = raw_cookies["cookies"]
    elif isinstance(raw_cookies, list):
        print("Detected Raw Cookie List. Sanitizing...")
        sanitized_cookies = []
        for c in raw_cookies:
            new_cookie = {}
            # Copy valid fields
            valid_fields = ['name', 'value', 'domain', 'path', 'expires', 'httpOnly', 'secure', 'sameSite']
            
            # Map expirationDate to expires
            if 'expirationDate' in c:
                new_cookie['expires'] = c['expirationDate']
            elif 'expires' in c:
                new_cookie['expires'] = c['expires']
                
            for k in valid_fields:
                if k in c and k != 'expires': # Already handled expires
                     new_cookie[k] = c[k]
            
            # Fix SameSite
            if 'sameSite' in new_cookie:
                ss = new_cookie['sameSite']
                if ss == "no_restriction" or ss is None:
                    new_cookie['sameSite'] = "None"
                # Playwright expects PascalCase for SameSite usually: "Strict", "Lax", "None"
                elif ss.lower() == "lax":
                    new_cookie['sameSite'] = "Lax"
                elif ss.lower() == "strict":
                    new_cookie['sameSite'] = "Strict"
            
            # Fix Secure
            if 'secure' in new_cookie:
                new_cookie['secure'] = bool(new_cookie['secure'])
                
            # Remove url if present (add_cookies uses domain)
            
            sanitized_cookies.append(new_cookie)
    else:
        print("Unknown JSON format.")
        return

    print(f"Prepared {len(sanitized_cookies)} cookies.")

    print("Launching browser (Headless: False)...")
    p = None
    browser = None
    
    try:
        # Launch WITHOUT storage_state to inject manually
        p, browser, context, page = await launch_browser(headless=False)
        
        print("Injecting cookies...")
        try:
            await context.add_cookies(sanitized_cookies)
        except Exception as e:
            print(f"Error adding cookies: {e}")
            # Try to continue or specific handling
        
        print(f"Navigating to {target_url}...")
        await page.goto(target_url, timeout=120000, wait_until="load")
        
        print("Waiting 15s for full page render...")
        await page.wait_for_timeout(15000)
        
        # Check current URL
        current_url = page.url
        print(f"Current URL: {current_url}")
        
        # Take screenshot
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
        filename = "login_proof.png" # Overwrite previous one
        filepath = os.path.join(static_dir, filename)
        
        await page.screenshot(path=filepath, full_page=True)
        print(f"Screenshot saved to {filepath}")
        
        # If successfully on upload page (or logged in context), save the correct state
        if "login" not in current_url: # Heuristic: if we are not redirected to login
            print("Navigation looks successful (not on login page).")
            print("Overwriting session file with valid Storage State...")
            await save_session(context, session_name)
            print("Session file updated successfully.")
        else:
            print("WARNING: It seems we are still on a login page/redirect.")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("Closing browser...")
        if p and browser:
            await close_browser(p, browser)
        print("Done.")

if __name__ == "__main__":
    SESSION_NAME = "tiktok_profile_01"
    TARGET_URL = "https://www.tiktok.com/upload"
    
    asyncio.run(convert_and_verify(SESSION_NAME, TARGET_URL))
