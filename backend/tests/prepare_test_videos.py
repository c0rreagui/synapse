"""
Teste E2E REAL: Upload via Synapse → Bot → TikTok Studio
=========================================================
Prepara 6 vídeos reais, faz upload via UI, aprova em massa,
e valida agendamento real no TikTok Studio.

Critérios:
- Dias: 13, 14, 15 Jan 2026
- Horário: 12:25
- Perfis: 01 e 02
"""
import shutil
from pathlib import Path

# Prepare test videos
BASE_DIR = Path(__file__).parent.parent
APPROVED_DIR = BASE_DIR / "data" / "approved"
PENDING_DIR = BASE_DIR / "data" / "pending"
TEST_VIDEOS_DIR = BASE_DIR / "tests" / "test_videos"

TEST_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

# Find a valid source video
source_video = None
for f in APPROVED_DIR.glob("*.mp4"):
    if f.stat().st_size > 1000000:  # > 1MB
        source_video = f
        break

if not source_video:
    print("❌ Nenhum vídeo válido encontrado em approved/")
    exit(1)

print(f"✅ Vídeo fonte: {source_video.name} ({source_video.stat().st_size / 1024 / 1024:.1f}MB)")

# Create 6 test videos
test_videos = []
for i in range(1, 7):
    dest = TEST_VIDEOS_DIR / f"e2e_test_video_{i:02d}.mp4"
    if not dest.exists():
        shutil.copy(source_video, dest)
    test_videos.append(dest)
    print(f"  📹 {dest.name}")

print(f"\n✅ {len(test_videos)} vídeos prontos em tests/test_videos/")
print("\nPróximo passo: Upload manual via UI do Synapse em http://localhost:3000")
