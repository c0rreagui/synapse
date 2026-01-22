"""
Batch Manager API Endpoints
============================

Endpoints REST para gerenciamento de uploads em lote.
Expõe as funcionalidades do batch_manager.py core module.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.batch_manager import batch_manager


router = APIRouter(tags=["Batch Manager"])


# === Request/Response Models ===

class CreateBatchRequest(BaseModel):
    """Request para criar um novo batch"""
    files: List[str] = Field(..., description="Lista de caminhos de vídeo")
    profile_ids: List[str] = Field(..., description="Lista de profile_ids")
    start_time: str = Field(..., description="Horário de início (ISO 8601)")
    interval_minutes: int = Field(60, ge=15, le=480, description="Intervalo entre posts em minutos")
    viral_music_enabled: bool = Field(False, description="Ativar música viral")
    sound_id: Optional[str] = Field(None, description="ID da música viral")
    sound_title: Optional[str] = Field(None, description="Título da música")


class ExecuteBatchRequest(BaseModel):
    """Request para executar um batch"""
    force: bool = Field(False, description="Se True, ignora eventos inválidos")


# === Endpoints ===

@router.get("/list")
async def list_batches(limit: int = 20):
    """
    Lista batches recentes.
    
    Args:
        limit: Máximo de batches a retornar (default: 20)
    """
    limit = min(max(1, limit), 100)
    batches = batch_manager.list_batches(limit=limit)
    
    return {
        "success": True,
        "count": len(batches),
        "batches": batches
    }


@router.post("/create")
async def create_batch(request: CreateBatchRequest):
    """
    Cria um novo batch de agendamentos.
    
    O batch é criado mas NÃO executado. Use /validate para validar
    e /execute para agendar os eventos.
    """
    try:
        start_dt = datetime.fromisoformat(request.start_time)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Formato de data inválido. Use ISO 8601."
        )
    
    if not request.files:
        raise HTTPException(
            status_code=400,
            detail="Lista de arquivos não pode estar vazia"
        )
    
    if not request.profile_ids:
        raise HTTPException(
            status_code=400,
            detail="Lista de profile_ids não pode estar vazia"
        )
    
    batch_id = batch_manager.create_batch(
        files=request.files,
        profiles=request.profile_ids,
        start_time=start_dt,
        interval_minutes=request.interval_minutes,
        viral_music_enabled=request.viral_music_enabled,
        sound_id=request.sound_id,
        sound_title=request.sound_title
    )
    
    # Retornar batch criado com status
    result = batch_manager.get_batch_status(batch_id)
    
    return {
        "success": True,
        "batch_id": batch_id,
        "message": f"Batch criado com {len(request.files) * len(request.profile_ids)} eventos",
        "batch": result
    }


@router.post("/{batch_id}/validate")
async def validate_batch(batch_id: str):
    """
    Valida todos os eventos do batch com Smart Logic.
    
    Retorna contagem de eventos válidos, inválidos e com warnings.
    """
    try:
        result = batch_manager.validate_batch(batch_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return {
        "success": True,
        **result.to_dict()
    }


@router.post("/{batch_id}/execute")
async def execute_batch(batch_id: str, request: ExecuteBatchRequest):
    """
    Executa o batch, agendando todos os eventos.
    
    Args:
        batch_id: ID do batch
        force: Se True, ignora eventos inválidos e agenda os válidos
    """
    try:
        result = batch_manager.execute_batch(batch_id, force=request.force)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "success": True,
        **result.to_dict()
    }


@router.get("/{batch_id}")
async def get_batch_status(batch_id: str):
    """
    Retorna status atual do batch.
    """
    result = batch_manager.get_batch_status(batch_id)
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Batch {batch_id} não encontrado"
        )
    
    return {
        "success": True,
        "batch": result
    }


@router.delete("/{batch_id}")
async def cancel_batch(batch_id: str):
    """
    Cancela um batch em andamento.
    
    Apenas batches que ainda não foram executados podem ser cancelados.
    """
    try:
        success = batch_manager.cancel_batch(batch_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Batch já foi executado ou cancelado"
        )
    
    return {
        "success": True,
        "message": f"Batch {batch_id} cancelado"
    }


@router.get("/health")
async def health_check():
    """Health check do módulo Batch Manager"""
    return {
        "status": "healthy",
        "module": "batch_manager",
        "active_batches": len(batch_manager._batches) if hasattr(batch_manager, '_batches') else 0
    }
