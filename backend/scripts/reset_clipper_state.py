import sys
import os

# Adiciona o diretório raiz do backend ao sys.path para importações absolutas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from script_env import setup_script_env
setup_script_env()

from core.database import SessionLocal
from core.models import Army  # Carrega para evitar erro de FK
from core.clipper.models import ClipJob, TwitchTarget
import shutil

def reset_clipper_state():
    db = SessionLocal()
    try:
        # 1. Deletar todos os ClipJobs
        deleted_jobs = db.query(ClipJob).delete()
        print(f"Deletados {deleted_jobs} ClipJobs.")

        # 2. Resetar os TwitchTargets
        targets = db.query(TwitchTarget).all()
        for t in targets:
            t.last_checked_at = None
            t.last_clip_found_at = None
            t.total_clips_processed = 0
            t.consecutive_empty_checks = 0
        print(f"Resetados {len(targets)} TwitchTargets.")
        
        db.commit()
        print("Estado do banco de dados resetado com sucesso.")
        
        # 3. Limpar workspace do clipper (opcional, fallback)
        workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/clipper_workspace'))
        if os.path.exists(workspace_dir):
            for filename in os.listdir(workspace_dir):
                filepath = os.path.join(workspace_dir, filename)
                try:
                    if os.path.isfile(filepath) or os.path.islink(filepath):
                        os.unlink(filepath)
                    elif os.path.isdir(filepath):
                        shutil.rmtree(filepath)
                except Exception as e:
                    print(f"Falha ao deletar {filepath}. Reason: {e}")
            print(f"Workspace {workspace_dir} limpo.")
            
    except Exception as e:
        db.rollback()
        print(f"Erro ao resetar estado: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_clipper_state()
