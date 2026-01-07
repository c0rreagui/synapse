import asyncio
from core.browser import launch_browser, close_browser

async def main():
    print("Testing browser.py module on Google...")
    try:
        p, browser, context, page = await launch_browser(headless=False)
        print("Browser launched with Stealth Args!")
        await page.goto("https://www.google.com")
        print("Navigated to Google")
        await page.screenshot(path="debug_module_google.png")
        print("Screenshot taken")
        await close_browser(p, browser)
        print("Browser closed")
    except Exception as e:
        print(f"Error in module google test: {e}")

if __name__ == "__main__":
    asyncio.run(main())
