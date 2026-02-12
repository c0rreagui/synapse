import sys
import os
import json
import time
from playwright.sync_api import sync_playwright

# Setup Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # synapse root
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
SESSIONS_DIR = os.path.join(BACKEND_DIR, "data", "sessions")
sys.path.append(BACKEND_DIR)

def login_and_capture(profile_id):
    print(f"Iniciando Assistente de Login para: {profile_id}")
    print("Abrindo navegador... Por favor, faca login no TikTok.")
    
    session_path = os.path.join(SESSIONS_DIR, f"{profile_id}.json")
    
    with sync_playwright() as p:
        # Launch headful browser
        browser = p.chromium.launch(headless=False)
        
        # Load existing cookies if any (to help with captcha or partial login)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Try to load previous cookies to avoid full re-login if possible
        if os.path.exists(session_path):
            try:
                with open(session_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cookies = data.get("cookies", []) if isinstance(data, dict) else data
                    if cookies:
                        # Clean cookies for playwright
                        valid_cookies = []
                        for c in cookies:
                            c_copy = c.copy()
                            if 'sameSite' in c_copy and c_copy['sameSite'] not in ['Strict', 'Lax', 'None']:
                                del c_copy['sameSite']
                            valid_cookies.append(c_copy)
                        context.add_cookies(valid_cookies)
            except Exception as e:
                print(f"[!] Could not load existing cookies: {e}")

        page = context.new_page()
        
        try:
            page.goto("https://www.tiktok.com/@", timeout=60000)
        except:
            print("[!] Timeout loading page, but continuing...")

        print("[*] Monitorando cookies de sessao...")
        
        # Wait for sessionid
        start_time = time.time()
        logged_in = False
        final_cookies = []
        
        while time.time() - start_time < 300: # 5 minutes timeout
            try:
                cookies = context.cookies()
                session_id = next((c for c in cookies if c['name'] == 'sessionid'), None)
                
                if session_id:
                    print("[+] LOGIN DETECTADO! Capturando sessao...")
                    # Wait a bit for other cookies (csrf, etc) to settle
                    time.sleep(3)
                    final_cookies = context.cookies()
                    logged_in = True
                    break
                
                if page.is_closed():
                    print("[-] Navegador fechado pelo usuario.")
                    break
            except Exception as e:
               if "Target closed" in str(e):
                   print("[-] Navegador fechado.")
                   break
               pass
                
            time.sleep(1)
            
        if logged_in:
            output_data = {
                "cookies": final_cookies,
                "updated_at": time.time(),
                "origins": []
            }
            
            with open(session_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=4)
                
            print(f"[+] Sessao salva com sucesso em: {session_path}")
            print("[+] Tudo pronto! O perfil deve ficar ATIVO em instantes.")
            
            time.sleep(2)
            try:
                browser.close()
            except:
                pass
            return True
        else:
            print("[!] Tempo limite excedido ou navegador fechado sem login.")
            try:
                 browser.close()
            except:
                pass
            return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python login_helper.py <profile_id>")
        # Default for debugging user's request
        target = "tiktok_profile_1770135259969" 
        login_and_capture(target)
    else:
        login_and_capture(sys.argv[1])
