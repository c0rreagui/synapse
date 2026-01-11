
import asyncio
import json
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.uploader_monitored import upload_video_monitored

SCHEDULE_FILE = r"c:\APPS - ANTIGRAVITY\Synapse\backend\data\schedule.json"
TEST_VIDEO_PATH = r"c:\APPS - ANTIGRAVITY\Synapse\backend\media\@p2_teste_multiconta.mp4"

async def main():
    print("👁️ INICIANDO DEBUG DO AGENDAMENTO COM OLHO DE DEUS")
    
    # 1. Load Schedule
    with open(SCHEDULE_FILE, 'r') as f:
        events = json.load(f)
        
    # 2. Filter Pending for tiktok_profile_02
    pending = [e for e in events if e['status'] == 'pending' and e['profile_id'] == 'tiktok_profile_02']
    
    if not pending:
        print("❌ Nenhum evento pendente encontrado para tiktok_profile_02")
        return

    # Take the last one (most recent)
    event = pending[-1]
    print(f"✅ Evento encontrado: {event['id']}")
    print(f"📅 Data Original: {event['scheduled_time']}")
    
    # 3. Override Video Path (Fixing external path issue)
    print(f"🔧 Substituindo vídeo: {event['video_path']} -> {TEST_VIDEO_PATH}")
    
    # 4. Trigger Upload with Monitor
    print("🚀 Iniciando upload monitorado...")
    try:
        result = await upload_video_monitored(
            session_name="tiktok_profile_02", # Mapped from profile_id
            video_path=TEST_VIDEO_PATH,
            caption="Teste de Agendamento - Synapse Auto",
            hashtags=["synapse", "debug", "test"],
            schedule_time=event['scheduled_time'],
            post=True, # We want to actually hit the schedule button
            enable_monitor=True, # THE EYE OF GOD
            viral_music_enabled=event.get('viral_music_enabled', False)
        )
        
        print(f"🏁 Resultado: {result['status']}")
        if result['status'] == 'success':
            print("✅ Upload/Agendamento realizado com sucesso!")
        else:
            print(f"❌ Erro: {result['message']}")
            
    except Exception as e:
        print(f"💥 Exceção fatal: {e}")

if __name__ == "__main__":
    # if sys.platform == 'win32':
    #     asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
