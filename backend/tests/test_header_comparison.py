"""
Capture and compare HTTP headers between successful and failed navigations
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def capture_headers_comparison():
    session_file = "c:\\APPS - ANTIGRAVITY\\Synapse\\backend\\data\\sessions\\tiktok_profile_02.json"
    
    # Read session to get original User-Agent if stored
    with open(session_file, 'r') as f:
        session_data = json.load(f)
    
    results = {
        "session_cookies_count": len(session_data.get('cookies', [])),
        "tests": []
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=session_file)
        
        # TEST 1: Homepage (known to work)
        print("\n" + "="*60)
        print("TEST 1: TikTok Homepage (Should Work)")
        print("="*60)
        
        page1 = await context.new_page()
        
        # Capture request headers
        homepage_headers = {}
        
        async def capture_homepage_headers(request):
            if "tiktok.com" in request.url and request.url == "https://www.tiktok.com/":
                homepage_headers['url'] = request.url
                homepage_headers['headers'] = request.headers
                homepage_headers['method'] = request.method
        
        page1.on("request", capture_homepage_headers)
        
        await page1.goto("https://www.tiktok.com/", timeout=30000)
        await page1.wait_for_timeout(3000)
        
        url1 = page1.url
        cookies1 = await context.cookies()
        
        print(f"Final URL: {url1}")
        print(f"Cookies after navigation: {len(cookies1)}")
        print(f"Has sessionid: {any(c['name'] == 'sessionid' for c in cookies1)}")
        
        if "login" in url1:
            print("❌ FAILED - Redirected to login")
        else:
            print("✅ SUCCESS - Stayed on TikTok")
        
        results["tests"].append({
            "name": "Homepage",
            "url": url1,
            "success": "login" not in url1,
            "cookies_count": len(cookies1),
            "has_sessionid": any(c['name'] == 'sessionid' for c in cookies1),
            "headers": homepage_headers.get('headers', {})
        })
        
        # TEST 2: TikTok Studio (known to fail)
        print("\n" + "="*60)
        print("TEST 2: TikTok Studio Upload (Fails)")
        print("="*60)
        
        page2 = await context.new_page()
        
        # Capture request headers
        studio_headers = {}
        
        async def capture_studio_headers(request):
            if "tiktokstudio" in request.url:
                studio_headers['url'] = request.url
                studio_headers['headers'] = request.headers
                studio_headers['method'] = request.method
        
        page2.on("request", capture_studio_headers)
        
        await page2.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=30000)
        await page2.wait_for_timeout(3000)
        
        url2 = page2.url
        cookies2 = await context.cookies()
        
        print(f"Final URL: {url2}")
        print(f"Cookies after navigation: {len(cookies2)}")
        print(f"Has sessionid: {any(c['name'] == 'sessionid' for c in cookies2)}")
        
        if "login" in url2:
            print("❌ FAILED - Redirected to login")
        else:
            print("✅ SUCCESS - Stayed on Studio")
        
        results["tests"].append({
            "name": "TikTok Studio",
            "url": url2,
            "success": "login" not in url2,
            "cookies_count": len(cookies2),
            "has_sessionid": any(c['name'] == 'sessionid' for c in cookies2),
            "headers": studio_headers.get('headers', {})
        })
        
        # Compare headers
        print("\n" + "="*60)
        print("HEADER COMPARISON")
        print("="*60)
        
        if homepage_headers.get('headers') and studio_headers.get('headers'):
            home_h = homepage_headers['headers']
            studio_h = studio_headers['headers']
            
            all_keys = set(home_h.keys()) | set(studio_h.keys())
            
            for key in sorted(all_keys):
                home_val = home_h.get(key, "MISSING")
                studio_val = studio_h.get(key, "MISSING")
                
                if home_val != studio_val:
                    print(f"\n🔍 {key}:")
                    print(f"   Homepage: {home_val[:100] if isinstance(home_val, str) else home_val}")
                    print(f"   Studio:   {studio_val[:100] if isinstance(studio_val, str) else studio_val}")
        
        # Save results
        output_file = "c:\\APPS - ANTIGRAVITY\\Synapse\\header_comparison.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        await page1.wait_for_timeout(5000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_headers_comparison())
