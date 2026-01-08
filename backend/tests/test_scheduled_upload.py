"""
Upload agendado: fluxo manual agendamento
Data: 10/01/2026 às 15:45
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.uploader_monitored import upload_video_monitored
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

async def scheduled_upload():
    print("\n" + "="*60)
    print("📅 UPLOAD AGENDADO - Fluxo Manual Agendamento")
    print("="*60)
    
    # Configurações
    video_path = "c:\\APPS - ANTIGRAVITY\\Synapse\\backend\\errors\\p1_fluxo_manual.mp4"
    session_name = "tiktok_profile_02"  # Perfil Ibope
    caption = "🎬 Fluxo Manual de Agendamento - Testando sistema Synapse"
    schedule_time = "2026-01-10T15:45:00"  # 10 de janeiro às 15:45
    
    print(f"\n📹 Video: {os.path.basename(video_path)}")
    print(f"👤 Perfil: {session_name} (Ibope)")
    print(f"📝 Caption: {caption}")
    print(f"📅 Agendado para: 10/01/2026 às 15:45")
    print("="*60 + "\n")
    
    if not os.path.exists(video_path):
        print(f"❌ Vídeo não encontrado: {video_path}")
        return
    
    result = await upload_video_monitored(
        session_name=session_name,
        video_path=video_path,
        caption=caption,
        hashtags=["synapse", "automacao", "tiktok", "agendamento"],
        schedule_time=schedule_time,
        post=True,  # Enviar/agendar de verdade
        enable_monitor=False
    )
    
    print("\n" + "="*60)
    print("📊 RESULTADO")
    print("="*60)
    print(f"Status: {result['status']}")
    print(f"Message: {result.get('message', 'N/A')}")
    
    if result['status'] in ['ready', 'scheduled', 'posted']:
        print("\n✅ ✅ ✅ SUCESSO! Upload agendado com sucesso! ✅ ✅ ✅")
        print("📅 O vídeo será publicado em 10/01/2026 às 15:45")
    else:
        print(f"\n❌ Erro: {result.get('message')}")
        print(f"Screenshot: {result.get('screenshot_path', 'N/A')}")
    
    print("="*60 + "\n")
    
    return result

if __name__ == "__main__":
    asyncio.run(scheduled_upload())
