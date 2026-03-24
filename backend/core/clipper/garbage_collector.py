"""
Garbage Collector — Limpeza automática de disco para o pipeline Clipper.

Regras:
1. Clips brutos (baixados da Twitch) → deletados após o job completar/falhar
2. Vídeos rejeitados → arquivo deletado imediatamente
3. Vídeos postados com sucesso → deletados 24h após confirmação de post no TikTok
4. Traces/screenshots de debug → deletados após 7 dias
5. Exports órfãos (sem PendingApproval correspondente) → deletados após 48h

Segurança:
- NUNCA deleta vídeos pendentes de aprovação
- NUNCA deleta vídeos aprovados mas ainda não postados
- NUNCA deleta vídeos cujo post falhou (podem precisar re-postar)
- Só deleta vídeos postados COM SUCESSO há mais de 24h
"""

import os
import glob
import logging
from datetime import datetime, timezone, timedelta

from core.database import safe_session
from core.clipper.models import ClipJob
from core.models import PendingApproval, ScheduleItem

logger = logging.getLogger("GarbageCollector")

# ── Configuração ──
CLIPS_DIR = "/app/data/clipper/clips"
EXPORTS_DIR = "/app/data/exports"
ERRORS_DIR = "/app/errors"
MONITOR_DIR = "/app/MONITOR/runs"
POSTED_RETENTION_HOURS = 24  # Manter vídeo 24h após postagem confirmada
DEBUG_RETENTION_DAYS = 7     # Manter traces/screenshots por 7 dias
MAX_CLIPS_DIR_GB = 5         # Limite máximo de espaço para clips brutos
AUDIO_TEMP_DIR = "/app/data/clipper/audio_temp"
SUBS_DIR = "/app/data/clipper/subs"


def run_gc():
    """Executa todas as rotinas de limpeza."""
    logger.info("🧹 Garbage Collector iniciado")

    freed = 0
    freed += _clean_processed_clips()
    freed += _clean_rejected_videos()
    freed += _clean_posted_videos()
    freed += _clean_old_debug_files()
    freed += _clean_orphan_exports()
    freed += _clean_temp_files()
    freed += _enforce_clips_size_limit()

    _clean_old_failed_jobs()

    freed_mb = freed / (1024 * 1024)
    logger.info(f"🧹 GC finalizado — {freed_mb:.1f} MB liberados")
    return freed


def _file_size_safe(path: str) -> int:
    """Retorna tamanho do arquivo ou 0 se não existir."""
    try:
        return os.path.getsize(path) if os.path.exists(path) else 0
    except OSError:
        return 0


def _remove_file(path: str) -> int:
    """Remove arquivo e retorna bytes liberados."""
    size = _file_size_safe(path)
    try:
        if os.path.exists(path):
            os.remove(path)
            logger.debug(f"  🗑️ Removido: {os.path.basename(path)} ({size / 1024 / 1024:.1f} MB)")
    except OSError as e:
        logger.warning(f"  ⚠️ Falha ao remover {path}: {e}")
        return 0
    return size


def _clean_processed_clips() -> int:
    """
    Remove clips brutos de jobs que já completaram ou falharam permanentemente.
    Clips de jobs ativos (pending, downloading, transcribing, editing, stitching) são preservados.
    """
    freed = 0
    if not os.path.isdir(CLIPS_DIR):
        return 0

    # Buscar job IDs ativos (que ainda precisam dos clips)
    active_job_ids = set()
    with safe_session() as db:
        active_jobs = db.query(ClipJob.id).filter(
            ClipJob.status.in_(["pending", "downloading", "transcribing", "editing", "stitching", "waiting_clips"])
        ).all()
        active_job_ids = {j.id for j in active_jobs}

    # Listar todos os clips e verificar se o job correspondente está ativo
    clip_files = glob.glob(os.path.join(CLIPS_DIR, "job*_clip*"))
    removed_count = 0
    for clip_path in clip_files:
        filename = os.path.basename(clip_path)
        # Extrair job ID do nome: "job10_clip0_titulo.mp4" → 10
        try:
            job_id = int(filename.split("_clip")[0].replace("job", ""))
        except (ValueError, IndexError):
            continue

        if job_id not in active_job_ids:
            freed += _remove_file(clip_path)
            removed_count += 1

    if removed_count:
        logger.info(f"  📦 Clips brutos: {removed_count} arquivos removidos de jobs finalizados")
    return freed


def _clean_rejected_videos() -> int:
    """Remove arquivos de vídeos rejeitados na curadoria."""
    freed = 0
    with safe_session() as db:
        rejected = db.query(PendingApproval).filter(
            PendingApproval.status == "rejected"
        ).all()

        for video in rejected:
            if video.video_path and os.path.exists(video.video_path):
                freed += _remove_file(video.video_path)
            # Marcar como limpo (não tentar deletar de novo)
            video.video_path = None
            db.commit()

    return freed


def _clean_posted_videos() -> int:
    """
    Remove vídeos que foram POSTADOS COM SUCESSO no TikTok há mais de 24h.

    Critérios OBRIGATÓRIOS (todos devem ser verdadeiros):
    1. PendingApproval.status == "approved"
    2. Existe ScheduleItem correspondente (mesmo video_path)
    3. ScheduleItem.status == "completed" (postou com sucesso)
    4. ScheduleItem.completed_at ou updated_at é > 24h atrás
    """
    freed = 0
    cutoff = datetime.now(timezone.utc) - timedelta(hours=POSTED_RETENTION_HOURS)

    with safe_session() as db:
        approved = db.query(PendingApproval).filter(
            PendingApproval.status == "approved",
            PendingApproval.video_path.isnot(None)
        ).all()

        for video in approved:
            if not video.video_path or not os.path.exists(video.video_path):
                continue

            # Buscar ScheduleItem correspondente pelo video_path
            video_filename = os.path.basename(video.video_path)
            schedule_item = db.query(ScheduleItem).filter(
                ScheduleItem.video_path.contains(video_filename),
                ScheduleItem.status == "completed"
            ).first()

            if not schedule_item:
                # Vídeo aprovado mas NÃO postado ainda → NÃO deletar
                continue

            # Verificar se postou há mais de 24h
            post_time = schedule_item.updated_at or schedule_item.scheduled_time
            if post_time and post_time.replace(tzinfo=timezone.utc) < cutoff:
                logger.info(f"  ✅ Vídeo postado há >24h: {video_filename} (postado em {post_time})")
                freed += _remove_file(video.video_path)
                video.video_path = None
                db.commit()

    return freed


def _clean_old_debug_files() -> int:
    """Remove traces, screenshots e reports de debug antigos (>7 dias)."""
    freed = 0
    cutoff_ts = (datetime.now() - timedelta(days=DEBUG_RETENTION_DAYS)).timestamp()

    for debug_dir in [MONITOR_DIR, ERRORS_DIR]:
        if not os.path.isdir(debug_dir):
            continue

        for root, dirs, files in os.walk(debug_dir):
            for f in files:
                fpath = os.path.join(root, f)
                try:
                    if os.path.getmtime(fpath) < cutoff_ts:
                        freed += _remove_file(fpath)
                except OSError:
                    continue

        # Remover diretórios vazios
        for root, dirs, files in os.walk(debug_dir, topdown=False):
            for d in dirs:
                dpath = os.path.join(root, d)
                try:
                    if not os.listdir(dpath):
                        os.rmdir(dpath)
                except OSError:
                    pass

    if freed:
        logger.info(f"  🔍 Debug files antigos: {freed / 1024 / 1024:.1f} MB removidos")
    return freed


def _clean_orphan_exports() -> int:
    """
    Remove arquivos em exports/ que não têm PendingApproval correspondente
    e são mais antigos que 48h (provavelmente sobras de jobs antigos).
    """
    freed = 0
    if not os.path.isdir(EXPORTS_DIR):
        return 0

    cutoff_ts = (datetime.now() - timedelta(hours=48)).timestamp()

    # Buscar todos os video_paths conhecidos
    known_paths = set()
    with safe_session() as db:
        approvals = db.query(PendingApproval.video_path).filter(
            PendingApproval.video_path.isnot(None)
        ).all()
        known_paths = {os.path.basename(a.video_path) for a in approvals if a.video_path}

    for f in os.listdir(EXPORTS_DIR):
        fpath = os.path.join(EXPORTS_DIR, f)
        if not os.path.isfile(fpath):
            continue
        if f in known_paths:
            continue  # Arquivo ainda referenciado
        try:
            if os.path.getmtime(fpath) < cutoff_ts:
                logger.info(f"  👻 Export órfão: {f}")
                freed += _remove_file(fpath)
        except OSError:
            continue

    return freed


def _clean_temp_files() -> int:
    """Remove arquivos temporários de áudio e legendas antigas."""
    freed = 0

    for temp_dir in [AUDIO_TEMP_DIR, SUBS_DIR]:
        if not os.path.isdir(temp_dir):
            continue
        cutoff_ts = (datetime.now() - timedelta(hours=6)).timestamp()
        for f in os.listdir(temp_dir):
            fpath = os.path.join(temp_dir, f)
            try:
                if os.path.isfile(fpath) and os.path.getmtime(fpath) < cutoff_ts:
                    freed += _remove_file(fpath)
            except OSError:
                continue

    if freed:
        logger.info(f"  🎵 Temp files: {freed / 1024 / 1024:.1f} MB removidos")
    return freed


def _enforce_clips_size_limit() -> int:
    """
    Se o diretório de clips ultrapassar MAX_CLIPS_DIR_GB, remove os clips
    mais antigos (por mtime) de jobs NÃO-ativos até voltar abaixo do limite.
    Isso evita que o disco encha quando um alvo tem centenas de clips.
    """
    freed = 0
    if not os.path.isdir(CLIPS_DIR):
        return 0

    max_bytes = MAX_CLIPS_DIR_GB * 1024 * 1024 * 1024

    # Calcular tamanho atual
    all_clips = []
    total_size = 0
    for f in os.listdir(CLIPS_DIR):
        fpath = os.path.join(CLIPS_DIR, f)
        if not os.path.isfile(fpath):
            continue
        try:
            size = os.path.getsize(fpath)
            mtime = os.path.getmtime(fpath)
            all_clips.append((fpath, size, mtime, f))
            total_size += size
        except OSError:
            continue

    if total_size <= max_bytes:
        return 0

    logger.warning(f"  ⚠️ Clips dir: {total_size / 1024 / 1024 / 1024:.1f} GB (limite: {MAX_CLIPS_DIR_GB} GB)")

    # Buscar jobs ativos para não deletar seus clips
    active_job_ids = set()
    with safe_session() as db:
        active_jobs = db.query(ClipJob.id).filter(
            ClipJob.status.in_(["pending", "downloading", "transcribing", "editing", "stitching", "waiting_clips"])
        ).all()
        active_job_ids = {j.id for j in active_jobs}

    # Ordenar por mtime (mais antigos primeiro) e remover até ficar abaixo do limite
    all_clips.sort(key=lambda x: x[2])
    removed_count = 0

    for fpath, size, mtime, filename in all_clips:
        if total_size <= max_bytes:
            break

        # Extrair job ID e pular se ativo
        try:
            job_id = int(filename.split("_clip")[0].replace("job", ""))
        except (ValueError, IndexError):
            continue

        if job_id in active_job_ids:
            continue

        freed += _remove_file(fpath)
        total_size -= size
        removed_count += 1

    if removed_count:
        logger.info(f"  📏 Limite de espaço: {removed_count} clips antigos removidos ({freed / 1024 / 1024:.1f} MB)")
    return freed


def _clean_old_failed_jobs():
    """
    Remove registros de ClipJobs falhados com mais de 24h do banco.
    Isso mantém a contagem da esteira limpa.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    with safe_session() as db:
        old_failed = db.query(ClipJob).filter(
            ClipJob.status == "failed",
            ClipJob.created_at < cutoff,
        ).all()
        if old_failed:
            count = len(old_failed)
            job_ids = [j.id for j in old_failed]
            db.query(PendingApproval).filter(PendingApproval.clip_job_id.in_(job_ids)).delete(synchronize_session=False)
            for job in old_failed:
                db.delete(job)
            db.commit()
            logger.info(f"  🗂️ {count} jobs falhados antigos removidos do banco")
