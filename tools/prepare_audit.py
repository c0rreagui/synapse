
import os
import shutil
import glob

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
DATA_DIR = os.path.join(BACKEND_DIR, "data")
PENDING_DIR = os.path.join(DATA_DIR, "pending")
APPROVED_DIR = os.path.join(DATA_DIR, "approved")
PROCESSING_DIR = os.path.join(BACKEND_DIR, "processing")
DONE_DIR = os.path.join(BACKEND_DIR, "done")
ERRORS_DIR = os.path.join(BACKEND_DIR, "errors")
TEST_VIDEOS_SRC = os.path.join(BACKEND_DIR, "tests", "test_videos")

DIRS_TO_CLEAN = [PENDING_DIR, APPROVED_DIR, PROCESSING_DIR, DONE_DIR, ERRORS_DIR]

def clean_directories():
    print("🧹 Limpando diretórios...")
    for d in DIRS_TO_CLEAN:
        if os.path.exists(d):
            files = glob.glob(os.path.join(d, "*"))
            for f in files:
                try:
                    if os.path.isfile(f):
                        os.remove(f)
                    elif os.path.isdir(f):
                        shutil.rmtree(f)
                except Exception as e:
                    print(f"⚠️ Erro ao limpar {f}: {e}")
        else:
            os.makedirs(d)
    print("✅ Diretórios limpos.")

def populate_pending():
    print("📦 Populando pending com vídeos de teste...")
    
    # Check source
    if not os.path.exists(TEST_VIDEOS_SRC):
        print(f"❌ Diretório de vídeos de teste não encontrado: {TEST_VIDEOS_SRC}")
        return

    src_files = [f for f in os.listdir(TEST_VIDEOS_SRC) if f.endswith('.mp4')]
    if not src_files:
        print("❌ Nenhum vídeo fonte encontrado.")
        return

    # Create 4 verification videos
    # 1 for Single Approval
    # 3 for Mass Approval
    
    source_video = os.path.join(TEST_VIDEOS_SRC, src_files[0])
    
    test_set = [
        "audit_single_01.mp4",
        "audit_mass_01.mp4",
        "audit_mass_02.mp4",
        "audit_mass_03.mp4"
    ]
    
    for fname in test_set:
        dst = os.path.join(PENDING_DIR, fname)
        shutil.copy2(source_video, dst)
        
        # Create metadata json
        meta_json = dst.replace('.mp4', '.json')
        with open(meta_json, 'w') as f:
            f.write(f'{{"profile_id": "p1", "source": "test_audit", "original_name": "{fname}"}}')
            
        print(f"  + Criado: {fname}")

    print("✅ Seed completo.")

if __name__ == "__main__":
    clean_directories()
    populate_pending()
