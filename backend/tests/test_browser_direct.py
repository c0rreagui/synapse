"""
Test browser.py directly to diagnose cookie loading
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.browser import launch_browser, close_browser
from core.session_manager import get_session_path
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_browser_direct():
    session_name = "tiktok_profile_02"
    session_path = get_session_path(session_name)
    
    print(f"\n{'='*60}")
    print("TESTE DIRETO DO BROWSER.PY")
    print(f"{'='*60}")
    print(f"Session name: {session_name}")
    print(f"Session path: {session_path}")
    print(f"Session exists: {os.path.exists(session_path)}")
    print(f"{'='*60}\n")
    
    # Verifica se o arquivo realmente existe
    if not os.path.exists(session_path):
        print("❌ ERRO: Arquivo de sessão não encontrado!")
        return
    
    # Verifica conteúdo do arquivo
    import json
    with open(session_path, 'r') as f:
        session_data = json.load(f)
        cookies = session_data.get('cookies', [])
        print(f"Cookies no arquivo: {len(cookies)}")
        has_sessionid = any(c['name'] == 'sessionid' for c in cookies)
        print(f"Tem sessionid: {has_sessionid}")
    
    print("\n🚀 Launching browser via browser.py...")
    
    p, browser, context, page = await launch_browser(
        headless=False, 
        storage_state=session_path
    )
    
    print("✅ Browser launched!")
    
    # Verifica cookies no context
    cookies_in_context = await context.cookies()
    print(f"\n🍪 Cookies no context após launch: {len(cookies_in_context)}")
    has_sessionid = any(c['name'] == 'sessionid' for c in cookies_in_context)
    print(f"Tem sessionid no context: {has_sessionid}")
    
    # Lista alguns cookies importantes
    important = ['sessionid', 'sid_tt', 'sid_guard']
    for name in important:
        cookie = next((c for c in cookies_in_context if c['name'] == name), None)
        if cookie:
            print(f"   ✅ {name}: {cookie['value'][:20]}...")
        else:
            print(f"   ❌ {name}: MISSING!")
    
    print("\n🌍 Navegando para TikTok...")
    await page.goto("https://www.tiktok.com/", timeout=30000)
    await page.wait_for_timeout(3000)
    
    url = page.url
    print(f"\n📍 URL final: {url}")
    
    if "login" in url:
        print("❌ REDIRECTED TO LOGIN!")
    else:
        print("✅ Stayed on TikTok - cookies working!")
    
    # Screenshot
    screenshot = "c:\\APPS - ANTIGRAVITY\\Synapse\\browser_py_test.png"
    await page.screenshot(path=screenshot)
    print(f"📸 Screenshot: {screenshot}")
    
    await page.wait_for_timeout(5000)
    await close_browser(p, browser)
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test_browser_direct())
