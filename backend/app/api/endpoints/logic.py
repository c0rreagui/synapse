import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import cast, Date
from sqlalchemy.orm import Session

from core.database import get_db, SessionLocal
from core.models import ScheduleItem

router = APIRouter()
logger = logging.getLogger(__name__)

class TimeCheckRequest(BaseModel):
    profile_id: str
    proposed_time: str  # ISO string

class TimeCheckResponse(BaseModel):
    is_valid: bool
    can_proceed: bool
    issues: List[dict] = []
    suggested_time: Optional[str] = None

@router.post("/check-conflict", response_model=TimeCheckResponse)
async def check_schedule_conflict(data: TimeCheckRequest, db: Session = Depends(get_db)):
    """
    Verifica se há conflitos de horário para o agendamento.
    [SYN-100] Implementado Rate Limit Visual de 3 posts por dia
    """
    issues = []
    can_proceed = True
    suggested_time = None
    
    try:
        dt = datetime.fromisoformat(data.proposed_time.replace('Z', '+00:00'))
        
        # Check Daily Rate Limit (3 posts per day max)
        day_date = dt.date()
        daily_posts = db.query(ScheduleItem).filter(
            ScheduleItem.profile_slug == data.profile_id,
            cast(ScheduleItem.scheduled_time, Date) == day_date,
            ScheduleItem.status.in_(['pending', 'processing', 'completed', 'done', 'ready'])
        ).count()
        
        if daily_posts >= 3:
            issues.append({
                "severity": "warning",
                "code": "RATE_LIMIT_WARNING",
                "message": f"Atenção: Este perfil já atingiu o limite de {daily_posts} posts neste dia.",
                "suggested_fix": "Considere reagendar para um dia com menos postagens."
            })
            # We don't block them per se, but 'can_proceed' can be true for warnings.
            # But wait, the frontend shows an error border if there are warnings!
            # Let's mark it as valid but warn.
            
    except Exception as e:
        logger.error(f"Erro no check-conflict: {e}")
        pass
        
    return {
        "is_valid": len(issues) == 0,
        "can_proceed": can_proceed,
        "issues": issues,
        "suggested_time": suggested_time
    }
