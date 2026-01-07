import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    print("🚀 Starting E2E Upload Test...")
    
    # Path to dummy video (relative to this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(script_dir, "dummy_video.mp4")
    if not os.path.exists(video_path):
        print(f"❌ Error: Dummy video not found at {video_path}")
        return

    async with async_playwright() as p:
        # Launch browser in VISIBLE mode (headless=False)
        # slow_mo=1000 slows down operations by 1 second so you can see what's happening
        browser = await p.chromium.launch(headless=False, slow_mo=1000) 
        page = await browser.new_page()
        
        try:
            # Go to Home Page
            print("🌐 Navigating to http://localhost:3000...")
            await page.goto("http://localhost:3000")
            
            # Check Title
            try:
                # Find H1 with specific text
                title_locator = page.locator("h1", has_text="Fábrica de Conteúdo")
                await title_locator.wait_for(timeout=5000)
                print(f"✅ Page Title Found: 'Fábrica de Conteúdo'")
                
                # Check for other h1 just in case
                all_h1s = await page.locator("h1").all_inner_texts()
                print(f"ℹ️ All H1s found: {all_h1s}")
                
            except Exception as e:
                print(f"❌ Could not find H1 with 'Fábrica de Conteúdo': {e}")
                all_h1s = await page.locator("h1").all_inner_texts()
                print(f"ℹ️ All H1s found: {all_h1s}")
                raise AssertionError(f"Title 'Fábrica de Conteúdo' not found. Available H1s: {all_h1s}")

            # Prepare for upload
            print("📤 Uploading file...")
            
            # Using set_input_files on the hidden input
            # The input is hidden inside the upload div, we can select it by type="file"
            await page.set_input_files('input[type="file"]', video_path)
            
            # Wait for success toast or queue item
            # Toast appears with text: `✅ "dummy_video.mp4" enviado com sucesso!`
            # Or item in queue with status "enviando" -> "processando" -> "concluido"
            
            print("⏳ Waiting for upload success...")
            
            # Wait for toast
            toast_locator = page.locator("text=enviado com sucesso")
            await toast_locator.wait_for(state="visible", timeout=10000)
            
            print("✅ Success Toast appeared!")
            
            # Verify Queue Item
            queue_item = page.locator("text=dummy_video.mp4")
            await queue_item.first.wait_for(state="visible")
            print("✅ File appears in the queue!")
            
            print("🎉 ALL TESTS PASSED!")

        except Exception as e:
            error_msg = f"❌ Test Failed: {type(e).__name__}: {e}"
            print(error_msg)
            with open("error_log.txt", "w", encoding="utf-8") as f:
                f.write(error_msg)
            # Take screenshot on failure
            await page.screenshot(path="test_failure.png")
            print("📸 Screenshot saved to test_failure.png")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
