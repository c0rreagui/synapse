import asyncio
import sys
import os
import logging
from backend.core.browser import launch_browser, close_browser

# Add root to path
sys.path.append(os.getcwd())

async def diagnose():
    print("--- DIAGNOSING COOKIES VISUALLY ---")
    profile_id = "tiktok_profile_01"
    session_path = os.path.abspath(f"backend/data/sessions/{profile_id}.json")
    
    print(f"Loading session: {session_path}")
    
    p = None
    browser = None
    try:
        p, browser, context, page = await launch_browser(
            headless=True, # Headless but we will screenshot
            storage_state=session_path
        )
        
        print("Navigating to TikTok Upload (Auth Check)...")
        # Try upload page as it redirects to login if auth is bad
        await page.goto("https://www.tiktok.com/upload?lang=en", timeout=60000)
        await page.wait_for_timeout(5000)
        
        title = await page.title()
        url = page.url
        print(f"Page Title: {title}")
        print(f"Current URL: {url}")
        
        # Take screenshot
        output_path = os.path.abspath("C:/Users/guico/.gemini/antigravity/brain/adef9bb8-9af7-4d7e-a470-5320a1ffcfbf/tiktok_debug_evidence.png")
        await page.screenshot(path=output_path)
        print(f"Screenshot saved to: {output_path}")
        
        # Checking for specific elements
        avatar = await page.query_selector("header img")
        if avatar:
            print("Avatar element FOUND in header.")
            src = await avatar.get_attribute("src")
            print(f"Avatar SRC: {src}")
        else:
            print("Avatar element NOT FOUND in header.")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_browser(p, browser)

if __name__ == "__main__":
    asyncio.run(diagnose())
