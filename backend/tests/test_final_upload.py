"""
Final end-to-end upload test with simplified config
"""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.uploader_monitored import upload_video_monitored

async def final_upload_test():
    print("\n" + "="*60)
    print("🎯 TESTE FINAL: Upload Completo com Config Simplificada")
    print("="*60 + "\n")
    
    video_path = "c:\\APPS - ANTIGRAVITY\\Synapse\\backend\\data\\pending\\p2_test123.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return
    
    print(f"📹 Video: {os.path.basename(video_path)}")
    print(f"👤 Profile: tiktok_profile_02")
    print(f"📝 Caption: Teste final - config simplificada")
    print(f"🎬 Action: Post Imediato\n")
    
    result = await upload_video_monitored(
        session_name="tiktok_profile_02",
        video_path=video_path,
        caption="🎯 Teste FINAL - Config simplificada funcionando! #teste #synapse",
        hashtags=["teste", "synapse", "success"],
        schedule_time=None,
        post=True,  # Immediate post
        enable_monitor=False  # Disable monitor for cleaner output
    )
    
    print("\n" + "="*60)
    print("📊 RESULTADO FINAL")
    print("="*60)
    print(f"Status: {result['status']}")
    print(f"Message: {result.get('message', 'N/A')}")
    
    if result['status'] == 'ready':
        print("\n✅ ✅ ✅ SUCESSO TOTAL! ✅ ✅ ✅")
        print("O bot funcionou corretamente com cookies!")
    else:
        print(f"\n❌ Erro: {result.get('message')}")
        print(f"Screenshot: {result.get('screenshot_path', 'N/A')}")
    
    print("="*60 + "\n")
    
    return result

if __name__ == "__main__":
    asyncio.run(final_upload_test())
