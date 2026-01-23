from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class TimeCheckRequest(BaseModel):
    profile_id: str
    proposed_time: str  # ISO string

class TimeCheckResponse(BaseModel):
    is_valid: bool
    can_proceed: bool
    issues: List[dict] = []
    suggested_time: Optional[str] = None

@router.post("/check-conflict", response_model=TimeCheckResponse)
async def check_schedule_conflict(data: TimeCheckRequest):
    """
    Verifica se há conflitos de horário para o agendamento.
    Por enquanto, retorna sempre válido para desbloquear o frontend.
    """
    # TODO: Implementar verificação real contra o banco de dados/agendador
    return {
        "is_valid": True,
        "can_proceed": True,
        "issues": [],
        "suggested_time": None
    }
