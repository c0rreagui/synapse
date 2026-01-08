"""
Test para verificar se a navegação está funcionando corretamente
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.browser import launch_browser, close_browser
from core.session_manager import get_session_path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_navigation_only():
    session_name = "tiktok_profile_02"
    session_path = get_session_path(session_name)
    
    logger.info(f"🔧 Iniciando teste de navegação simples")
    logger.info(f"📂 Session: {session_path}")
    
    p, browser, context, page = await launch_browser(headless=False, storage_state=session_path)
    
    try:
        # Navega
        logger.info("🌍 Navegando para TikTok Studio...")
        await page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=60000)
        
        # Aguarda um tempo razoável
        logger.info("⏳ Aguardando 8 segundos...")
        await page.wait_for_timeout(8000)
        
        # Captura estado
        url = page.url
        title = await page.title()
        
        logger.info(f"\n📍 URL final: {url}")
        logger.info(f"📄 Title: {title}")
        
        if "login" in url:
            logger.error("❌ REDIRECTED TO LOGIN!")
        else:
            logger.info("✅ Stayed on TikTok Studio")
        
        # Testa seletores
        logger.info("\n🔍 Testando seletores...")
        
        input_count = await page.locator('input[type="file"]').count()
        logger.info(f"   input[type='file']: {input_count}")
        
        btn_count = await page.locator('button:has-text("Selecionar")').count()
        logger.info(f"   button:has-text('Selecionar'): {btn_count}")
        
        # Screenshot
        screenshot_path = "c:\\APPS - ANTIGRAVITY\\Synapse\\test_nav_only.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        logger.info(f"\n📸 Screenshot: {screenshot_path}")
        
        # Aguarda para inspeção manual
        logger.info("\n⏳ Mantendo browser aberto por 15 segundos...")
        await page.wait_for_timeout(15000)
        
    finally:
        await close_browser(p, browser)

if __name__ == "__main__":
    asyncio.run(test_navigation_only())
