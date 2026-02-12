import asyncio
from playwright.async_api import async_playwright
import os

SESSION_PATH = r"d:\APPS - ANTIGRAVITY\Synapse\backend\data\sessions\tiktok_profile_1770307556827.json"

async def test_load():
    print(f"Testing session load from: {SESSION_PATH}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(storage_state=SESSION_PATH)
            print("Session loaded successfully!")
            await context.close()
        except Exception as e:
            print(f"FAILED to load session: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_load())
