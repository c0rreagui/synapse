import requests
import time
import os

API_BASE = "http://localhost:8000/api/v1"

# Test 1: Approve video for Profile 1
print("=" * 60)
print("TEST 1: Approvando vídeo para Perfil 1 (tiktok_profile_01)")
print("=" * 60)

response = requests.post(f"{API_BASE}/queue/approve", json={
    "id": "p1_5aad2915",
    "action": "immediate",
    "viral_music_enabled": True,
    "privacy_level": "self_only"
})

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Wait for worker to pick it up
print("\n⏳ Aguardando 10s para o queue_worker processar...")
time.sleep(10)

# Check if file was moved to approved
approved_dir = r"C:\APPS - ANTIGRAVITY\Synapse\backend\data\approved"
print(f"\n📂 Arquivos em approved/:")
if os.path.exists(approved_dir):
    for f in os.listdir(approved_dir):
        print(f"  - {f}")
else:
    print("  (vazio)")

print("\n" + "=" * 60)
print("Verificar logs do queue_worker no terminal")
print("=" * 60)
