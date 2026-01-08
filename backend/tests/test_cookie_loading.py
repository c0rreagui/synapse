"""
Test script to verify Playwright cookie loading
"""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright
import json

async def test_cookie_loading(profile_id):
    session_file = f"c:\\APPS - ANTIGRAVITY\\Synapse\\backend\\data\\sessions\\{profile_id}.json"
    
    print(f"📂 Testing session: {session_file}")
    print(f"📄 File exists: {os.path.exists(session_file)}")
    
    if not os.path.exists(session_file):
        print("❌ Session file not found!")
        return
    
    # Check file content
    with open(session_file, 'r') as f:
        data = json.load(f)
        print(f"🍪 Cookies in file: {len(data.get('cookies', []))}")
        print(f"🌐 Origins in file: {len(data.get('origins', []))}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Load with storage_state
        print(f"\n🔄 Loading context with storage_state...")
        context = await browser.new_context(storage_state=session_file)
        page = await context.new_page()
        
        # Navigate to TikTok
        print(f"🌍 Navigating to TikTok...")
        await page.goto("https://www.tiktok.com/", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # Check URL
        current_url = page.url
        print(f"📍 Current URL: {current_url}")
        
        if "login" in current_url:
            print("❌ REDIRECTED TO LOGIN! Cookies not working.")
        else:
            print("✅ No login redirect - cookies working!")
        
        # Check if logged in
        try:
            # Try to find profile icon or username
            profile_icon = await page.locator('[data-e2e="profile-icon"], [data-e2e="nav-profile"]').count()
            if profile_icon > 0:
                print("✅ Profile icon found - USER IS LOGGED IN!")
            else:
                print("⚠️ No profile icon - may not be logged in")
        except Exception as e:
            print(f"⚠️ Could not check login status: {e}")
        
        # Take screenshot
        screenshot_path = f"c:\\APPS - ANTIGRAVITY\\Synapse\\cookie_test_{profile_id}.png"
        await page.screenshot(path=screenshot_path)
        print(f"📸 Screenshot saved: {screenshot_path}")
        
        # Wait for user to see
        print("\n⏳ Waiting 10 seconds for visual inspection...")
        await page.wait_for_timeout(10000)
        
        await browser.close()
        print("\n✅ Test complete!")

if __name__ == "__main__":
    profile = sys.argv[1] if len(sys.argv) > 1 else "tiktok_profile_02"
    asyncio.run(test_cookie_loading(profile))
