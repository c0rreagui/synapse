"""
TESTE FINAL DE PRODUCAO
Testa Perfil 1 e Perfil 2 com Privacy = Somente Eu
"""
import requests
import time
import os

API_BASE = "http://localhost:8000/api/v1"

def test_production():
    print("\n" + "#"*70)
    print("#  TESTE FINAL DE PRODUCAO - PERFIS 1 E 2")
    print("#"*70)
    
    tests = [
        {
            "video_id": "p1_f8990217",
            "profile_id": "tiktok_profile_01",
            "profile_name": "PERFIL 1 (tododiaumcorte.aleatorio)"
        },
        {
            "video_id": "p1_f854fcba", 
            "profile_id": "tiktok_profile_02",
            "profile_name": "PERFIL 2 (criandoibope)"
        }
    ]
    
    for i, test in enumerate(tests, 1):
        print(f"\n{'='*70}")
        print(f"TESTE {i}/2: {test['profile_name']}")
        print(f"{'='*70}")
        
        print(f"\n1. Aprovando video {test['video_id']}...")
        try:
            response = requests.post(f"{API_BASE}/queue/approve", json={
                "id": test['video_id'],
                "action": "immediate",
                "viral_music_enabled": False,
                "privacy_level": "self_only",
                "target_profile_id": test['profile_id']
            }, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   OK! Arquivo: {data.get('filename')}")
                print(f"   Privacy: {data.get('privacy_level')}")
            else:
                print(f"   ERRO: {response.status_code}")
                print(f"   {response.text}")
                continue
                
        except Exception as e:
            print(f"   Exception: {e}")
            continue
        
        # Aguardar processamento
        print(f"\n2. Aguardando queue_worker processar (30s)...")
        time.sleep(30)
        
        # Verificar estado
        print(f"\n3. Verificando resultado...")
        
        # Check processing
        processing_dir = r"C:\APPS - ANTIGRAVITY\Synapse\backend\processing"
        approved_dir = r"C:\APPS - ANTIGRAVITY\Synapse\backend\data\approved"
        
        video_file = f"{test['video_id']}.mp4"
        
        in_processing = os.path.exists(os.path.join(processing_dir, video_file))
        in_approved = os.path.exists(os.path.join(approved_dir, video_file))
        
        if in_processing:
            print(f"   STATUS: Ainda em PROCESSING (executando ou travado)")
        elif in_approved:
            print(f"   STATUS: Ainda em APPROVED (nao foi processado)")
        else:
            print(f"   STATUS: Concluido (nao esta em approved nem processing)")
        
        # Check monitor
        monitor_dir = r"C:\APPS - ANTIGRAVITY\Synapse\MONITOR\runs"
        if os.path.exists(monitor_dir):
            folders = sorted([f for f in os.listdir(monitor_dir) if "20260114" in f], reverse=True)
            if folders:
                latest = folders[0]
                print(f"   MONITOR: {latest}")
                
                screenshots_dir = os.path.join(monitor_dir, latest, "01_capturas", "screenshots")
                if os.path.exists(screenshots_dir):
                    files = os.listdir(screenshots_dir)
                    print(f"   Screenshots: {len(files)} arquivos")
                    
                    # Procurar screenshot de privacidade
                    privacy_shots = [f for f in files if 'privacidade' in f.lower() or 'privacy' in f.lower()]
                    if privacy_shots:
                        print(f"   Screenshot de privacidade encontrado: {privacy_shots[0]}")
        
        # Intervalo entre testes
        if i < len(tests):
            print(f"\n   Aguardando 10s antes do proximo teste...")
            time.sleep(10)
    
    print(f"\n{'='*70}")
    print("TESTES CONCLUIDOS")
    print(f"{'='*70}")
    print("\nVerifique:")
    print("1. Pasta MONITOR/runs para screenshots de privacidade")
    print("2. Interface TikTok Studio para confirmar videos agendados com 'Somente Eu'")
    print(f"{'='*70}")

if __name__ == "__main__":
    test_production()
