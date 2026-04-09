import asyncio
import sys
import os

# Adiciona backend ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from app.api.endpoints.factory import _resolve_profiles_for_approval
from core.models import PendingApproval, Profile
from core.auto_scheduler import create_queue, schedule_next_batch

def test_approval():
    db = SessionLocal()
    # Pega o ultimo PendingApproval aprovado (com video) para testar
    item = db.query(PendingApproval).filter(PendingApproval.status == 'approved').order_by(PendingApproval.id.desc()).first()
    if not item:
        print("Nenhum item found")
        return
    
    print(f"Testando com o item: {item.id} -> video: {item.video_path}")
    profiles = _resolve_profiles_for_approval(item, db, profile_slug="dosealtatv")
    print(f"Perfis detectados: {[p.slug for p in profiles]}")
    
    schedule_hours = [10, 15, 18]
    for p in profiles:
        print(f"--- Processando perfil {p.slug} ---")
        try:
            queue_items = create_queue(
                profile_slug=p.slug,
                videos=[{
                    "path": item.video_path,
                    "caption": "test caption",
                    "hashtags": "test",
                    "privacy_level": "public_to_everyone",
                }],
                posts_per_day=len(schedule_hours),
                schedule_hours=schedule_hours,
                db=db,
            )
            print(f"create_queue retornou {len(queue_items)} itens (id: {[q.id for q in queue_items]})")
            
            result = asyncio.run(schedule_next_batch(
                profile_slug=p.slug,
                batch_size=1,
                db=db,
            ))
            print(f"schedule_next_batch retornou: {result}")
        except Exception as e:
            print(f"Erro no perfil {p.slug}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_approval()
