import asyncio
import os
import sys

# Adiciona o diretório raiz ao path para importar módulos do core
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.browser import launch_browser, close_browser
from core.session_manager import get_session_path, save_session

PROFILE_ID = "tiktok_profile_1770135259969"

async def auto_heal():
    print(f"[HEAL] Iniciando Auto-Cura para {PROFILE_ID}...")
    session_path = get_session_path(PROFILE_ID)
    
    if not os.path.exists(session_path):
        print("[ERROR] Arquivo de sessao original nao encontrado.")
        return

    p = None
    browser = None
    try:
        # Lança no modo Headless do Docker, mas com stealth ativado e identidade fixa de Desktop
        p, browser, context, page = await launch_browser(
            headless=True,
            storage_state=session_path,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        print("[INFO] Navegando para TikTok Home...")
        try:
            await page.goto("https://www.tiktok.com/", timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"[WARN] Timeout/Erro na navegacao inicial: {e}")

        # 3. Verificar Login (Tentativa 1 - Check de Avatar)
        logged_in = False
        try:
            # Procura por elementos exclusivos de quem esta logado (href contém /@)
            await page.wait_for_selector('a[href*="/@"]', timeout=5000)
            print("[INFO] Avatar/Perfil detectado na Home.")
            logged_in = True
        except:
            print("[WARN] Avatar nao detectado na Home. Tentando ir para Upload...")

        # 4. Teste Definitivo: Navegar para Upload
        print("[INFO] Navegando para Pagina de Upload (Teste Real)...")
        await page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(8)
        
        # Tira screenshot do estado atual
        screenshot_path = os.path.abspath("heal_vibe_debug.png")
        await page.screenshot(path=screenshot_path)
        print(f"[INFO] Screenshot salva: {screenshot_path}")
        
        url = page.url
        print(f"[INFO] URL Final: {url}")
        
        if "login" in url or "signup" in url or "guest" in url:
            print("[FAIL] Redirecionado para Login/Guest. Sessao INVALIDA.")
            # Nao salvamos nada se falhou, para não corromper o arquivo com sessão de guest
        else:
            print("[SUCCESS] Permanecemos na pagina de Upload! Sessao VALIDA.")
            # Salvar o storage state atualizado (que agora tem tokens novos)
            await context.storage_state(path=session_path)
            print("[INFO] Sessao curada salva com sucesso.")

    except Exception as e:
        print(f"[ERROR] Erro critico no processo de cura: {e}")
    finally:
        await close_browser(p, browser)

if __name__ == "__main__":
    asyncio.run(auto_heal())
