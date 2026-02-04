import asyncio
import os
import sys
from playwright.async_api import async_playwright

# Adjust path to import core
sys.path.append(os.getcwd())

async def test_session():
    session_path = "d:\\APPS - ANTIGRAVITY\\Synapse\\backend\\data\\sessions\\tiktok_profile_1770135259969.json"
    
    if not os.path.exists(session_path):
        print(f"[X] Session file NOT found at: {session_path}")
        return

    print(f"[OK] Session file found. Size: {os.path.getsize(session_path)} bytes")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        try:
            # Try loading storage state
            context = await browser.new_context(storage_state=session_path)
            print("[OK] Context created with storage_state.")
            
            cookies = await context.cookies()
            print(f"[*] Cookie count in context: {len(cookies)}")
            
            # Check for sessionid
            session_id = next((c for c in cookies if c['name'] == 'sessionid'), None)
            if session_id:
                print(f"[OK] 'sessionid' cookie FOUND: {session_id['value'][:10]}...")
            else:
                print("[X] 'sessionid' cookie NOT FOUND in context!")

            page = await context.new_page()
            print("[*] Navigating to TikTok...")
            await page.goto("https://www.tiktok.com/upload", timeout=60000)
            await page.wait_for_timeout(5000)
            
            # Screenshot
            output_shot = "debug_session_test.png"
            await page.screenshot(path=output_shot)
            print(f"[*] Screenshot saved to {output_shot}")
            
            if "login" in page.url:
                 print("[!] Redirected to Login URL!")
            else:
                 print(f"[OK] Current URL: {page.url}")

        except Exception as e:
            print(f"💥 Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_session())
