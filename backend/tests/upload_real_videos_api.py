"""
Teste E2E REAL: Upload via API com vídeos reais + Aprovação + Bot
==================================================================
"""
import requests
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TEST_VIDEOS = BASE_DIR / "tests" / "test_videos"
API = "http://localhost:8000"

# Upload 6 vídeos reais via API
profiles = ["tiktok_profile_01", "tiktok_profile_02"]
videos = []

for i in range(1, 7):
    video_path = TEST_VIDEOS / f"e2e_test_video_{i:02d}.mp4"
    
    if not video_path.exists():
        print(f"❌ Vídeo não encontrado: {video_path}")
        continue
    
    profile = profiles[(i-1) % 2]  # Alternar entre perfis
    
    print(f"\n📤 Upload vídeo {i}/6: {video_path.name} → {profile}")
    print(f"   Tamanho: {video_path.stat().st_size / 1024 / 1024:.1f}MB")
    
    with open(video_path, 'rb') as f:
        files = {'file': (video_path.name, f, 'video/mp4')}
        data = {'profile_id': profile}
        
        try:
            r = requests.post(f"{API}/ingestion/upload", files=files, data=data, timeout=60)
            if r.ok:
                result = r.json()
                print(f"   ✅ ID: {result.get('id', 'N/A')}")
                videos.append(result.get('id'))
            else:
                print(f"   ❌ Erro HTTP {r.status_code}")
                print(f"   Resposta: {r.text[:300]}")
        except Exception as e:
            print(f"   ❌ Exceção: {e}")

print(f"\n{'='*60}")
print(f"✅ {len(videos)} vídeos enviados via API")
print(f"{'='*60}")
print("\n📋 Próximos passos:")
print("1. Recarregar dashboard http://localhost:3000")
print("2. Verificar 'Aprovação Manual' (devem aparecer 6 vídeos)")
print("3. Selecionar todos via checkbox")
print("4. Aprovar em massa:")
print("   - Videos 1-2: 13/01/2026 @ 12:25")
print("   - Videos 3-4: 14/01/2026 @ 12:25")
print("   - Videos 5-6: 15/01/2026 @ 12:25")
print("5. Aguardar bot processar (Factory Watcher)")
print("6. Verificar TikTok Studio")

