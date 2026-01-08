"""
Test with TikTok Monitor (Olho de Deus) ACTIVATED
"""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.uploader_monitored import upload_video_monitored

async def test_with_monitor():
    print("👁️ ATIVANDO OLHO DE DEUS (Monitor Ultra-Detalhado)\n")
    
    # Use approved video
    video_path = "c:\\APPS - ANTIGRAVITY\\Synapse\\backend\\data\\approved\\p2_test_simplified_browser.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        # Try to find any video in approved
        approved_dir = "c:\\APPS - ANTIGRAVITY\\Synapse\\backend\\data\\approved"
        for f in os.listdir(approved_dir):
            if f.endswith(".mp4"):
                video_path = os.path.join(approved_dir, f)
                print(f"✅ Using: {f}")
                break
    
    result = await upload_video_monitored(
        session_name="tiktok_profile_02",
        video_path=video_path,
        caption="🔬 Teste com Olho de Deus #teste #synapse #monitoring",
        hashtags=["teste", "synapse", "monitoring"],
        schedule_time=None,
        post=True,  # Immediate post
        enable_monitor=True  # 👁️ ATIVAR MONITOR
    )
    
    print(f"\n{'='*60}")
    print(f"RESULTADO FINAL:")
    print(f"  Status: {result['status']}")
    print(f"  Message: {result.get('message', 'N/A')}")
    print(f"  Screenshot: {result.get('screenshot_path', 'N/A')}")
    print(f"{'='*60}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_with_monitor())
