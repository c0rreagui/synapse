"""
TESTE AUTOMATIZADO COMPLETO
1. Prepara video em pending
2. Aprova via API
3. Executa diretamente (bypass queue_worker)
4. Reporta resultados
"""
import requests
import time
import os
import asyncio
import sys
import logging

# Windows fix
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Minimal logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from core.manual_executor import execute_approved_video

API_BASE = "http://localhost:8000/api/v1"

def run_test():
    print("\n" + "#"*70)
    print("#  TESTE AUTOMATIZADO COMPLETO - PERFIL 1")
    print("#"*70)
    
    # 1. Find a test video in pending
    pending_dir = r"C:\APPS - ANTIGRAVITY\Synapse\backend\data\pending"
    videos = [f for f in os.listdir(pending_dir) if f.endswith('.mp4')]
    
    if not videos:
        print("\nERRO: Nenhum video disponivel em pending/")
        return
    
    test_video = videos[0]
    video_id = test_video.replace('.mp4', '')
    
    print(f"\n1. VIDEO SELECIONADO: {test_video}")
    
    # 2. Approve via API
    print(f"\n2. APROVANDO VIA API...")
    try:
        response = requests.post(f"{API_BASE}/queue/approve", json={
            "id": video_id,
            "action": "immediate",
            "viral_music_enabled": False,
            "privacy_level": "self_only",
            "target_profile_id": "tiktok_profile_01"
        }, timeout=10)
        
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   ERRO: {response.text}")
            return
        
        data = response.json()
        filename = data.get('filename')
        print(f"   OK! Movido para approved/: {filename}")
        
    except Exception as e:
        print(f"   ERRO na API: {e}")
        return
    
    # 3. Execute directly
    print(f"\n3. EXECUTANDO MANUAL_EXECUTOR...")
    print(f"   (Janela do navegador deve abrir)")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(execute_approved_video(filename))
        
        print(f"\n4. RESULTADO:")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        
        if result.get('status') == 'ready':
            print(f"\n>>> SUCESSO! BOT FUNCIONOU <<<")
        else:
            print(f"\n>>> FALHA! <<<")
            
    except Exception as e:
        print(f"\n>>> EXCEPTION <<<")
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        loop.close()
    
    # 4. Check for monitor output
    print(f"\n5. VERIFICANDO MONITOR...")
    monitor_dir = r"C:\APPS - ANTIGRAVITY\Synapse\MONITOR\runs"
    if os.path.exists(monitor_dir):
        folders = sorted([f for f in os.listdir(monitor_dir) if f.startswith("tiktok_profile")], reverse=True)
        if folders:
            latest = folders[0]
            print(f"   Pasta MONITOR mais recente: {latest}")
            
            screenshots_dir = os.path.join(monitor_dir, latest, "01_capturas", "screenshots")
            if os.path.exists(screenshots_dir):
                files = os.listdir(screenshots_dir)
                print(f"   Screenshots capturados: {len(files)}")
                if len(files) > 0:
                    print(f"   Primeiros arquivos:")
                    for f in files[:3]:
                        print(f"     - {f}")
            else:
                print(f"   AVISO: Pasta screenshots vazia")
    
    print(f"\n" + "="*70)
    print("TESTE CONCLUIDO - Verifique os resultados acima")
    print("="*70)

if __name__ == "__main__":
    run_test()
