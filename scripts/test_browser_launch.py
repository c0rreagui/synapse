
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.browser import launch_browser, close_browser

async def test_launch():
    print(f"Platform: {sys.platform}")
    from core.browser import IN_DOCKER
    print(f"IN_DOCKER: {IN_DOCKER}")
    
    try:
        p, browser, context, page = await launch_browser(headless=True)
        print("Successfully launched browser with default args")
        await page.goto("https://www.google.com")
        print(f"Page title: {await page.title()}")
        await close_browser(p, browser)
    except Exception as e:
        print(f"Default launch failed: {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(test_launch())
