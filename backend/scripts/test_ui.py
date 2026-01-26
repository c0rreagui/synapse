
import asyncio
from playwright.async_api import async_playwright
import sys
import os
import io

# Force UTF-8 for Windows Console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def run():
    print("🚀 Starting UI Test Bot...")
    async with async_playwright() as p:
        # Launch browser (headless=True for speed, but screenshots likely need virtual display on some envs. 
        # On Windows local it's fine)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        # Capture Console Logs
        page.on("console", lambda msg: print(f"CONSOLE [{msg.type}]: {msg.text}"))
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        
        url = "http://127.0.0.1:3000/oracle"
        print(f"🌐 Navigating to {url}...")
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            print("✅ Page Loaded")
            
            # Pre-check screenshot
            await page.screenshot(path=os.path.join("data", "debug_initial_load.png"))
            
            # Check Title
            title = await page.title()
            print(f"📄 Title: {title}")
            
            # dump html content for debugging
            # content = await page.content()
            # print(f"📄 Content Length: {len(content)}")
            
            # 1. Click 'Deep Analytics' Tab
            # Try specific button role
            deep_tab = page.get_by_role("button", name="Deep Analytics")
            
            if await deep_tab.count() > 0:
                print("✅ Found 'Deep Analytics' Tab Button")
                await deep_tab.click()
                print("🖱️ Clicked 'Deep Analytics'")
                await page.wait_for_timeout(2000) # Explicit wait for animation/render
            else:
                print("❌ 'Deep Analytics' Tab Button NOT FOUND")
                print("--- PAGE TEXT DUMP ---")
                text = await page.inner_text("body")
                print(text[:1000]) # First 1000 chars
                print("--- END DUMP ---")
                
                print("Dump of visible buttons:")
                # Correct way to get all button texts
                locator = page.get_by_role("button")
                button_count = await locator.count()
                for i in range(button_count):
                    print(f"- {await locator.nth(i).inner_text()}")
                    
                await browser.close()
                return

            # 2. Verify Charts
            # Look for specific chart container or text
            # Retention Chart
            retention_text = "Curva de Retenção"
            if await page.get_by_text(retention_text).count() > 0:
                 print("✅ Retention Chart Title found")
            else:
                 print(f"❌ '{retention_text}' Not Found")

            # Heatmap
            heatmap_text = "Mapa de Calor"
            if await page.get_by_text(heatmap_text).count() > 0:
                print("✅ Heatmap Title found")
            else:
                print(f"❌ '{heatmap_text}' Not Found")
                
            # 3. Verify Patterns
            patterns_text = "Padrões Detectados"
            if await page.get_by_text(patterns_text).count() > 0:
                print("✅ Pattern Section found")
            else:
                print(f"❌ '{patterns_text}' Not Found")
            
            # 4. Final Screenshot
            screenshot_path = os.path.join("data", "ui_test_result.png")
            await page.screenshot(path=screenshot_path)
            print(f"📸 Screenshot saved to {screenshot_path}")
            
        except Exception as e:
            print(f"❌ Error during test: {e}")
            await page.screenshot(path=os.path.join("data", "debug_error.png"))
            
        finally:
            await browser.close()
            print("🏁 Test Finished")

if __name__ == "__main__":
    asyncio.run(run())
