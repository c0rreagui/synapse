"""
Debug script to find the correct file upload selector
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_upload_selectors():
    session_file = "c:\\APPS - ANTIGRAVITY\\Synapse\\backend\\data\\sessions\\tiktok_profile_02.json"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=session_file)
        page = await context.new_page()
        
        print("\n🌍 Navigating to TikTok Studio...")
        await page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=60000)
        await page.wait_for_timeout(8000)
        
        url = page.url
        print(f"📍 Current URL: {url}")
        
        if "login" in url:
            print("❌ Redirected to login - stopping")
            await browser.close()
            return
        
        print("✅ On upload page - searching for file input...")
        
        # Try different selectors
        selectors_to_try = [
            'input[type="file"]',
            'input[accept*="video"]',
            'input[type="file"][accept]',
            '[data-e2e="upload-input"]',
            'input.upload-input',
            'input#fileInput',
            'input[name="upload"]',
            '.upload-btn input',
            'button:has-text("Selecionar")',
            'button:has-text("Select")',
        ]
        
        found_selectors = []
        
        for selector in selectors_to_try:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    print(f"✅ Found '{selector}': {count} element(s)")
                    found_selectors.append(selector)
                    
                    # Try to get element details
                    try:
                        first = page.locator(selector).first
                        is_visible = await first.is_visible()
                        print(f"   - Visible: {is_visible}")
                    except:
                        pass
                else:
                    print(f"❌ Not found: '{selector}'")
            except Exception as e:
                print(f"⚠️ Error with '{selector}': {str(e)[:50]}")
        
        # Get all input elements
        print("\n📋 All input elements on page:")
        all_inputs = await page.locator('input').all()
        for i, inp in enumerate(all_inputs):
            try:
                inp_type = await inp.get_attribute('type')
                inp_id = await inp.get_attribute('id')
                inp_class = await inp.get_attribute('class')
                is_visible = await inp.is_visible()
                print(f"{i+1}. type={inp_type}, id={inp_id}, visible={is_visible}, class={inp_class[:50] if inp_class else 'N/A'}")
            except:
                pass
        
        # Save screenshot
        screenshot_path = "c:\\APPS - ANTIGRAVITY\\Synapse\\debug_upload_page.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n📸 Screenshot saved: {screenshot_path}")
        
        # Save HTML
        html = await page.content()
        html_path = "c:\\APPS - ANTIGRAVITY\\Synapse\\debug_upload_page.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"💾 HTML saved: {html_path}")
        
        print("\n⏳ Keeping browser open for 20 seconds for manual inspection...")
        await page.wait_for_timeout(20000)
        
        await browser.close()
        
        return found_selectors

if __name__ == "__main__":
    result = asyncio.run(debug_upload_selectors())
    print(f"\n✅ Found selectors: {result}")
