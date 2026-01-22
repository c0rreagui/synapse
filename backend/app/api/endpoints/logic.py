"""
Smart Logic API Endpoints
=========================

Endpoints REST para o motor de regras inteligente.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.smart_logic import smart_logic


router = APIRouter(tags=["Smart Logic"])


# === Request/Response Models ===

class CheckConflictRequest(BaseModel):
    profile_id: str
    proposed_time: str  # ISO 8601
    exclude_event_id: Optional[str] = None


class SuggestSlotRequest(BaseModel):
    preferred_time: Optional[str] = None  # ISO 8601
    prefer_prime_time: bool = True


class ValidateBatchRequest(BaseModel):
    events: List[Dict[str, Any]]


class ValidationIssueResponse(BaseModel):
    severity: str
    code: str
    message: str
    suggested_fix: Optional[str] = None


class ValidationResultResponse(BaseModel):
    is_valid: bool
    can_proceed: bool
    issues: List[ValidationIssueResponse]
    suggested_time: Optional[str] = None


class OptimalTimeSlotResponse(BaseModel):
    time: str
    score: float
    reasons: List[str]


# === Endpoints ===

@router.get("/rules")
async def get_rules():
    """
    Retorna as regras de negócio configuradas.
    
    Útil para exibir no frontend ou documentação.
    """
    return {
        "success": True,
        "rules": smart_logic.get_rules()
    }


@router.post("/check-conflict", response_model=Dict[str, Any])
async def check_conflict(request: CheckConflictRequest):
    """
    Verifica se um horário proposto tem conflitos.
    
    Retorna:
    - is_valid: True se não há erros
    - can_proceed: True se pode agendar (sem erros bloqueantes)
    - issues: Lista de problemas encontrados
    - suggested_time: Horário alternativo sugerido (se aplicável)
    """
    try:
        proposed_time = datetime.fromisoformat(request.proposed_time)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Formato de data inválido. Use ISO 8601."
        )
    
    result = smart_logic.check_conflict(
        profile_id=request.profile_id,
        proposed_time=proposed_time,
        exclude_event_id=request.exclude_event_id
    )
    
    return {
        "success": True,
        **result.to_dict()
    }


@router.get("/suggest/{profile_id}")
async def suggest_slot(
    profile_id: str,
    preferred_time: Optional[str] = None,
    prefer_prime_time: bool = True
):
    """
    Sugere o melhor slot disponível para um perfil.
    
    Args:
        profile_id: ID do perfil TikTok
        preferred_time: Horário preferido (ISO 8601, opcional)
        prefer_prime_time: Se deve priorizar horários de pico
        
    Returns:
        Slot sugerido com score e razões
    """
    pref_dt = None
    if preferred_time:
        try:
            pref_dt = datetime.fromisoformat(preferred_time)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Formato de data inválido. Use ISO 8601."
            )
    
    slot = smart_logic.suggest_slot(
        profile_id=profile_id,
        preferred_time=pref_dt,
        prefer_prime_time=prefer_prime_time
    )
    
    if slot:
        return {
            "success": True,
            "suggestion": slot.to_dict()
        }
    else:
        return {
            "success": False,
            "message": "Nenhum slot disponível encontrado nos próximos 7 dias"
        }


@router.get("/optimal-times/{profile_id}")
async def get_optimal_times(
    profile_id: str,
    target_date: Optional[str] = None,
    count: int = 5
):
    """
    Retorna os melhores horários disponíveis para um perfil.
    
    Args:
        profile_id: ID do perfil TikTok
        target_date: Data alvo (ISO 8601, opcional - default: hoje)
        count: Quantidade de sugestões (default: 5)
        
    Returns:
        Lista de slots ordenada por score
    """
    target_dt = None
    if target_date:
        try:
            target_dt = datetime.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Formato de data inválido. Use ISO 8601."
            )
    
    # Limitar count para evitar abuse
    count = min(max(1, count), 20)
    
    slots = smart_logic.get_optimal_times(
        profile_id=profile_id,
        target_date=target_dt,
        count=count
    )
    
    return {
        "success": True,
        "profile_id": profile_id,
        "target_date": (target_dt or datetime.now()).strftime("%Y-%m-%d"),
        "count": len(slots),
        "optimal_times": [s.to_dict() for s in slots]
    }


@router.post("/validate-batch")
async def validate_batch(request: ValidateBatchRequest):
    """
    Valida um batch de eventos de agendamento.
    
    Útil para validar uploads em lote antes de agendar.
    
    Args:
        events: Lista de dicts com {profile_id, scheduled_time, id?}
        
    Returns:
        Dict mapeando cada evento para seu ValidationResult
    """
    if not request.events:
        raise HTTPException(
            status_code=400,
            detail="Lista de eventos não pode estar vazia"
        )
    
    if len(request.events) > 100:
        raise HTTPException(
            status_code=400,
            detail="Máximo de 100 eventos por batch"
        )
    
    results = smart_logic.validate_batch(request.events)
    
    # Contar válidos vs inválidos
    valid_count = sum(1 for r in results.values() if r.is_valid)
    invalid_count = len(results) - valid_count
    
    return {
        "success": True,
        "total": len(results),
        "valid": valid_count,
        "invalid": invalid_count,
        "results": {k: v.to_dict() for k, v in results.items()}
    }


@router.get("/health")
async def health_check():
    """Health check do módulo Smart Logic"""
    return {
        "status": "healthy",
        "module": "smart_logic",
        "rules": smart_logic.get_rules()
    }
