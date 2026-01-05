from playwright.sync_api import sync_playwright
import json
import time
import os

def debug_login():
    # Use absolute path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    session_path = os.path.join(base_dir, "data", "sessions", "tiktok_profile_02.json")
    static_dir = os.path.join(base_dir, "static")
    
    print(f"Session path: {session_path}")
    
    # 1. Carregar os cookies manualmente
    with open(session_path, 'r') as f:
        data = json.load(f)
        cookies = data["cookies"] if "cookies" in data else data
    
    print(f"Loaded {len(cookies)} cookies")

    with sync_playwright() as p:
        # 2. Lançar navegador com User-Agent fixo (para parecer o Chrome Real)
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        
        # 3. Criar contexto COM user-agent específico
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # 4. Injetar cookies na força bruta
        try:
            context.add_cookies(cookies)
            print("✅ Cookies injetados no contexto.")
        except Exception as e:
            print(f"❌ Erro ao injetar cookies: {e}")

        # 5. Navegar
        page = context.new_page()
        print("📍 Navegando para upload...")
        page.goto("https://www.tiktok.com/tiktokstudio/upload")
        
        # 6. Esperar para vermos o resultado
        page.wait_for_timeout(5000)
        
        # Check URL
        current_url = page.url
        print(f"📌 Current URL: {current_url}")
        
        if "login" in current_url.lower():
            print("❌ FAILED: Still on login page")
        else:
            print("✅ SUCCESS: Logged in!")
        
        # 7. Screenshot
        screenshot_path = os.path.join(static_dir, "debug_p2_manual.png")
        page.screenshot(path=screenshot_path)
        print(f"📸 Screenshot salvo em {screenshot_path}")
        
        # Manter aberto por 30s para inspeção visual
        print("⏳ Mantendo navegador aberto por 30s...")
        time.sleep(30)
        browser.close()
        print("👋 Done!")

if __name__ == "__main__":
    debug_login()
