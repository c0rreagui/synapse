"""
TESTE FINAL COM NOVOS VIDEOS
"""
import requests
import time
import os

API_BASE = "http://localhost:8000/api/v1"

def test():
    print("\n" + "="*70)
    print("TESTE FINAL - PERFIS 1 E 2")
    print("="*70)
    
    # Test Profile 1
    print("\n[1/2] PERFIL 1 (tiktok_profile_01)")
    print("-" * 70)
    try:
        r = requests.post(f"{API_BASE}/queue/approve", json={
            "id": "profile1_test",
            "action": "immediate",
            "viral_music_enabled": False,
            "privacy_level": "self_only",
            "target_profile_id": "tiktok_profile_01"
        }, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print(f"OK! Video aprovado para Perfil 1")
        else:
            print(f"ERRO: {r.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    time.sleep(5)
    
    # Test Profile 2
    print("\n[2/2] PERFIL 2 (tiktok_profile_02)")
    print("-" * 70)
    try:
        r = requests.post(f"{API_BASE}/queue/approve", json={
            "id": "profile2_test",
            "action": "immediate",
            "viral_music_enabled": False,
            "privacy_level": "self_only",
            "target_profile_id": "tiktok_profile_02"
        }, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print(f"OK! Video aprovado para Perfil 2")
        else:
            print(f"ERRO: {r.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    print("\n" + "="*70)
    print("AGUARDANDO PROCESSAMENTO (60s)...")
    print("="*70)
    time.sleep(60)
    
    print("\n" + "="*70)
    print("VERIFICANDO RESULTADOS")
    print("="*70)
    
    # Check MONITOR
    monitor_dir = r"C:\APPS - ANTIGRAVITY\Synapse\MONITOR\runs"
    if os.path.exists(monitor_dir):
        folders = sorted([f for f in os.listdir(monitor_dir) if "20260114" in f], reverse=True)
        print(f"\nFolders MONITOR hoje: {len(folders)}")
        for folder in folders[:3]:
            print(f"  - {folder}")
    
    print("\n" + "="*70)
    print("TESTE CONCLUIDO")
    print("Verifique TikTok Studio para confirmar agendamentos 'Somente Eu'")
    print("="*70)

if __name__ == "__main__":
    test()
