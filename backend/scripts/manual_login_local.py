import asyncio
import os
import json
from playwright.async_api import async_playwright

# Configuração
SESSION_NAME = "opiniaoviral"  # Seu perfil
OUTPUT_DIR = "d:/APPS - ANTIGRAVITY/Synapse/backend/data/sessions" # Caminho absoluto que você já tem
os.makedirs(OUTPUT_DIR, exist_ok=True)
SESSION_FILE = os.path.join(OUTPUT_DIR, f"tiktok_profile_1770307556827.json") # ID Fixo do seu perfil opiniaoviral

async def run():
    print(f"🚀 Iniciando captura de sessão para: {SESSION_NAME}")
    print("ℹ️  Um navegador será aberto. Faça login no TikTok manualmente.")
    print("ℹ️  Quando terminar e estiver na página inicial logado, feche o navegador.")

    async with async_playwright() as p:
        # Lança navegador com CABEÇALHO DE GENTE (Não de robô)
        browser = await p.chromium.launch(
            headless=False, 
            channel="chrome", # Tenta usar o Chrome instalado
            args=["--enable-logging", "--v=1"]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="pt-BR"
        )
        
        page = await context.new_page()
        
        try:
            await page.goto("https://www.tiktok.com/login", timeout=60000)
        except:
            print("⚠️ Timeout no carregamento inicial, mas navegador segue aberto.")

        # Espera o navegador ser fechado pelo usuário
        try:
            # Espera até URL mudar para feed (indicativo de sucesso) ou user fechar
            await page.wait_for_url("**/foryou**", timeout=300000)
            print("✅ Login detectado (feed carregado). Salvando sessão...")
        except:
            pass 

        # Salva o estado completo (Cookies + LocalStorage + SessionStorage)
        # É ISSO que falta quando copiamos só cookies!
        await context.storage_state(path=SESSION_FILE)
        
        print(f"\n✅ Sessão salva com sucesso em: {os.path.abspath(SESSION_FILE)}")
        print(" O Synapse Docker já deve conseguir ler este arquivo diretamente!")

if __name__ == "__main__":
    asyncio.run(run())
