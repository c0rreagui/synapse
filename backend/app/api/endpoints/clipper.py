from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime

from core.database import get_db, safe_session
from sqlalchemy.orm import Session
from core.clipper.models import TwitchTarget, ClipJob
from core.clipper.monitor import register_target, check_target

# Se for rodar a verificação sincronicamente na route, se n engatilha no redis
# A arq pool pode ser injetada dps

router = APIRouter()

class TargetCreate(BaseModel):
    channel_url: str
    army_id: Optional[int] = None

class TargetResponse(BaseModel):
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
    min_clip_views: int = 100
    max_clips_per_check: int = 5
    check_interval_minutes: int = 15

class ClipJobResponse(BaseModel):
    id: int
    target_id: int
    status: str
    current_step: str
    progress_pct: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


@router.get("/jobs", response_model=List[ClipJobResponse])
def list_clip_jobs(db: Session = Depends(get_db)):
    """
    Lista o status dos jobs de cortes recentes para acompanhamento da esteira.
    """
    jobs = db.query(ClipJob).order_by(ClipJob.id.desc()).limit(20).all()
    out = []
    for j in jobs:
        out.append(ClipJobResponse(
            id=j.id,
            target_id=j.target_id,
            status=j.status,
            current_step=j.current_step or "",
            progress_pct=j.progress_pct,
            error_message=j.error_message,
            created_at=j.created_at,
            updated_at=j.updated_at
        ))
    return out

@router.post("/targets", response_model=TargetResponse)
async def create_twitch_target(target: TargetCreate):
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
            broadcaster_id=res.get("broadcaster_id"),
            profile_image_url=res.get("profile_image_url"),
            offline_image_url=res.get("offline_image_url"),
            active=True,
            status=res.get("status"),
            min_clip_views=100,
            max_clips_per_check=5,
            check_interval_minutes=15
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
    targets = db.query(TwitchTarget).order_by(TwitchTarget.id.desc()).all()
    out = []
    for t in targets:
        out.append(TargetResponse(
            id=t.id,
            channel_url=t.channel_url,
            channel_name=t.channel_name,
            broadcaster_id=t.broadcaster_id,
            profile_image_url=t.profile_image_url,
            offline_image_url=t.offline_image_url,
            active=t.active,
            last_checked_at=t.last_checked_at,
            last_clip_found_at=t.last_clip_found_at,
            total_clips_processed=t.total_clips_processed,
            consecutive_empty_checks=t.consecutive_empty_checks,
            min_clip_views=t.min_clip_views,
            max_clips_per_check=t.max_clips_per_check,
            check_interval_minutes=t.check_interval_minutes
        ))
    return out


@router.post("/targets/{target_id}/check")
async def force_check_target(target_id: int, background_tasks: BackgroundTasks):
    """
    Força a checagem imediata de clipes para um canal (para debug ou requisição on-demand).
    Aqui ele busca o clip e já enfilera se achar.
    """
    try:
        idx = await check_target(target_id)
        if idx:
            # O proximo passo ideal seria: await redis.enqueue_job("process_clip_job", idx, _queue_name="clipper:queue")
            # Mas como ja e validado, sera capturado pelo cron do monitor nativamente tambem.
            return {"message": "Checagem concluída. Clipes encontrados e job de processamento enfileirado", "job_id": idx}
        else:
            return {"message": "Checagem concluída. Nenhum novo clip foi encontrado que bata com os requisitos."}
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))


class TargetUpdate(BaseModel):
    active: Optional[bool] = None
    min_clip_views: Optional[int] = None
    max_clips_per_check: Optional[int] = None
    check_interval_minutes: Optional[int] = None
    army_id: Optional[int] = None
    target_type: Optional[str] = None

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
            status=target.status,
            profile_id=target.profile_id,
            last_checked_at=target.last_checked_at,
            last_clip_found_at=target.last_clip_found_at,
            total_clips_processed=target.total_clips_processed,
            consecutive_empty_checks=target.consecutive_empty_checks,
            min_clip_views=target.min_clip_views,
            max_clips_per_check=target.max_clips_per_check,
            check_interval_minutes=target.check_interval_minutes
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


from core.models import PendingApproval

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

@router.get("/jobs", response_model=List[ClipJobResponse])
def list_clip_jobs(db: Session = Depends(get_db)):
    """
    Lista status dos ultimos 50 Jobs do pipeline de edição.
    """
    jobs = db.query(ClipJob).order_by(ClipJob.created_at.desc()).limit(50).all()
    out = []
    for j in jobs:
        out.append(ClipJobResponse(
            id=j.id,
            target_id=j.target_id,
            status=j.status,
            current_step=j.current_step,
            progress_pct=j.progress_pct,
            error_message=j.error_message,
            created_at=j.created_at,
            updated_at=j.updated_at
        ))
    return out
