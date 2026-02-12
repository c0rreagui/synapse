
import asyncio
import os
import sys
import json
from playwright.async_api import async_playwright

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.session_manager import get_session_path
from core.network_utils import DEFAULT_UA, get_upload_url

async def debug_session(profile_id):
    session_path = get_session_path(profile_id)
    print(f"[DEBUG] Loading session from: {session_path}")
    
    async with async_playwright() as p:
        # Using a very standard UA
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            storage_state=session_path,
            user_agent=ua,
            viewport={"width": 1280, "height": 720}
        )
        
        page = await context.new_page()
        
        # Monitor redirects
        page.on("framenavigated", lambda frame: print(f"[NAV] {frame.url}"))
        
        print(f"[ACTION] Navigating to {get_upload_url()}...")
        try:
            await page.goto(get_upload_url(), timeout=60000)
            await page.wait_for_timeout(5000) # Wait for stability
            
            final_url = page.url
            print(f"[RESULT] Final URL: {final_url}")
            
            # Check for login indicators
            if "login" in final_url.lower():
                print("[!] REDIRECTED TO LOGIN")
            else:
                print("[+] SESSION SEEMS TO WORK?")
                
            # Take a proper screenshot with some delay
            screenshot_path = f"debug_{profile_id}_final.png"
            await page.screenshot(path=screenshot_path)
            print(f"[SCREENSHOT] Saved to {screenshot_path}")
            
            # Check cookies after navigation
            cookies = await context.cookies()
            print(f"[COOKIES] Found {len(cookies)} cookies after navigation")
            
        except Exception as e:
            print(f"[ERROR] {e}")
            
        await browser.close()

if __name__ == "__main__":
    profile_id = "tiktok_profile_1770135259969"
    asyncio.run(debug_session(profile_id))
