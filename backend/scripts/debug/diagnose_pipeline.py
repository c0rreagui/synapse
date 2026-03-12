"""
Diagnóstico rápido: verifica se TwitchTarget.auto_approve é acessível
e lista jobs failed de hoje que podem ser reprocessados.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime, timezone, timedelta
from core.database import safe_session
from core.clipper.models import TwitchTarget, ClipJob

def diagnose():
    with safe_session() as db:
        # 1. Testar acesso ao auto_approve
        targets = db.query(TwitchTarget).all()
        print(f"\n[DIAG] {len(targets)} TwitchTarget(s) encontrado(s):")
        for t in targets:
            try:
                val = t.auto_approve
                print(f"  - #{t.id} {t.channel_name}: auto_approve = {val} ✅")
            except AttributeError as e:
                print(f"  - #{t.id} {t.channel_name}: ERRO -> {e} ❌")

        # 2. Listar jobs failed de hoje
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        failed_jobs = db.query(ClipJob).filter(
            ClipJob.status == "failed",
            ClipJob.created_at >= today_start
        ).all()

        print(f"\n[DIAG] {len(failed_jobs)} ClipJob(s) falhados hoje:")
        for j in failed_jobs:
            print(f"  - Job #{j.id} | target_id={j.target_id} | step='{j.current_step}' | error='{j.error_message[:100] if j.error_message else 'N/A'}'")

        # 3. Listar jobs que poderiam estar presos (downloading/transcribing/editing/stitching)
        stuck_jobs = db.query(ClipJob).filter(
            ClipJob.status.in_(["downloading", "transcribing", "editing", "stitching"]),
        ).all()

        print(f"\n[DIAG] {len(stuck_jobs)} ClipJob(s) potencialmente presos:")
        for j in stuck_jobs:
            print(f"  - Job #{j.id} | status={j.status} | step='{j.current_step}' | created={j.created_at}")

if __name__ == "__main__":
    diagnose()
