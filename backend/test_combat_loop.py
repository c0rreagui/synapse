"""
Test Combat Loop v2 - Quick test for popup killer and caption fill
"""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.uploader import upload_video
from core.browser import launch_browser, close_browser

# Config
VIDEO_PATH = os.path.join(os.path.dirname(__file__), "media", "@p2_teste_multiconta.mp4")
SESSION_PATH = os.path.join(os.path.dirname(__file__), "data", "sessions", "tiktok_profile_01.json")
CAPTION = "🔥 Teste Combat Loop v2 #teste #automacao"

async def main():
    print("=" * 50)
    print("🎮 TESTE COMBAT LOOP v2")
    print("=" * 50)
    print(f"📹 Video: {VIDEO_PATH}")
    print(f"🔑 Session: {SESSION_PATH}")
    print(f"📝 Caption: {CAPTION}")
    print()
    
    if not os.path.exists(VIDEO_PATH):
        print(f"❌ Video não encontrado: {VIDEO_PATH}")
        return
    
    if not os.path.exists(SESSION_PATH):
        print(f"❌ Session não encontrada: {SESSION_PATH}")
        return
    
    p = None
    browser = None
    
    try:
        # Launch browser
        print("🌐 Abrindo browser...")
        p, browser, context, page = await launch_browser(
            headless=False,
            storage_state=SESSION_PATH
        )
        
        # Run upload
        print("🚀 Iniciando upload...")
        result = await upload_video(
            page=page,
            video_path=VIDEO_PATH,
            caption=CAPTION,
            profile_id="p1",
            session_name="tiktok_profile_01",
            hashtags=["combatloop", "v2"]
        )
        
        print()
        print("=" * 50)
        print("📊 RESULTADO:")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        print(f"   Screenshot: {result.get('screenshot_path')}")
        print("=" * 50)
        
        # Keep browser open for inspection
        print("\n⏸️ Browser aberto. Pressione ENTER para fechar...")
        input()
        
    except Exception as e:
        print(f"💥 Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if p and browser:
            await close_browser(p, browser)
        print("✅ Teste finalizado!")

if __name__ == "__main__":
    asyncio.run(main())
