import asyncio
import os
import sys
from playwright.async_api import async_playwright

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Configurations
SESSION_NAME = "tiktok_profile_01"
USER_DATA_DIR = os.path.join(BASE_DIR, "user_data", SESSION_NAME)

async def main():
    print(f"🚀 Iniciando Modo de Login Manual para: {SESSION_NAME}")
    print(f"📂 Pasta de Sessão: {USER_DATA_DIR}")
    
    async with async_playwright() as p:
        # Launch persistent context
        # Headless=False to let user interact
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            channel="chrome", # Use Chrome if available for better codec support
            args=["--start-maximized"],
            no_viewport=True
        )
        
        page = await browser.new_page() if len(browser.pages) == 0 else browser.pages[0]
        
        print("🌍 Abrindo TikTok...")
        await page.goto("https://www.tiktok.com/login", timeout=60000)
        
        print("\n" + "="*50)
        print("⚠️  AÇÃO NECESSÁRIA: FAÇA O LOGIN NO NAVEGADOR ABERTO")
        print("="*50)
        print("OBS: Se já estiver logado, apenas verifique se consegue acessar o 'Upload'.")
        print("Este script manterá o navegador aberto por 5 minutos.")
        print("Pressione Ctrl+C no terminal para encerrar mais cedo (isso salvará a sessão).")
        
        try:
            # Wait for 5 minutes allow user to login
            for i in range(300):
                await asyncio.sleep(1)
                if i % 30 == 0:
                    print(f"⏳ Tempo restante: {300-i}s...")
        except KeyboardInterrupt:
            print("🛑 Interrompido pelo usuário.")
        finally:
            print("💾 Salvando estado e fechando...")
            await browser.close()
            print("✅ Sessão salva. Agora você pode rodar o teste automatizado.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
