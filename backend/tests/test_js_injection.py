"""
Test JavaScript Injection Anti-Popup
"""
import asyncio
import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.uploader import upload_video

# Config
VIDEO_PATH = os.path.join(os.path.dirname(__file__), "media", "@p2_teste_multiconta.mp4")
CAPTION = "🔥 Teste JS Injection Anti-Popup #teste"

async def main():
    print("=" * 60)
    print("💉 TESTE: JavaScript Injection Anti-Popup")
    print("=" * 60)
    print(f"📹 Video: {VIDEO_PATH}")
    print(f"📝 Caption: {CAPTION}")
    print()
    
    if not os.path.exists(VIDEO_PATH):
        print(f"❌ Video não encontrado: {VIDEO_PATH}")
        return
    
    try:
        result = await upload_video(
            session_name="tiktok_profile_01",
            video_path=VIDEO_PATH,
            caption=CAPTION,
            hashtags=["jsinjection", "antipopup"],
            post=False  # Safety: Never auto-post
        )
        
        print()
        print("=" * 60)
        print("📊 RESULTADO:")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        print(f"   Screenshot: {result.get('screenshot_path')}")
        print("=" * 60)
        
    except Exception as e:
        print(f"💥 Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
