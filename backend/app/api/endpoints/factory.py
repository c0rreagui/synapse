"""
Factory Endpoints - Curation Pipeline (SYN-86)
===============================================

Endpoints para a Vitrine de Curadoria Tinder-Style.
Consome a tabela `pending_approvals` e orquestra:
  - Listagem de vídeos pendentes
  - Aprovação (injeta no scheduler via batch_manager/smart_logic)
  - Rejeição (remove do DB + garbage collection do arquivo)
  - Inversão (FFmpeg vstack reverso: gameplay no topo, facecam embaixo)
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import PendingApproval

logger = logging.getLogger("FactoryAPI")

router = APIRouter()


# ─── Response Models ────────────────────────────────────────────────────

class PendingItemResponse(BaseModel):
    id: int
    clip_job_id: Optional[int] = None
    video_path: str
    thumbnail_path: Optional[str] = None
    streamer_name: Optional[str] = None
    title: Optional[str] = None
    duration_seconds: Optional[int] = None
    file_size_bytes: Optional[int] = None
    status: str
    created_at: datetime


# ─── GET /pending ────────────────────────────────────────────────────────

@router.get("/pending", response_model=List[PendingItemResponse])
def list_pending(db: Session = Depends(get_db)):
    """
    Lista todos os vídeos pendentes de curadoria.
    Ordenados do mais recente para o mais antigo.
    """
    items = (
        db.query(PendingApproval)
        .filter(PendingApproval.status == "pending")
        .order_by(PendingApproval.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        PendingItemResponse(
            id=item.id,
            clip_job_id=item.clip_job_id,
            video_path=item.video_path,
            thumbnail_path=item.thumbnail_path,
            streamer_name=item.streamer_name,
            title=item.title,
            duration_seconds=item.duration_seconds,
            file_size_bytes=item.file_size_bytes,
            status=item.status,
            created_at=item.created_at,
        )
        for item in items
    ]


# ─── POST /approve/{id} — SYN-78: Smart Queue Pipeline ──────────────────

@router.post("/approve/{item_id}")
async def approve_item(item_id: int, db: Session = Depends(get_db)):
    """
    Aprova um vídeo pendente e o injeta na Smart Queue.
    Usa auto_scheduler.create_queue() + schedule_next_batch() para
    distribuir inteligentemente ao longo dos dias, respeitando:
    - SmartLogic: intervalo mínimo 2h, max 3 posts/dia
    - calculate_next_slots: distribui nos schedule_hours configurados
    """
    item = db.query(PendingApproval).filter(PendingApproval.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    if item.status != "pending":
        raise HTTPException(status_code=400, detail=f"Item já processado: {item.status}")

    # Verificar arquivo existe
    if not os.path.exists(item.video_path):
        raise HTTPException(status_code=400, detail=f"Arquivo não encontrado: {item.video_path}")

    try:
        from core.auto_scheduler import create_queue, schedule_next_batch
        from core.models import Profile

        # Pegar o primeiro perfil ativo para agendamento automático
        profile = db.query(Profile).filter(Profile.active == True).first()
        if not profile:
            raise HTTPException(status_code=400, detail="Nenhum perfil ativo encontrado para agendamento")

        # Horários padrão de publicação (12h e 18h se não configurado)
        schedule_hours = [12, 18]

        # 1. Inserir na Smart Queue
        queue_items = create_queue(
            profile_slug=profile.slug,
            videos=[{
                "path": item.video_path,
                "caption": item.title or "",
                "hashtags": [],
                "privacy_level": "public_to_everyone",
            }],
            posts_per_day=2,
            schedule_hours=schedule_hours,
            db=db,
        )

        # 2. Agendar imediatamente via pipeline inteligente
        result = await schedule_next_batch(
            profile_slug=profile.slug,
            batch_size=1,
            db=db,
        )

        # 3. Marcar como aprovado
        item.status = "approved"
        db.commit()

        scheduled_time = None
        if queue_items and hasattr(queue_items[0], 'scheduled_at') and queue_items[0].scheduled_at:
            scheduled_time = queue_items[0].scheduled_at.isoformat()

        logger.info(f"✅ Item #{item_id} aprovado via Smart Queue → perfil @{profile.slug} | resultado: {result}")

        return {
            "message": "Vídeo aprovado e inserido na Smart Queue",
            "profile": profile.slug,
            "scheduled_time": scheduled_time,
            "queue_result": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao aprovar item #{item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /queue-status — SYN-78: Status da Smart Queue ──────────────────

@router.get("/queue-status")
def get_queue_status(db: Session = Depends(get_db)):
    """
    Retorna o status da Smart Queue para o frontend (widget de contadores).
    """
    from core.models import VideoQueue, Profile

    profile = db.query(Profile).filter(Profile.active == True).first()
    if not profile:
        return {"queued": 0, "scheduled": 0, "failed": 0, "total_pending": 0}

    queued = db.query(VideoQueue).filter(
        VideoQueue.profile_slug == profile.slug,
        VideoQueue.status == "queued"
    ).count()

    scheduled = db.query(VideoQueue).filter(
        VideoQueue.profile_slug == profile.slug,
        VideoQueue.status == "scheduled"
    ).count()

    failed = db.query(VideoQueue).filter(
        VideoQueue.profile_slug == profile.slug,
        VideoQueue.status == "failed"
    ).count()

    total_pending = db.query(PendingApproval).filter(
        PendingApproval.status == "pending"
    ).count()

    return {
        "profile": profile.slug,
        "queued": queued,
        "scheduled": scheduled,
        "failed": failed,
        "total_pending": total_pending,
    }


# ─── DELETE /reject/{id} ─────────────────────────────────────────────────

@router.delete("/reject/{item_id}")
def reject_item(item_id: int, db: Session = Depends(get_db)):
    """
    Rejeita um vídeo pendente.
    Remove do DB e aplica garbage collection no arquivo físico.
    """
    item = db.query(PendingApproval).filter(PendingApproval.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    video_path = item.video_path

    # Remover do DB
    db.delete(item)
    db.commit()

    # Garbage collection: remover arquivo físico
    if video_path and os.path.exists(video_path):
        try:
            os.remove(video_path)
            logger.info(f"🗑️ Arquivo removido: {video_path}")
        except OSError as e:
            logger.warning(f"Falha ao remover arquivo {video_path}: {e}")

    logger.info(f"❌ Item #{item_id} rejeitado e removido")

    return {"message": "Vídeo rejeitado e removido com sucesso"}


# ─── POST /invert/{id} ──────────────────────────────────────────────────

@router.post("/invert/{item_id}")
async def invert_item(item_id: int, db: Session = Depends(get_db)):
    """
    Inverte o layout do vídeo: gameplay sobe pro topo, facecam desce.
    Usa FFmpeg para cortar a imagem 1080x1920 pela metade e recombinar
    com vstack invertido. Não precisa de Whisper ou re-download.
    """
    item = db.query(PendingApproval).filter(PendingApproval.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    if not os.path.exists(item.video_path):
        raise HTTPException(status_code=400, detail="Arquivo original não encontrado")

    # Gerar caminho de saída
    base, ext = os.path.splitext(item.video_path)
    inverted_path = f"{base}_inverted{ext}"

    # FFmpeg: cortar metade superior (facecam 960px) e metade inferior (gameplay 960px)
    # e empilhar na ordem inversa (gameplay no topo, facecam embaixo)
    cmd = [
        "ffmpeg", "-y",
        "-i", item.video_path,
        "-filter_complex",
        "[0:v]crop=1080:960:0:0[top];"     # facecam (metade superior)
        "[0:v]crop=1080:960:0:960[bottom];" # gameplay (metade inferior)
        "[bottom][top]vstack=inputs=2[out]", # inverter: gameplay em cima, facecam embaixo
        "-map", "[out]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "copy",
        "-movflags", "+faststart",
        inverted_path,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        _, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
    except asyncio.TimeoutError:
        process.kill()
        raise HTTPException(status_code=500, detail="FFmpeg timeout na inversão")

    if process.returncode != 0:
        error = stderr.decode("utf-8", errors="replace").strip()[-200:]
        raise HTTPException(status_code=500, detail=f"FFmpeg falhou: {error}")

    if not os.path.exists(inverted_path):
        raise HTTPException(status_code=500, detail="Arquivo invertido não foi gerado")

    # Atualizar o path no DB para o novo arquivo
    old_path = item.video_path
    item.video_path = inverted_path
    db.commit()

    # Remover o arquivo antigo
    if os.path.exists(old_path):
        try:
            os.remove(old_path)
        except OSError:
            pass

    logger.info(f"🔀 Item #{item_id} invertido com sucesso: {inverted_path}")

    return {
        "message": "Layout invertido com sucesso",
        "new_path": inverted_path,
    }
