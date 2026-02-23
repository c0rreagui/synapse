"""
Auto-Scheduler API Endpoints - SYN-67
"""
import asyncio
import logging
from typing import List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db, SessionLocal
from core.models import VideoQueue
from core import auto_scheduler as svc

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auto-scheduler", tags=["auto-scheduler"])


# ---------- Schemas ----------

class VideoItem(BaseModel):
    path: str
    caption: str = ""
    hashtags: List[str] = []
    privacy_level: str = "public_to_everyone"


class CreateQueueRequest(BaseModel):
    profile_slug: str
    videos: List[VideoItem] = Field(..., min_length=1)
    posts_per_day: int = Field(default=1, ge=1, le=3)
    schedule_hours: List[int] = Field(default=[18], description="Lista de horas exatas do dia (ex: [12, 18])")
    start_hour: int = Field(default=18, ge=0, le=23)  # Mantido para backward-compat
    auto_schedule_first_batch: bool = True  # Agenda os primeiros 10 imediatamente


class ScheduleBatchRequest(BaseModel):
    batch_size: int = Field(default=10, ge=1, le=30)


# ---------- Endpoints ----------

@router.post("/queue")
async def create_queue(
    request: CreateQueueRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Cria fila de videos para auto-agendamento.
    Se auto_schedule_first_batch=True, agenda os primeiros 10 em background.
    """
    videos_data = [v.model_dump() for v in request.videos]
    # schedule_hours: usa o campo novo; fallback para start_hour se vazio
    schedule_hours = request.schedule_hours or [request.start_hour]
    # Garantir que nunca excede posts_per_day em horas por dia
    max_posts: int = int(request.posts_per_day)
    schedule_hours_vals: list[int] = [int(h) for h in schedule_hours]
    schedule_hours = schedule_hours_vals[:max_posts] # type: ignore

    items = svc.create_queue(
        profile_slug=request.profile_slug,
        videos=videos_data,
        posts_per_day=request.posts_per_day,
        schedule_hours=schedule_hours,
        db=db
    )

    response: dict[str, Any] = {
        "success": True,
        "profile_slug": request.profile_slug,
        "total_queued": len(items),
        "posts_per_day": request.posts_per_day,
        "schedule_hours": schedule_hours,
        "message": f"{len(items)} videos adicionados a fila."
    }

    if request.auto_schedule_first_batch and items:
        # Agenda em background para nao bloquear a resposta HTTP
        def _run_batch():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Usa importacao global feita no topo do arquivo
                batch_db = SessionLocal()
                result = loop.run_until_complete(
                    svc.schedule_next_batch(
                        profile_slug=request.profile_slug,
                        batch_size=min(10, len(items)),
                        db=batch_db
                    )
                )
                logger.info(f"[AUTO-SCHEDULER] Batch inicial: {result}")
                batch_db.close()
            finally:
                loop.close()

        background_tasks.add_task(_run_batch)
        response["batch_scheduling"] = "started_in_background"
        response["message"] += f" Agendamento do primeiro lote iniciado."

    return response


@router.get("/queue/{profile_slug}")
def get_queue(profile_slug: str, db: Session = Depends(get_db)):
    """Retorna o estado completo da fila para um perfil."""
    return svc.get_queue_status(profile_slug=profile_slug, db=db)


@router.post("/queue/{profile_slug}/schedule-batch")
async def schedule_batch(
    profile_slug: str,
    request: ScheduleBatchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Agenda o proximo lote de videos da fila.
    Util quando o usuario quer forcar o agendamento de mais um lote.
    """
    # Verificar se ja tem items na fila
    count = db.query(VideoQueue).filter(
        VideoQueue.profile_slug == profile_slug,
        VideoQueue.status == "queued"
    ).count()

    if count == 0:
        raise HTTPException(
            status_code=400,
            detail=f"Nenhum video pendente na fila de {profile_slug}"
        )

    def _run_batch():
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Usa importacao global feita no topo do arquivo
            batch_db = SessionLocal()
            result = loop.run_until_complete(
                svc.schedule_next_batch(
                    profile_slug=profile_slug,
                    batch_size=request.batch_size,
                    db=batch_db
                )
            )
            logger.info(f"[AUTO-SCHEDULER] Lote manual: {result}")
            batch_db.close()
        finally:
            loop.close()

    background_tasks.add_task(_run_batch)

    return {
        "success": True,
        "profile_slug": profile_slug,
        "queued_before": count,
        "batch_size": request.batch_size,
        "message": f"Agendamento de ate {request.batch_size} videos iniciado em background."
    }


@router.get("/queue/{profile_slug}/preview-slots")
def preview_slots(
    profile_slug: str,
    schedule_hours: str = "18",  # Query param: horas separadas por virgula ex: "12,18"
    count: int = 10,
    db: Session = Depends(get_db)
):
    """
    Previsualiza os proximos slots que seriam usados para o perfil.
    schedule_hours: string com horas separadas por virgula (ex: "12,18").
    Util para mostrar ao usuario antes de confirmar a fila.
    """
    try:
        parsed_hours = [int(h.strip()) for h in schedule_hours.split(",") if h.strip()]
        parsed_hours = [h for h in parsed_hours if 0 <= h <= 23]
        if not parsed_hours:
            raise ValueError("Nenhuma hora valida")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"schedule_hours invalido: {e}")

    if count > 30:
        raise HTTPException(status_code=400, detail="Maximo 30 slots para preview")

    slots = svc.calculate_next_slots(
        profile_slug=profile_slug,
        count=count,
        schedule_hours=parsed_hours,
        db=db
    )

    from zoneinfo import ZoneInfo
    sp_tz = ZoneInfo("America/Sao_Paulo")

    return {
        "profile_slug": profile_slug,
        "schedule_hours": parsed_hours,
        "slots": [
            {
                "position": i + 1,
                "datetime": slot.isoformat(),
                "display": slot.strftime("%d/%m/%Y %H:%M")
            }
            for i, slot in enumerate(slots)
        ]
    }


@router.delete("/queue/{profile_slug}")
def cancel_queue(profile_slug: str, db: Session = Depends(get_db)):
    """Cancela todos os itens pendentes da fila (status=queued)."""
    updated = db.query(VideoQueue).filter(
        VideoQueue.profile_slug == profile_slug,
        VideoQueue.status == "queued"
    ).update({"status": "cancelled"})
    db.commit()

    return {
        "success": True,
        "profile_slug": profile_slug,
        "cancelled": updated,
        "message": f"{updated} videos cancelados da fila."
    }
