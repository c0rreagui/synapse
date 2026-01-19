import requests
import time
import os

API_BASE = "http://localhost:8000/api/v1"

def test_profile(profile_id, video_id, profile_name):
    print("\n" + "=" * 70)
    print(f"TESTE: {profile_name} | Privacy: Somente Eu")
    print("=" * 70)
    
    # Aprovar video
    print(f"\n1. Aprovando video {video_id}...")
    response = requests.post(f"{API_BASE}/queue/approve", json={
        "id": video_id,
        "action": "immediate",
        "viral_music_enabled": True,
        "privacy_level": "self_only",
        "target_profile_id": profile_id
    })
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        filename = data.get('filename')
        print(f"   OK! Arquivo movido: {filename}")
        print(f"\n2. Aguardando queue_worker processar (30s)...")
        time.sleep(30)
        
        # Verificar MONITOR
        monitor_base = r"C:\APPS - ANTIGRAVITY\Synapse\MONITOR\runs"
        print(f"\n3. Procurando pasta MONITOR mais recente...")
        
        if os.path.exists(monitor_base):
            folders = [f for f in os.listdir(monitor_base) if f.startswith("tiktok_profile")]
            folders.sort(reverse=True)
            
            if folders:
                latest = folders[0]
                print(f"   Pasta mais recente: {latest}")
                
                # Verificar screenshots
                screenshots_dir = os.path.join(monitor_base, latest, "01_capturas", "screenshots")
                if os.path.exists(screenshots_dir):
                    files = os.listdir(screenshots_dir)
                    print(f"   Screenshots capturados: {len(files)}")
                    for f in files[:5]:  # Mostrar primeiros 5
                        print(f"     - {f}")
                else:
                    print("   AVISO: Pasta de screenshots vazia ou nao existe")
            else:
                print("   AVISO: Nenhuma pasta MONITOR encontrada")
        
        print(f"\n4. Verificando estado final...")
        # Verificar processing
        processing_dir = r"C:\APPS - ANTIGRAVITY\Synapse\backend\processing"
        if os.path.exists(processing_dir):
            files = [f for f in os.listdir(processing_dir) if filename.replace('.json', '') in f]
            if files:
                print(f"   Video ainda em PROCESSING:")
                for f in files:
                    print(f"     - {f}")
            else:
                print(f"   Video NAO esta em processing (concluido ou erro)")
    else:
        print(f"   ERRO: {response.text}")

# Testes
print("\n" + "#" * 70)
print("#  TESTE AUTOMATIZADO: Aprovacao -> Queue Worker -> Privacy")
print("#" * 70)

# Limpar approved primeiro
print("\nLimpando pasta approved...")
approved_dir = r"C:\APPS - ANTIGRAVITY\Synapse\backend\data\approved"
if os.path.exists(approved_dir):
    for f in os.listdir(approved_dir):
        if f.endswith('.mp4') or f.endswith('.json'):
            os.remove(os.path.join(approved_dir, f))
    print("  OK")

# Test Profile 1
test_profile("tiktok_profile_01", "p1_f76a9aa1", "PERFIL 1 (tiktok_profile_01)")

print("\n" + "=" * 70)
print("TESTE CONCLUIDO")
print("=" * 70)
