"""
Test TikTok Studio upload page specifically
"""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright
import json

async def test_studio_upload(profile_id):
    session_file = f"c:\\APPS - ANTIGRAVITY\\Synapse\\backend\\data\\sessions\\{profile_id}.json"
    
    print(f"\n🎬 Testing TikTok Studio Upload Page")
    print(f"📂 Session: {profile_id}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=session_file)
        page = await context.new_page()
        
        # Navigate DIRECTLY to upload page (like the bot does)
        print(f"\n🌍 Navigating to TikTok Studio Upload...")
        await page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=60000)
        await page.wait_for_timeout(5000)
        
        # Check URL
        current_url = page.url
        print(f"📍 Final URL: {current_url}")
        
        if "login" in current_url or "redirect" in current_url:
            print("❌ REDIRECTED! Not logged in for Studio.")
        else:
            print("✅ Stayed on upload page - working!")
        
        # Check for upload input
        try:
            upload_input = await page.locator('input[type="file"]').count()
            print(f"📤 Upload inputs found: {upload_input}")
            if upload_input > 0:
                print("✅ Upload page loaded correctly!")
        except:
            pass
        
        # Screenshot
        screenshot_path = f"c:\\APPS - ANTIGRAVITY\\Synapse\\studio_test_{profile_id}.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"📸 Screenshot: {screenshot_path}")
        
        print("\n⏳ Waiting 15 seconds for inspection...")
        await page.wait_for_timeout(15000)
        
        await browser.close()

if __name__ == "__main__":
    profile = sys.argv[1] if len(sys.argv) > 1 else "tiktok_profile_02"
    asyncio.run(test_studio_upload(profile))
