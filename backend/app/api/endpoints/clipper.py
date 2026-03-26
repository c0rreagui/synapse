import os

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import List, Optional
from datetime import datetime

from core.database import get_db, safe_session
from sqlalchemy.orm import Session
from core.clipper.models import TwitchTarget, ClipJob, JobStatus
from core.models import PendingApproval
from core.clipper.monitor import register_target, check_target
from core.limiter import limiter
from core.logger import logger

# Se for rodar a verificação sincronicamente na route, se n engatilha no redis
# A arq pool pode ser injetada dps

router = APIRouter()

class TargetCreate(BaseModel):
    channel_url: str
    army_id: Optional[int] = None
    auto_approve: bool = False

class TargetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    channel_url: str
    channel_name: str
    target_type: str
    category_id: Optional[str] = None
    broadcaster_id: Optional[str] = None
    profile_image_url: Optional[str] = None
    offline_image_url: Optional[str] = None
    active: bool
    status: Optional[str] = None
    army_id: Optional[int] = None
    last_checked_at: Optional[datetime] = None
    last_clip_found_at: Optional[datetime] = None
    total_clips_processed: int = 0
    consecutive_empty_checks: int = 0
    min_clip_views: int = 10
    max_clips_per_check: int = 100
    check_interval_minutes: int = 15
    auto_approve: bool = False
    layout_mode: str = "auto"

class ClipMetadataPydantic(BaseModel):
    title: Optional[str] = None
    views: Optional[int] = None
    duration: Optional[float] = None
    creator: Optional[str] = None
    game: Optional[str] = None

class ClipJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    target_id: int
    status: JobStatus
    current_step: Optional[str] = None
    progress_pct: int
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    channel_name: Optional[str] = None
    clip_metadata: Optional[List[ClipMetadataPydantic]] = None
    priority: int = 0



# /jobs route definida no final do arquivo (L240+)

@router.post("/targets", response_model=TargetResponse)
@limiter.limit("5/minute")
async def create_twitch_target(request: Request, target: TargetCreate):
    """
    Cadastra uma nova URL da Twitch para iniciar monitoramento contínuo.
    O backend descobre e guarda o broadcaster_id da Twitch usando OAuth2.
    """
    try:
        res = await register_target(target.channel_url, army_id=target.army_id)
        # TODO: Refetch to get complete telemetry if needed, but for now defaults are fine.
        return TargetResponse(
            id=res["id"],
            channel_url=target.channel_url,
            channel_name=res["channel_name"],
            target_type=res.get("target_type", "channel"),
            army_id=res.get("army_id", target.army_id),
            category_id=res.get("category_id"),
            broadcaster_id=res.get("broadcaster_id"),
            profile_image_url=res.get("profile_image_url"),
            offline_image_url=res.get("offline_image_url"),
            active=True,
            status=res.get("status"),
            min_clip_views=res.get("min_clip_views", 10),
            max_clips_per_check=res.get("max_clips_per_check", 100),
            check_interval_minutes=15,
            auto_approve=target.auto_approve,
            layout_mode="auto",
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/targets", response_model=List[TargetResponse])
def list_twitch_targets(db: Session = Depends(get_db)):
    """
    Lista todos os canais sendo monitorados.
    """
    return db.query(TwitchTarget).order_by(TwitchTarget.id.desc()).all()


@router.post("/targets/{target_id}/check")
@limiter.limit("10/minute")
async def force_check_target(request: Request, target_id: int, background_tasks: BackgroundTasks):
    """
    Força a checagem imediata de clipes para um canal (para debug ou requisição on-demand).
    Roda em background para não causar timeout (targets de categoria podem demorar 30s+).
    """
    with safe_session() as db:
        target = db.query(TwitchTarget).filter(TwitchTarget.id == target_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Target não encontrado")
        if not target.active:
            raise HTTPException(status_code=400, detail="Target está desativado")

    async def _run_check():
        try:
            await check_target(target_id)
        except Exception as e:
            logger.error(f"Erro no scan manual do target #{target_id}: {e}")

    background_tasks.add_task(_run_check)
    return {"message": "Varredura manual iniciada em background. Resultados aparecerão em breve."}


class TargetUpdate(BaseModel):
    active: Optional[bool] = None
    min_clip_views: Optional[int] = None
    max_clips_per_check: Optional[int] = None
    check_interval_minutes: Optional[int] = None
    army_id: Optional[int] = None
    target_type: Optional[str] = None
    auto_approve: Optional[bool] = None
    layout_mode: Optional[str] = None

@router.patch("/targets/{target_id}", response_model=TargetResponse)
async def update_twitch_target(target_id: int, target_update: TargetUpdate, db: Session = Depends(get_db)):
    """
    Atualiza dados de um canal (ex: ativar/desativar ou mudar critérios).
    """
    try:
        target = db.query(TwitchTarget).filter(TwitchTarget.id == target_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Target nao encontrada")
        
        if target_update.active is not None:
            target.active = target_update.active
        if target_update.min_clip_views is not None:
            target.min_clip_views = target_update.min_clip_views
        if target_update.max_clips_per_check is not None:
            target.max_clips_per_check = target_update.max_clips_per_check
        if target_update.check_interval_minutes is not None:
            target.check_interval_minutes = target_update.check_interval_minutes
        if target_update.army_id is not None: # Changed from profile_id to army_id
            target.army_id = target_update.army_id # Changed from profile_id to army_id
        if target_update.target_type is not None:
            target.target_type = target_update.target_type
        if target_update.auto_approve is not None:
            target.auto_approve = target_update.auto_approve
        if target_update.layout_mode is not None:
            target.layout_mode = target_update.layout_mode

        db.commit()
        db.refresh(target)
        return TargetResponse(
            id=target.id,
            channel_url=target.channel_url,
            channel_name=target.channel_name,
            target_type=target.target_type,
            category_id=target.category_id,
            broadcaster_id=target.broadcaster_id,
            profile_image_url=target.profile_image_url,
            offline_image_url=target.offline_image_url,
            active=target.active,
            army_id=target.army_id,
            last_checked_at=target.last_checked_at,
            last_clip_found_at=target.last_clip_found_at,
            total_clips_processed=target.total_clips_processed,
            consecutive_empty_checks=target.consecutive_empty_checks,
            min_clip_views=target.min_clip_views,
            max_clips_per_check=target.max_clips_per_check,
            check_interval_minutes=target.check_interval_minutes,
            auto_approve=target.auto_approve,
            layout_mode=getattr(target, 'layout_mode', 'auto') or 'auto',
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/targets/{target_id}")
async def delete_twitch_target(target_id: int, db: Session = Depends(get_db)):
    """
    Remove um canal do monitoramento.
    Remove os clip_jobs e pending_approvals associados antes de deletar fisicamente.
    """
    try:
        target = db.query(TwitchTarget).filter(TwitchTarget.id == target_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Target nao encontrada")
        
        # Limpar jobs pendentes / orfãos (cascade manual)
        jobs = db.query(ClipJob).filter(ClipJob.target_id == target_id).all()
        job_ids = [j.id for j in jobs]
        
        # H07: Deletar fisicamente os arquivos de midia alocados aos jobs para nao vazar storage
        import os
        for job in jobs:
            try:
                if job.output_path and os.path.exists(job.output_path):
                    os.remove(job.output_path)
                if job.clip_local_paths:
                    for lp in job.clip_local_paths:
                        if lp and os.path.exists(lp):
                            os.remove(lp)
            except Exception as e:
                logger.warning(f"Erro ao tentar remover arquivo fisico do job {job.id}: {e}")

        if job_ids:
            # Free pending approvals
            db.query(PendingApproval).filter(PendingApproval.clip_job_id.in_(job_ids)).delete(synchronize_session=False)
            db.query(ClipJob).filter(ClipJob.target_id == target_id).delete(synchronize_session=False)
        
        db.delete(target)
        db.commit()
        
        return {"message": f"Target {target_id} e seus jobs excluidos com sucesso."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pipeline", response_model=List[ClipJobResponse])
def list_clip_jobs(db: Session = Depends(get_db)):
    """
    Lista status dos ultimos 50 Jobs do pipeline de edição.
    Inclui channel_name via join com TwitchTarget para exibição na Esteira.
    """
    rows = (
        db.query(ClipJob, TwitchTarget.channel_name)
        .outerjoin(TwitchTarget, ClipJob.target_id == TwitchTarget.id)
        .order_by(ClipJob.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        ClipJobResponse(
            id=job.id,
            target_id=job.target_id,
            status=job.status,
            current_step=job.current_step,
            progress_pct=job.progress_pct,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            channel_name=channel_name,
            priority=getattr(job, 'priority', 0) or 0,
        )
        for job, channel_name in rows
    ]


# ─── POST /jobs/{id}/prioritize — Priorizar um job ────────────────────────

@router.post("/jobs/{job_id}/prioritize")
async def prioritize_job(job_id: int, db: Session = Depends(get_db)):
    """
    Marca um job como alta prioridade. O worker vai processa-lo antes dos demais.
    Re-enfileira no Redis para garantir que seja processado rapidamente.
    """
    job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job nao encontrado")
    if job.status != "pending":
        raise HTTPException(status_code=400, detail=f"Apenas jobs pendentes podem ser priorizados (status atual: {job.status})")

    job.priority = 1
    db.commit()

    # Re-enfileirar no Redis para processamento imediato
    from core.config import REDIS_HOST, REDIS_PORT
    from arq.connections import RedisSettings, create_pool
    try:
        pool = await create_pool(RedisSettings(host=REDIS_HOST, port=REDIS_PORT))
        await pool.enqueue_job("process_clip_job", job_id, _queue_name="clipper:queue")
        await pool.close()
    except Exception as e:
        logger.warning(f"Falha ao re-enfileirar job #{job_id}: {e}")

    return {"message": f"Job #{job_id} priorizado", "priority": 1}


# ─── POST /jobs/{id}/cancel — Cancelar um job ─────────────────────────────

@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: int, db: Session = Depends(get_db)):
    """Cancela e remove um job da fila. Aceita qualquer status exceto completed."""
    job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job nao encontrado")

    # Limpar arquivos de clips associados
    import glob as _glob
    clips_dir = "/app/data/clipper/clips"
    pattern = os.path.join(clips_dir, f"job{job_id}_clip*")
    for cf in _glob.glob(pattern):
        try:
            os.remove(cf)
        except OSError:
            pass

    # Limpar output se existir
    if job.output_path and os.path.exists(job.output_path):
        try:
            os.remove(job.output_path)
        except OSError:
            pass

    # Limpar referências em pending_approvals (FK constraint)
    db.query(PendingApproval).filter(PendingApproval.clip_job_id == job.id).delete()

    db.delete(job)
    db.commit()
    return {"message": f"Job #{job_id} removido"}


# ─── POST /jobs/cancel-bulk — Cancelar jobs em massa ──────────────────────

class BulkCancelRequest(BaseModel):
    job_ids: List[int]

@router.post("/jobs/cancel-bulk")
def cancel_jobs_bulk(req: BulkCancelRequest, db: Session = Depends(get_db)):
    """Cancela e remove multiplos jobs de uma vez."""
    jobs = db.query(ClipJob).filter(
        ClipJob.id.in_(req.job_ids),
    ).all()

    import glob as _glob
    clips_dir = "/app/data/clipper/clips"
    cancelled = []
    for job in jobs:
        # Limpar clips
        for cf in _glob.glob(os.path.join(clips_dir, f"job{job.id}_clip*")):
            try:
                os.remove(cf)
            except OSError:
                pass
        # Limpar referências em pending_approvals (FK constraint)
        db.query(PendingApproval).filter(PendingApproval.clip_job_id == job.id).delete()
        cancelled.append(job.id)
        db.delete(job)

    db.commit()
    return {"cancelled": cancelled, "count": len(cancelled)}


@router.post("/jobs/cancel-all")
def cancel_all_jobs(db: Session = Depends(get_db)):
    """Remove todos os jobs não-completados da fila (pending, waiting_clips, downloading, etc)."""
    jobs = db.query(ClipJob).filter(
        ClipJob.status.notin_(["completed"])
    ).all()

    import glob as _glob
    clips_dir = "/app/data/clipper/clips"
    count = 0
    for job in jobs:
        for cf in _glob.glob(os.path.join(clips_dir, f"job{job.id}_clip*")):
            try:
                os.remove(cf)
            except OSError:
                pass
        if job.output_path and os.path.exists(job.output_path):
            try:
                os.remove(job.output_path)
            except OSError:
                pass
        # Limpar referências em pending_approvals (FK constraint)
        db.query(PendingApproval).filter(PendingApproval.clip_job_id == job.id).delete()
        db.delete(job)
        count += 1

    db.commit()
    return {"message": f"{count} jobs removidos da fila", "count": count}
