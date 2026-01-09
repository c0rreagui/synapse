
import os
import glob
import time
import json
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "backend", "data")
PROCESSING_DIR = os.path.join(BASE_DIR, "backend", "processing")
PENDING_DIR = os.path.join(DATA_DIR, "pending")
APPROVED_DIR = os.path.join(DATA_DIR, "approved")

def check_orphans(directory, name):
    print(f"\n🔍 Verificando Órfãos em {name} ({directory})...")
    if not os.path.exists(directory):
        print(f"  ⚠️ Diretório não existe: {directory}")
        return

    files = os.listdir(directory)
    mp4s = {f for f in files if f.endswith('.mp4')}
    jsons = {f for f in files if f.endswith('.json')}
    
    # Check MP4 without JSON
    for vid in mp4s:
        meta = vid.replace('.mp4', '.json')
        # Algumas vezes meta é filename.json, as vezes filename.mp4.json?
        # A convenção atual parece ser filename.json (ex: video.mp4 -> video.json)
        # Mas vamos checar ambas
        if vid.replace('.mp4', '.json') not in jsons and f"{vid}.json" not in jsons:
             print(f"  🔴 [CRÍTICO] Vídeo sem Metadata (Órfão): {vid}")

    # Check JSON without MP4
    for meta in jsons:
        # Se for video.json
        vid_candidates = [meta.replace('.json', '.mp4'), meta.replace('.mp4.json', '.mp4')]
        found = any(v in mp4s for v in vid_candidates)
        
        if not found:
             # Pode ser metadata solto?
             print(f"  🟡 [ALERTA] Metadata sem Vídeo: {meta}")

def check_stuck_processing():
    print(f"\n🔍 Verificando Processos Travados em {PROCESSING_DIR}...")
    if not os.path.exists(PROCESSING_DIR):
        print("  ✅ Diretório processing limpo (não existe).")
        return

    files = os.listdir(PROCESSING_DIR)
    if not files:
        print("  ✅ Nenhum arquivo em processamento.")
        return

    now = time.time()
    for f in files:
        full_path = os.path.join(PROCESSING_DIR, f)
        mtime = os.path.getmtime(full_path)
        age_seconds = now - mtime
        age_str = str(timedelta(seconds=int(age_seconds)))
        
        if age_seconds > 3600: # 1 hora
            print(f"  🔴 [CRÍTICO] Arquivo travado há {age_str}: {f}")
        elif age_seconds > 300: # 5 min
            print(f"  🟡 [ALERTA] Arquivo processando há {age_str}: {f}")
        else:
            print(f"  🟢 [OK] Processando há {age_str}: {f}")

if __name__ == "__main__":
    print("🛡️ AUDITORIA DE INTEGRIDADE DE DADOS")
    check_orphans(PENDING_DIR, "PENDING")
    check_orphans(APPROVED_DIR, "APPROVED")
    check_stuck_processing()
