"""
👁️ INTEGRAÇÃO COMPLETA - Uploader com Monitoramento TOTAL
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.uploader_monitored import upload_video_monitored
import logging

# Configura log para arquivo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug_test.log", mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

async def main():
    print("👁️ TESTE COM MONITORAMENTO ULTRA-COMPLETO")
    print("=" * 60)
    
    # video_path = os.path.join("backend", "media", "@p2_teste_multiconta.mp4")
    # Usa arquivo de inputs (já que é o que estamos testando)
    video_path = os.path.join("backend", "inputs", "@p2_visual_test.mp4")
    
    result = await upload_video_monitored(
        session_name="tiktok_profile_02",
        video_path=video_path,
        caption="🎯 Teste Visual Agendamento CLICK #SynapseAI #Auto",
        schedule_time="2026-01-09T21:55",
        post=True # Vamos tentar clicar (mas em schedule mode ele deve clicar em Programar)
    )
    
    print("\n" + "=" * 60)
    print(f"✅ Resultado: {result['status']}")
    if result.get('monitor_report'):
        print(f"📊 Relatório salvo em: {result['monitor_report']}")
        print(f"\n👉 Para análise interativa:")
        print(f"   npx playwright show-trace {result.get('trace_file', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(main())
