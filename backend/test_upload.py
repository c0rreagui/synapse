"""
Teste Manual do DOM Nuker - Upload direto
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.uploader import upload_video

async def main():
    print("🚀 Iniciando teste manual do DOM Nuker...")
    
    video_path = os.path.join("backend", "media", "@p2_teste_multiconta.mp4")
    
    result = await upload_video(
        session_name="tiktok_profile_01",
        video_path=video_path,
        caption="🎯 Teste DOM Nuker Cirúrgico - React Joyride Fix",
        schedule_time="2026-01-06T16:00",
        post=False
    )
    
    print(f"\n✅ Resultado: {result}")

if __name__ == "__main__":
    asyncio.run(main())
