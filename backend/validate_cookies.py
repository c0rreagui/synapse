"""
Cookie Validation Script
Tests if session cookies are still valid by attempting to access TikTok Studio
"""
import asyncio
import os
import sys

# CRITICAL: Set Windows event loop policy FIRST
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.browser import launch_browser, close_browser
from core.session_manager import get_session_path

async def validate_session(profile_name: str):
    """
    Validates a profile's session by attempting to access TikTok Studio.
    Returns True if logged in, False if redirected to login page.
    """
    print(f"\n{'='*70}")
    print(f"VALIDANDO: {profile_name}")
    print(f"{'='*70}")
    
    session_path = get_session_path(profile_name)
    
    if not os.path.exists(session_path):
        print(f"ERRO: Arquivo de sessao nao encontrado: {session_path}")
        return False
    
    print(f"1. Arquivo de sessao encontrado: {session_path}")
    
    # Get file size and last modified
    file_size = os.path.getsize(session_path)
    file_mtime = os.path.getmtime(session_path)
    
    import datetime
    last_modified = datetime.datetime.fromtimestamp(file_mtime)
    print(f"   Tamanho: {file_size} bytes")
    print(f"   Ultima modificacao: {last_modified}")
    
    print(f"\n2. Iniciando navegador com cookies...")
    
    p, browser, context, page = await launch_browser(
        headless=False,
        storage_state=session_path
    )
    
    try:
        print(f"3. Navegando para TikTok Studio Upload...")
        await page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=60000)
        
        print(f"4. Aguardando carregamento (5s)...")
        await page.wait_for_timeout(5000)
        
        # Check current URL
        current_url = page.url
        print(f"5. URL atual: {current_url}")
        
        # Take screenshot
        screenshot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "validation")
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshot_dir, f"{profile_name}_validation.png")
        await page.screenshot(path=screenshot_path, full_page=False)
        print(f"6. Screenshot salvo: {screenshot_path}")
        
        # Check if we're on login page
        is_logged_in = False
        
        if "login" in current_url.lower():
            print(f"\n>>> RESULTADO: NAO LOGADO (redirecionado para login)")
        elif "tiktokstudio" in current_url:
            # Check for upload elements
            upload_selector_found = await page.locator('input[type="file"]').count() > 0
            
            if upload_selector_found:
                print(f"\n>>> RESULTADO: LOGADO (elemento de upload encontrado)")
                is_logged_in = True
            else:
                print(f"\n>>> RESULTADO: INCERTO (em TikTok Studio mas sem elemento de upload)")
                # Check for login button as additional verification
                login_button = await page.locator('text="Entrar", text="Login"').count()
                if login_button > 0:
                    print(f"    Botao de login detectado - provavelmente NAO LOGADO")
                else:
                    print(f"    Sem botao de login - pode estar logado mas pagina nao carregou")
        else:
            print(f"\n>>> RESULTADO: INCERTO (URL inesperada)")
        
        print(f"\n7. Aguardando 3s para voce ver a janela...")
        await page.wait_for_timeout(3000)
        
        return is_logged_in
        
    except Exception as e:
        print(f"\nERRO durante validacao: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print(f"8. Fechando navegador...")
        await close_browser(p, browser)

async def main():
    print("\n" + "#"*70)
    print("#  VALIDACAO DE COOKIES - PERFIS 1 E 2")
    print("#"*70)
    
    results = {}
    
    # Test Profile 1
    results["tiktok_profile_01"] = await validate_session("tiktok_profile_01")
    
    await asyncio.sleep(2)
    
    # Test Profile 2
    results["tiktok_profile_02"] = await validate_session("tiktok_profile_02")
    
    # Summary
    print("\n" + "="*70)
    print("RESUMO DA VALIDACAO")
    print("="*70)
    for profile, is_valid in results.items():
        status = "VALIDO" if is_valid else "INVALIDO"
        icon = "✓" if is_valid else "✗"
        print(f"  {icon} {profile}: {status}")
    
    print("\n" + "="*70)
    if all(results.values()):
        print("CONCLUSAO: Todos os perfis estao logados!")
    elif not any(results.values()):
        print("CONCLUSAO: Nenhum perfil esta logado - renovacao necessaria")
    else:
        print("CONCLUSAO: Alguns perfis precisam de renovacao")
    print("="*70)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
