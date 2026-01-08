"""
Test if Playwright is actually loading cookies from storage_state
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def test_storage_state_loading():
    session_file = "c:\\APPS - ANTIGRAVITY\\Synapse\\backend\\data\\sessions\\tiktok_profile_02.json"
    
    # Load session file
    with open(session_file, 'r') as f:
        session_data = json.load(f)
    
    print(f"📂 Session file: {session_file}")
    print(f"🍪 Cookies in file: {len(session_data.get('cookies', []))}")
    
    # Find critical cookies
    critical_cookies = ['sessionid', 'sid_tt', 'sid_guard', 'uid_tt']
    for name in critical_cookies:
        exists = any(c['name'] == name for c in session_data.get('cookies', []))
        print(f"   - {name}: {'✅' if exists else '❌'}")
    
    print(f"\n🔧 Launching Playwright with storage_state...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Load with storage_state
        context = await browser.new_context(storage_state=session_file)
        page = await context.new_page()
        
        # Get all cookies from context
        cookies_in_browser = await context.cookies()
        
        print(f"\n🌐 Cookies loaded in browser: {len(cookies_in_browser)}")
        
        # Check critical cookies
        for name in critical_cookies:
            exists = any(c['name'] == name for c in cookies_in_browser)
            print(f"   - {name}: {'✅ LOADED' if exists else '❌ MISSING'}")
        
        # Navigate to TikTok
        print(f"\n🌍 Navigating to TikTok...")
        await page.goto("https://www.tiktok.com/", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # Get cookies AFTER navigation
        cookies_after_nav = await context.cookies()
        print(f"\n📊 Cookies after navigation: {len(cookies_after_nav)}")
        
        for name in critical_cookies:
            exists = any(c['name'] == name for c in cookies_after_nav)
            print(f"   - {name}: {'✅' if exists else '❌ LOST!'}")
        
        # Check current URL
        url = page.url
        print(f"\n📍 Current URL: {url}")
        
        if "login" in url:
            print("❌ REDIRECTED TO LOGIN - Cookies not working!")
        else:
            print("✅ Stayed on TikTok - Cookies working!")
        
        await page.wait_for_timeout(10000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_storage_state_loading())
