import asyncio
from core.browser import launch_browser, close_browser

async def main():
    print("Testing browser.py module...")
    try:
        p, browser, context, page = await launch_browser(headless=False)
        print("Browser launched with Stealth Args!")
        await page.goto("https://whoer.net")
        print("Navigated to Whoer")
        await page.screenshot(path="debug_module_test.png")
        print("Screenshot taken")
        await close_browser(p, browser)
        print("Browser closed")
    except Exception as e:
        print(f"Error in module test: {e}")

if __name__ == "__main__":
    asyncio.run(main())
