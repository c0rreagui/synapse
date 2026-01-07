import asyncio
from playwright.async_api import async_playwright

async def main():
    print("Starting Playwright Test...")
    try:
        async with async_playwright() as p:
            print("Launching Chromium...")
            browser = await p.chromium.launch(headless=False)
            print("Chromium Launched.")
            page = await browser.new_page()
            await page.goto("http://example.com")
            print("Navigation Success: ", await page.title())
            await browser.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
