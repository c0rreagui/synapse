import asyncio
from playwright.async_api import async_playwright
import os
from datetime import datetime

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", TIMESTAMP)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

BASE_URL = "http://127.0.0.1:3000"

async def run():
    async with async_playwright() as p:
        print("Launching Browser...")
        # Launch headless=False so user can see it briefly if they look, but we'll be fast.
        # Check if we can run headless=True to avoid popup. Let's try headless=True for stability on agent run.
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()

        print(f"Saving screenshots to: {SCREENSHOT_DIR}")

        # 1. Home Page
        print(f"Navigating to {BASE_URL}...")
        try:
            await page.goto(BASE_URL, timeout=10000)
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "1_home.png"))
            print("Home loaded")
        except Exception as e:
            print(f"Failed to load Home: {e}")
            await browser.close()
            return

        # 2. Oracle Page (Base)
        print(f"Navigating to {BASE_URL}/oracle...")
        try:
            await page.goto(f"{BASE_URL}/oracle", timeout=10000)
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "2_oracle_base.png"))
            print("Oracle loaded")
        except Exception as e:
            print(f"Failed to load Oracle: {e}")
        
        # 3. Check Tabs (Clicking)
        tabs = [
            {"name": "Deep Analytics", "selector": "text=Deep Analytics", "file": "3_analytics_tab.png"},
            {"name": "Auditoria SEO", "selector": "text=Auditoria SEO", "file": "4_audit_tab.png"},
            {"name": "Competitor Spy", "selector": "text=Competitor Spy", "file": "5_spy_tab.png"}
        ]

        for tab in tabs:
            print(f"Switching to {tab['name']}...")
            try:
                if await page.is_visible(tab['selector']):
                    await page.click(tab['selector'])
                    await page.wait_for_timeout(1000) # Wait for animation
                    await page.screenshot(path=os.path.join(SCREENSHOT_DIR, tab['file']))
                    print(f"{tab['name']} verified")
                else:
                    print(f"Tab {tab['name']} not found")
            except Exception as e:
                print(f"Error clicking {tab['name']}: {e}")

        await browser.close()
        print("Test Finished.")
        print(f"Screenshots saved in {SCREENSHOT_DIR}")

if __name__ == "__main__":
    asyncio.run(run())
