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
    print("👁️ BATERIA DE TESTES OLHO DE DEUS (3 Dias)")
    print("=" * 60)
    
    video_path = os.path.join("backend", "inputs", "@p2_visual_test.mp4")
    
    test_cases = [
        {"date": "2026-01-09", "time": "10:15", "desc": "Teste Dia 09 - Manhã"},
        # {"date": "2026-01-10", "time": "14:30", "desc": "Teste Dia 10 - Tarde"},
        # {"date": "2026-01-11", "time": "20:45", "desc": "Teste Dia 11 - Noite"} 
        # Vou rodar UM POR UM para não sobrecarregar ou você prefere sequencial?
        # Vou rodar sequencial com pausa.
    ]
    # Atualizando para rodar os 3 como pedido
    test_cases = [
        {"timestamp": "2026-01-09T10:15", "desc": "Dia 9 Manhã"},
        {"timestamp": "2026-01-10T14:30", "desc": "Dia 10 Tarde"},
        {"timestamp": "2026-01-11T20:45", "desc": "Dia 11 Noite"}
    ]

    for i, case in enumerate(test_cases):
        print(f"\n🚀 INICIANDO TESTE {i+1}/3: {case['desc']} ({case['timestamp']})")
        
        try:
            result = await upload_video_monitored(
                session_name="tiktok_profile_02",
                video_path=video_path,
                caption=f"🎯 {case['desc']} Olho de Deus #SynapseTest",
                schedule_time=case['timestamp'],
                post=True,
                enable_monitor=True
            )
            
            print(f"✅ Resultado Teste {i+1}: {result['status']}")
            if result.get('monitor_report'):
                print(f"📊 Relatório: {result['monitor_report']}")
            
            # Pausa entre testes para respirar
            if i < len(test_cases) - 1:
                print("⏳ Aguardando 10s para próximo teste...")
                await asyncio.sleep(10)
                
        except Exception as e:
            print(f"❌ Falha no Teste {i+1}: {e}")
            
    print("\n🏁 BATERIA DE TESTES CONCLUÍDA")

if __name__ == "__main__":
    asyncio.run(main())
