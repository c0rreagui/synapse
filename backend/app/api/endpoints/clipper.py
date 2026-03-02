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

class TargetResponse(BaseModel):
    id: int
    channel_url: str
    channel_name: str
    broadcaster_id: Optional[str] = None
    active: bool
    status: Optional[str] = None

class ClipJobResponse(BaseModel):
    id: int
    target_id: int
    status: str
    current_step: str
    progress_pct: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


@router.post("/targets", response_model=TargetResponse)
async def create_twitch_target(target: TargetCreate):
    """
    Cadastra uma nova URL da Twitch para iniciar monitoramento contínuo.
    O backend descobre e guarda o broadcaster_id da Twitch usando OAuth2.
    """
    try:
        res = await register_target(target.channel_url)
        return TargetResponse(
            id=res["id"],
            channel_url=target.channel_url,
            channel_name=res["channel_name"],
            broadcaster_id=res["broadcaster_id"],
            active=True,
            status=res["status"]
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
            active=t.active
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


@router.delete("/targets/{target_id}")
async def delete_twitch_target(target_id: int, db: Session = Depends(get_db)):
    """
    Remove um canal do monitoramento.
    Remove os clip_jobs associados ou apenas a target?
    A rigor, uma soft delete ou delete caseata. Aqui fazemos delete físico na target se quisermos limpar.
    Mas o ideal é excluir os jobs primeiro pela foreign key constraint, ou o SQLAlchemy resolve se tiver cascade.
    """
    try:
        target = db.query(TwitchTarget).filter(TwitchTarget.id == target_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Target nao encontrada")
        
        # Limpar jobs pendentes / orfãos (cascade manual simples)
        db.query(ClipJob).filter(ClipJob.target_id == target_id).delete()
        
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
