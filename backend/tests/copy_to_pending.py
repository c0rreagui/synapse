"""
Copia vídeos reais para data/pending e cria metadatas
"""
import shutil
import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
TEST_VIDEOS = BASE_DIR / "tests" / "test_videos"
PENDING = BASE_DIR / "data" / "pending"

PENDING.mkdir(parents=True, exist_ok=True)

profiles = ["tiktok_profile_01", "tiktok_profile_02"]

for i in range(1, 7):
    src = TEST_VIDEOS / f"e2e_test_video_{i:02d}.mp4"
    if not src.exists():
        print(f"❌ {src.name} não encontrado")
        continue
    
    profile = profiles[(i-1) % 2]
    dest = PENDING / src.name
    
    # Copy video
    if not dest.exists():
        shutil.copy(src, dest)
        print(f"✅ Copiado: {src.name} ({src.stat().st_size / 1024 / 1024:.1f}MB)")
    
    # Create metadata
    metadata = {
        "uploaded_at": datetime.now().isoformat(),
        "original_filename": src.name,
        "profile_id": profile,
        "status": "pending"
    }
    
    meta_file = PENDING / f"{src.name}.json"
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"   📝 Metadata: {profile}")

print(f"\n✅ 6 vídeos em data/pending/")
print("\n📋 Próximos passos:")
print("1. Recarregar http://localhost:3000")
print("2. Verificar 'Aprovação Manual' (6 novos vídeos)")
print("3. Selecionar todos e aprovar em massa (13,14,15/01 @ 12:25)")
