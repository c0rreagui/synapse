"""
Force Fix Profile 01 - Convert and sanitize cookies for Playwright
"""
import asyncio
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.browser import launch_browser, close_browser

# Paths
SESSION_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "sessions", "tiktok_profile_01.json"
)
STATIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static"
)

def transform_raw_to_storage_state(raw_cookies: list) -> dict:
    """
    Transform raw cookie list to Playwright storage_state format.
    """
    cleaned_cookies = []
    
    for cookie in raw_cookies:
        clean = {}
        
        # Required fields
        clean["name"] = cookie.get("name", "")
        clean["value"] = cookie.get("value", "")
        clean["domain"] = cookie.get("domain", "")
        clean["path"] = cookie.get("path", "/")
        
        # Handle expires/expirationDate
        if "expirationDate" in cookie:
            clean["expires"] = cookie["expirationDate"]
        elif "expires" in cookie:
            clean["expires"] = cookie["expires"]
        else:
            clean["expires"] = -1  # Session cookie
        
        # Boolean fields
        clean["httpOnly"] = bool(cookie.get("httpOnly", False))
        clean["secure"] = bool(cookie.get("secure", False))
        
        # Fix sameSite - Playwright expects "Strict", "Lax", or "None"
        same_site = cookie.get("sameSite")
        if same_site == "no_restriction" or same_site is None:
            clean["sameSite"] = "None"
        elif same_site and same_site.lower() == "lax":
            clean["sameSite"] = "Lax"
        elif same_site and same_site.lower() == "strict":
            clean["sameSite"] = "Strict"
        else:
            clean["sameSite"] = "None"
        
        cleaned_cookies.append(clean)
    
    return {
        "cookies": cleaned_cookies,
        "origins": []
    }

def sanitize_existing_cookies(storage_state: dict) -> dict:
    """
    Re-sanitize cookies that are already in storage_state format.
    Fixes sameSite values and removes invalid keys.
    """
    invalid_keys = ["hostOnly", "session", "storeId", "id"]
    
    for cookie in storage_state.get("cookies", []):
        # Remove invalid keys
        for key in invalid_keys:
            cookie.pop(key, None)
        
        # Fix sameSite
        same_site = cookie.get("sameSite")
        if same_site == "no_restriction" or same_site is None or same_site == "unspecified":
            cookie["sameSite"] = "None"
        elif same_site and same_site.lower() == "lax":
            cookie["sameSite"] = "Lax"
        elif same_site and same_site.lower() == "strict":
            cookie["sameSite"] = "Strict"
    
    return storage_state

async def fix_and_verify():
    print("="*50)
    print("🔧 FORCE FIX PROFILE 01")
    print("="*50)
    
    # Step 1: Read the file
    print(f"📂 Reading: {SESSION_PATH}")
    
    if not os.path.exists(SESSION_PATH):
        print(f"❌ File not found: {SESSION_PATH}")
        return
    
    with open(SESSION_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Step 2: Check format and transform/sanitize
    if isinstance(data, list):
        print(f"⚠️  Detected RAW format (list of {len(data)} cookies)")
        print("🔄 Transforming to Playwright storage_state format...")
        storage_state = transform_raw_to_storage_state(data)
        print(f"✅ Transformed {len(storage_state['cookies'])} cookies")
        
    elif isinstance(data, dict) and "cookies" in data:
        print(f"ℹ️  File in storage_state format ({len(data['cookies'])} cookies)")
        print("🔄 Re-sanitizing cookies...")
        storage_state = sanitize_existing_cookies(data)
        print("✅ Cookies sanitized")
    else:
        print("❌ Unknown format")
        return
    
    # Save the corrected file
    with open(SESSION_PATH, 'w', encoding='utf-8') as f:
        json.dump(storage_state, f, indent=2)
    print(f"💾 Saved corrected file: {SESSION_PATH}")
    
    # Step 3: Verify by loading in browser
    print("\n🌐 Launching browser to verify...")
    
    p = None
    browser = None
    
    try:
        p, browser, context, page = await launch_browser(
            headless=False,
            storage_state=SESSION_PATH
        )
        
        print("📍 Navigating to TikTok upload...")
        await page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=120000, wait_until="load")
        
        print("⏳ Waiting 15s for page to fully load...")
        await page.wait_for_timeout(15000)
        
        # Check URL
        current_url = page.url
        print(f"📌 Current URL: {current_url}")
        
        if "login" in current_url.lower():
            print("❌ FAILED: Still on login page")
            print("💡 TIP: Run 'python tools/login_session.py tiktok_profile_01' to re-login")
        else:
            print("✅ SUCCESS: Logged in!")
        
        # Screenshot
        screenshot_path = os.path.join(STATIC_DIR, "p1_reborn.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"📸 Screenshot saved: {screenshot_path}")
        
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("🚪 Closing browser...")
        if p and browser:
            await close_browser(p, browser)
    
    print("\n✅ Done!")

if __name__ == "__main__":
    asyncio.run(fix_and_verify())
