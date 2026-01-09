"""
👁️ DEBUG: Olho de Deus - Investigação do Seletor de Upload
============================================================
Executa um upload monitorado para capturar por que o seletor não é encontrado.
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.uploader_monitored import upload_video_monitored

async def main():
    print("👁️ OLHO DE DEUS - DEBUG SELETOR DE UPLOAD")
    print("=" * 60)
    
    # Usar um dos vídeos de teste reais
    video_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "tests", "test_videos", "e2e_test_video_01.mp4"
    )
    
    if not os.path.exists(video_path):
        print(f"❌ Vídeo não encontrado: {video_path}")
        return
    
    print(f"📹 Vídeo: {video_path}")
    print(f"📦 Tamanho: {os.path.getsize(video_path) / 1024 / 1024:.1f}MB")
    
    try:
        result = await upload_video_monitored(
            session_name="tiktok_profile_01",  # Usar perfil 1
            video_path=video_path,
            caption="🔍 Teste Debug Olho de Deus #SynapseDebug",
            schedule_time="2026-01-10T12:00",  # Agendar 2 dias à frente
            post=True,  # Tentar de verdade
            enable_monitor=True  # ATIVAR MONITORAMENTO TOTAL
        )
        
        print(f"\n{'='*60}")
        print(f"📊 RESULTADO: {result['status']}")
        print(f"💬 Mensagem: {result.get('message', 'N/A')}")
        
        if result.get('monitor_report'):
            print(f"📁 Relatório completo: {result['monitor_report']}")
        if result.get('trace_file'):
            print(f"🔍 Trace Playwright: {result['trace_file']}")
            
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
