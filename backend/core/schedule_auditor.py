"""
Schedule Auditor - Detecta mismatches de profile_slug vs video_path
"""
import re
from sqlalchemy import create_engine, text
from core.database import SessionLocal
from core.models import ScheduleItem
import logging

logger = logging.getLogger(__name__)

def audit_schedule_items() -> dict:
    """
    Audita todos os items pendentes para detectar mismatches.
    Retorna estatísticas sobre problemas encontrados.
    """
    db = SessionLocal()
    try:
        items = db.query(ScheduleItem).filter(
            ScheduleItem.status.in_(['pending', 'pending_approval', 'pending_analysis_oracle'])
        ).all()
        
        mismatches = []
        for item in items:
            # Extrair profile do video_path
            match = re.search(r'(tiktok_profile_\d+)', item.video_path)
            path_profile = match.group(1) if match else None
            
            if path_profile and path_profile != item.profile_slug:
                mismatches.append({
                    'id': item.id,
                    'expected': item.profile_slug,
                    'found': path_profile,
                    'video_path': item.video_path
                })
                logger.error(
                    f"MISMATCH DETECTED: Item {item.id} "
                    f"profile_slug={item.profile_slug} but "
                    f"video_path={item.video_path} contains {path_profile}"
                )
        
        return {
            'total_checked': len(items),
            'mismatches_found': len(mismatches),
            'details': mismatches
        }
    finally:
        db.close()
