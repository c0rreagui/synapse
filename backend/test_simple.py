import asyncio
from playwright.async_api import async_playwright

async def main():
    print("Testing RAW Playwright...")
    async with async_playwright() as p:
        # Minimal args usually work
        browser = await p.chromium.launch(headless=False) 
        print("Browser launched (RAW)")
        page = await browser.new_page()
        try:
            await page.goto("https://www.google.com", timeout=30000)
            print("Navigated to Google")
            await page.screenshot(path="debug_simple.png")
            print("Screenshot saved")
        except Exception as e:
            print(f"Navigation failed: {e}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
