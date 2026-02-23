"""
Auto-Scheduler Core Logic - SYN-67
Orquestra o agendamento incremental de videos no TikTok Studio nativo.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from zoneinfo import ZoneInfo

from core.database import get_db
from core.models import VideoQueue, ScheduleItem

logger = logging.getLogger(__name__)

SP_TZ = ZoneInfo("America/Sao_Paulo")


def calculate_next_slots(
    profile_slug: str,
    count: int,
    schedule_hours: List[int],
    db
) -> List[datetime]:
    """
    Calcula os proximos `count` slots de agendamento disponiveis para o perfil.
    schedule_hours: lista de horas do dia para postar (ex: [12, 18]).
    Respeita slots ja ocupados na tabela schedule e na video_queue.

    Retorna lista de datetimes (sem timezone, para compatibilidade com DB).
    """
    now = datetime.now(SP_TZ)
    # Comecar sempre a partir de amanha para ter margem de 24h
    check_date: datetime = now + timedelta(days=1)

    # Ordenar os horarios para distribuicao correta ao longo do dia
    sorted_hours = sorted(set(schedule_hours)) if schedule_hours else [18]

    slots = []

    # Buscar slots ja ocupados na tabela de agendamentos
    def _get_occupied_times(start_dt: datetime, end_dt: datetime) -> set:
        start_naive = start_dt.replace(tzinfo=None)
        end_naive = end_dt.replace(tzinfo=None)
        existing = db.query(ScheduleItem).filter(
            ScheduleItem.profile_slug == profile_slug,
            ScheduleItem.scheduled_time >= start_naive,
            ScheduleItem.scheduled_time <= end_naive,
            ScheduleItem.status.in_(["pending", "processing", "completed", "posted"])
        ).all()
        # Arredonda para hora para comparacao
        return {s.scheduled_time.replace(minute=0, second=0) for s in existing}

    # Buscar slots ja ocupados na video_queue (agendados)
    def _get_queued_times(start_dt: datetime, end_dt: datetime) -> set:
        start_naive = start_dt.replace(tzinfo=None)
        end_naive = end_dt.replace(tzinfo=None)
        queued = db.query(VideoQueue).filter(
            VideoQueue.profile_slug == profile_slug,
            VideoQueue.status == "scheduled",
            VideoQueue.scheduled_at >= start_naive,
            VideoQueue.scheduled_at <= end_naive
        ).all()
        return {s.scheduled_at.replace(minute=0, second=0) for s in queued if s.scheduled_at}

    max_search_days = 90
    for _ in range(max_search_days):
        if len(slots) >= count:
            break

        day_start = datetime(check_date.year, check_date.month, check_date.day, 0, 0, 0, tzinfo=SP_TZ)
        day_end = datetime(check_date.year, check_date.month, check_date.day, 23, 59, 59, tzinfo=SP_TZ)

        occupied = _get_occupied_times(day_start, day_end) | _get_queued_times(day_start, day_end)

        for hour in sorted_hours:
            if len(slots) >= count:
                break

            slot_dt = datetime(
                check_date.year, check_date.month, check_date.day,
                hour, 0, 0, tzinfo=SP_TZ
            )

            slot_naive_hour = slot_dt.replace(tzinfo=None, minute=0, second=0)
            if slot_naive_hour not in occupied:
                slots.append(slot_dt.replace(tzinfo=None))
                occupied.add(slot_naive_hour)

        check_date = check_date + timedelta(days=1)

    if len(slots) < count:
        logger.warning(f"[AUTO-SCHEDULER] So foram encontrados {len(slots)} de {count} slots solicitados em {max_search_days} dias.")

    return slots


def create_queue(
    profile_slug: str,
    videos: List[dict],  # [{"path": str, "caption": str, "hashtags": list, "privacy_level": str}]
    posts_per_day: int,
    schedule_hours: List[int],  # Ex: [12, 18] - horarios exatos por dia
    db
) -> List[VideoQueue]:
    """
    Cria registros na fila de videos (status=queued).
    Nao faz agendamento ainda - apenas persiste a fila.
    """
    # Remover fila existente para este perfil (que nao estejam em progresso)
    db.query(VideoQueue).filter(
        VideoQueue.profile_slug == profile_slug,
        VideoQueue.status.in_(["queued", "failed", "cancelled"])
    ).delete()
    db.flush()

    sorted_hours = sorted(set(schedule_hours)) if schedule_hours else [18]

    items = []
    for i, video in enumerate(videos):
        item = VideoQueue(
            profile_slug=profile_slug,
            video_path=video["path"],
            caption=video.get("caption", ""),
            hashtags=video.get("hashtags", []),
            privacy_level=video.get("privacy_level", "public_to_everyone"),
            position=i,
            posts_per_day=posts_per_day,
            start_hour=sorted_hours[0],  # Mantido para compat
            schedule_hours=sorted_hours,
            status="queued"
        )
        db.add(item)
        items.append(item)

    db.commit()
    logger.info(f"[AUTO-SCHEDULER] Fila criada: {len(items)} videos para {profile_slug} | horarios: {sorted_hours}")
    return items


async def schedule_next_batch(
    profile_slug: str,
    batch_size: int,
    db
) -> dict:
    """
    Agenda os proximos `batch_size` videos da fila no TikTok Studio.
    Importa e chama upload_video_monitored para cada item.

    Retorna: {"scheduled": int, "failed": int, "queued_remaining": int}
    """
    from core.uploader_monitored import upload_video_monitored

    # Buscar proximos da fila (status=queued, ordenado por posicao)
    pending = db.query(VideoQueue).filter(
        VideoQueue.profile_slug == profile_slug,
        VideoQueue.status == "queued"
    ).order_by(VideoQueue.position).limit(batch_size).all()

    if not pending:
        logger.info(f"[AUTO-SCHEDULER] Nenhum video pendente para {profile_slug}")
        return {"scheduled": 0, "failed": 0, "queued_remaining": 0}

    # Calcular slots para os items pendentes
    # schedule_hours e uma lista de horas do dia (ex: [12, 18])
    schedule_hours = pending[0].schedule_hours or [pending[0].start_hour or 18]
    slots = calculate_next_slots(
        profile_slug=profile_slug,
        count=len(pending),
        schedule_hours=schedule_hours,
        db=db
    )

    scheduled_count: int = 0
    failed_count: int = 0

    for i, queue_item in enumerate(pending):
        if i >= len(slots):
            logger.warning(f"[AUTO-SCHEDULER] Sem slots disponiveis para item {queue_item.id}. Interrompendo.")
            break

        slot = slots[i]
        slot_iso = slot.isoformat()

        logger.info(f"[AUTO-SCHEDULER] Agendando {queue_item.video_path} para {slot_iso}")

        try:
            result = await upload_video_monitored(
                session_name=profile_slug,
                video_path=queue_item.video_path,
                caption=queue_item.caption,
                hashtags=queue_item.hashtags,
                schedule_time=slot_iso,
                post=False,
                enable_monitor=False,
                privacy_level=queue_item.privacy_level,
            )

            if result.get("status") == "ready":
                # Criar ScheduleItem para rastreamento
                sched_item = ScheduleItem(
                    profile_slug=profile_slug,
                    video_path=queue_item.video_path,
                    scheduled_time=slot,
                    status="pending",
                    metadata_info={
                        "caption": queue_item.caption,
                        "hashtags": queue_item.hashtags,
                        "source": "auto_scheduler",
                        "queue_id": queue_item.id
                    }
                )
                db.add(sched_item)
                db.flush()

                # Atualizar video_queue
                queue_item.status = "scheduled"
                queue_item.scheduled_at = slot
                queue_item.schedule_item_id = sched_item.id

                db.commit()
                scheduled_count = scheduled_count + 1
                logger.info(f"[AUTO-SCHEDULER] Sucesso: item {queue_item.id} agendado para {slot}")
            else:
                queue_item.status = "failed"
                queue_item.error_message = result.get("message", "Upload falhou")
                db.commit()
                failed_count = failed_count + 1
                logger.error(f"[AUTO-SCHEDULER] Falhou: item {queue_item.id}: {queue_item.error_message}")

        except Exception as e:
            queue_item.status = "failed"
            queue_item.error_message = str(e)
            db.commit()
            failed_count = failed_count + 1
            logger.error(f"[AUTO-SCHEDULER] Excecao ao agendar item {queue_item.id}: {e}")

    # Contar restantes na fila
    queued_remaining = db.query(VideoQueue).filter(
        VideoQueue.profile_slug == profile_slug,
        VideoQueue.status == "queued"
    ).count()

    return {
        "scheduled": scheduled_count,
        "failed": failed_count,
        "queued_remaining": queued_remaining
    }


def get_queue_status(profile_slug: str, db) -> dict:
    """Retorna estado completo da fila para um perfil."""
    all_items = db.query(VideoQueue).filter(
        VideoQueue.profile_slug == profile_slug
    ).order_by(VideoQueue.position).all()

    counts = {"queued": 0, "scheduled": 0, "failed": 0, "cancelled": 0}
    for item in all_items:
        counts[item.status] = counts.get(item.status, 0) + 1

    return {
        "profile_slug": profile_slug,
        "total": len(all_items),
        "counts": counts,
        "items": [
            {
                "id": item.id,
                "position": item.position,
                "video_path": item.video_path,
                "caption": item.caption[:50] + "..." if len(item.caption) > 50 else item.caption,
                "status": item.status,
                "scheduled_at": item.scheduled_at.isoformat() if item.scheduled_at else None,
                "error_message": item.error_message,
            }
            for item in all_items
        ]
    }
