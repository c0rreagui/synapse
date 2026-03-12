"""
Clipper Worker - ARQ Worker Settings
=====================================

Worker dedicado do ARQ para rodar o pipeline do clipper.
Isolado do worker principal (Playwright) para podermos otimizar recursos,
ja que o Whisper e o FFmpeg exigem bastante CPU/RAM (e VRAM se disponivel).

Configurado para esvaziar a fila `clipper:queue`.
"""

import sys
import logging
import os
from datetime import datetime, timezone
from arq.connections import RedisSettings
from dotenv import load_dotenv



# Carregar variaveis
load_dotenv()

# Ajustar path se necessario para rodar isolado
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.clipper.downloader import download_job_clips
from core.clipper.transcriber import transcribe_job_clips
from core.clipper.subtitle_engine import generate_ass_for_multiple
from core.clipper.editor import edit_clip
from core.clipper.stitcher import ensure_minimum_duration

from core.database import safe_session
from core.clipper.models import ClipJob, TwitchTarget
from core.models import PendingApproval

logger = logging.getLogger("ClipperWorker")


def _fail_job_db(job_id: int, error_message: str, current_step: str = "Falha no pipeline."):
    """Helper para marcar job como falhado no DB."""
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = error_message[:500]
            job.current_step = current_step
            db.commit()
    logger.error(f"Job #{job_id} falhado: {error_message[:200]}")


async def _process_clip_job_inner(ctx, job_id: int):
    """
    Funcao principal orquestradora do pipeline de um unico ClipJob.
    1. Download dos clipes
    2. Whisper (transcricao word-level)
    3. ASS (legendas estilizadas)
    4. FFmpeg Edit (facecam crop, ass burn, 9:16)
    5. Stitcher (crossfade se multiplos clipes)
    """
    logger.info(f"==> Iniciando processamento do ClipJob #{job_id}")

    # Guard: evitar reprocessamento se job ja nao esta pending
    with safe_session() as db:
        guard_job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if not guard_job:
            logger.warning(f"Job #{job_id} nao encontrado no DB, pulando.")
            return
        if guard_job.status not in ("pending", "downloading", "transcribing", "editing", "stitching"):
            logger.info(f"Job #{job_id} ja esta em status '{guard_job.status}', pulando reprocessamento.")
            return

    # 1. Download
    dl_result = await download_job_clips(job_id)
    if not dl_result.get("success"):
        error_msg = dl_result.get("error", "Unknown error")
        _fail_job_db(job_id, f"Download error: {error_msg}", "Falha no download dos clipes.")
        return

    # 2. Transcricao (Whisper)
    tr_result = await transcribe_job_clips(job_id)
    if not tr_result.get("success"):
        error_msg = tr_result.get("error", "Unknown error")
        errors = tr_result.get("errors", [])
        full_error = f"Transcription error: {error_msg}" + (f" | {' | '.join(errors)}" if errors else "")
        _fail_job_db(job_id, full_error, "Falha na transcricao de audio.")
        return

    # Preparar para edicao
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if not job:
            return
        local_paths = job.clip_local_paths or []
        transcriptions = job.whisper_result or []

    if not local_paths or not transcriptions:
        _fail_job_db(job_id, "Arquivos locais ou transcricoes nao encontrados.", "Falha ao preparar para edicao.")
        return

    # Buscar channel_name, auto_approve e target_id
    channel_name = None
    target_auto_approve = False
    target_id = None
    with safe_session() as db:
        job_obj = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if job_obj and job_obj.target_id:
            target_id = job_obj.target_id
            target = db.query(TwitchTarget).filter(TwitchTarget.id == job_obj.target_id).first()
            if target:
                channel_name = target.channel_name
                target_auto_approve = getattr(target, 'auto_approve', False) or False

    # Filtrar apenas pares clip+transcricao com palavras (B05/B25 fix)
    valid_pairs = []
    for path, trans in zip(local_paths, transcriptions):
        if trans.get("word_count", 0) > 0:
            valid_pairs.append((path, trans))
        else:
            logger.warning(f"Job #{job_id}: Clip {path} sem palavras transcritas, pulando edicao.")

    if not valid_pairs:
        _fail_job_db(job_id, "Nenhum clipe teve palavras transcritas com sucesso.", "Falha: transcricoes vazias.")
        return

    # 3. Gerar ASS & 4. FFmpeg Edit (por clipe individual)
    edited_paths = []

    # Atualiza DB para "editing"
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if job:
            job.status = "editing"
            job.current_step = f"Editando 0/{len(valid_pairs)} clipes..."
            job.progress_pct = 50
            db.commit()

    for idx, (path, trans) in enumerate(valid_pairs):
        try:
            ass_path = generate_ass_for_multiple(
                transcriptions=[trans],
                style_name="opus",
                time_offsets=[0.0]
            )

            edit_res = await edit_clip(
                video_path=path,
                ass_path=ass_path,
                timeout_seconds=900,
                channel_name=channel_name,
            )

            if edit_res.get("success"):
                edited_paths.append(edit_res.get("output_path"))
            else:
                logger.error(f"Job #{job_id} falhou na edicao do clipe {idx}: {edit_res.get('error')}")
        except Exception as e:
            logger.error(f"Job #{job_id} excecao na edicao do clipe {idx}: {e}", exc_info=True)

        with safe_session() as db:
            job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
            if job:
                job.current_step = f"Editando {idx + 1}/{len(valid_pairs)} clipes..."
                job.progress_pct = 50 + int(((idx + 1) / len(valid_pairs)) * 40)
                db.commit()

    if not edited_paths:
        _fail_job_db(job_id, "Nenhum clipe foi editado com sucesso.", "Falha na edicao.")
        return

    # 5. Stitching
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if job:
            job.status = "stitching"
            job.current_step = "Aplicando costura final..."
            job.progress_pct = 90
            db.commit()

    streamer_name = channel_name or ""

    # Aplicar Outro Filler se duracao total for menor que 60s
    if streamer_name and len(edited_paths) > 0:
        try:
            from core.clipper.stitcher import _get_duration
            durations = []
            for ep in edited_paths:
                durations.append(await _get_duration(ep))

            total_duration = sum(durations)

            if total_duration < 60.0:
                missing = 60.0 - total_duration + 1.0
                with safe_session() as db:
                    j = db.query(ClipJob).filter(ClipJob.id == job_id).first()
                    if j:
                        j.current_step = f"Gerando {missing:.1f}s de filler para atingir 1m..."
                        db.commit()

                from core.clipper.hook_generator import generate_outro_filler
                bg_clip = edited_paths[0]
                hook_res = await generate_outro_filler(
                    streamer=streamer_name,
                    target_duration=missing,
                    bg_video_path=bg_clip
                )
                if hook_res.get("success"):
                    hook_path = hook_res.get("output_path")
                    if hook_path and os.path.exists(hook_path):
                        edited_paths.append(hook_path)
                        logger.info(f"Job #{job_id}: Filler de {missing:.1f}s adicionado.")
                else:
                    logger.warning(f"Falha ao gerar filler para Job #{job_id}: {hook_res.get('error')}")

        except Exception as e:
            logger.error(f"Erro inesperado ao gerar filler: {e}", exc_info=True)

    # Stitching Final
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if job:
            job.status = "stitching"
            job.current_step = "Aplicando costura final..."
            job.progress_pct = 90
            db.commit()

    stitch_res = await ensure_minimum_duration(edited_clips=edited_paths)

    if not stitch_res.get("success"):
        _fail_job_db(job_id, f"Stitch error: {stitch_res.get('error')}", "Falha na costura.")
        return

    # Marcar como concluido
    output_path = stitch_res.get("output_path")
    duration = stitch_res.get("duration", 0)

    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if job:
            job.status = "completed"
            job.current_step = "Concluido!"
            job.progress_pct = 100
            job.output_path = output_path
            job.completed_at = datetime.now(timezone.utc)
            job.duration_seconds = duration
            db.commit()

    # Inserir na fila de curadoria (PendingApproval)
    try:
        file_size = os.path.getsize(output_path) if output_path and os.path.exists(output_path) else 0

        approval_status = "approved" if target_auto_approve else "pending"
        approval_id = None
        with safe_session() as db:
            approval = PendingApproval(
                clip_job_id=job_id,
                video_path=output_path,
                streamer_name=channel_name,
                title=f"{channel_name or 'Clip'} #{job_id}",
                duration_seconds=int(duration),
                file_size_bytes=file_size,
                status=approval_status,
            )
            db.add(approval)
            db.commit()
            db.refresh(approval)
            approval_id = approval.id

        if target_auto_approve:
            logger.info(f"Job #{job_id} Auto-Approved (PendingApproval #{approval_id}).")
            try:
                from core.auto_scheduler import create_queue, schedule_next_batch
                from core.models import Profile, Army

                with safe_session() as db:
                    # Resolver profile via Army do target (prioridade) ou fallback
                    profile = None
                    target = db.query(TwitchTarget).filter(TwitchTarget.id == target_id).first()
                    if target and target.army_id:
                        army = db.query(Army).filter(Army.id == target.army_id).first()
                        if army and army.profiles:
                            for p in army.profiles:
                                if p.active:
                                    profile = p
                                    break

                    if not profile:
                        profile = db.query(Profile).filter(Profile.active == True).first()

                    if profile:
                        create_queue(
                            profile_slug=profile.slug,
                            videos=[{
                                "path": output_path,
                                "caption": f"{channel_name or 'Clip'} #{job_id}",
                                "hashtags": [],
                                "privacy_level": "public_to_everyone",
                            }],
                            posts_per_day=2,
                            schedule_hours=[12, 18],
                            db=db,
                        )
                        result = await schedule_next_batch(
                            profile_slug=profile.slug,
                            batch_size=1,
                            db=db,
                        )
                        logger.info(f"Job #{job_id} Auto-Enfileirado no perfil @{profile.slug}: {result}")
                    else:
                        logger.warning(f"Job #{job_id}: Nenhum profile ativo para auto-enfileirar.")
            except Exception as sq_err:
                logger.error(f"Erro ao enfileirar Job #{job_id} no Scheduler: {sq_err}", exc_info=True)
        else:
            logger.info(f"Job #{job_id} inserido na fila de curadoria manual (PendingApproval #{approval_id}).")

    except Exception as e:
        logger.error(f"Job #{job_id} concluido mas falhou ao inserir na curadoria: {e}", exc_info=True)


async def process_clip_job(ctx, job_id: int):
    """
    Ponto de entrada do ARQ. Antes de processar o job recebido,
    verifica se ha jobs de alta prioridade que devem ser processados primeiro.
    """
    # Checar se ha job de alta prioridade que deve passar na frente
    actual_job_id = job_id
    try:
        with safe_session() as db:
            priority_job = (
                db.query(ClipJob)
                .filter(ClipJob.status == "pending", ClipJob.priority >= 1)
                .order_by(ClipJob.priority.desc(), ClipJob.id.asc())
                .first()
            )
            if priority_job and priority_job.id != job_id:
                # Ha um job prioritario diferente do que recebemos — processa ele primeiro
                logger.info(f"Job #{priority_job.id} tem prioridade {priority_job.priority}, processando antes de #{job_id}")
                actual_job_id = priority_job.id
                # Resetar prioridade para evitar loop
                priority_job.priority = 0
                db.commit()
    except Exception as e:
        logger.warning(f"Erro ao checar prioridade: {e}")

    try:
        await _process_clip_job_inner(ctx, actual_job_id)
    except Exception as e:
        logger.error(f"Erro fatal orfao processando job #{actual_job_id}: {e}", exc_info=True)
        try:
            _fail_job_db(actual_job_id, str(e), "Falha critica no worker pipeline.")
        except Exception as cleanup_err:
            logger.error(f"Falha secundaria ao marcar job #{actual_job_id} como falhado: {cleanup_err}")

    # Se trocamos o job, re-enfileirar o original para nao perder
    if actual_job_id != job_id:
        try:
            with safe_session() as db:
                orig = db.query(ClipJob).filter(ClipJob.id == job_id, ClipJob.status == "pending").first()
                if orig:
                    from core.config import REDIS_HOST, REDIS_PORT
                    from arq.connections import RedisSettings, create_pool as arq_create_pool
                    pool = await arq_create_pool(RedisSettings(host=REDIS_HOST, port=REDIS_PORT))
                    await pool.enqueue_job("process_clip_job", job_id, _queue_name="clipper:queue")
                    await pool.close()
                    logger.info(f"Job #{job_id} re-enfileirado apos processar prioritario #{actual_job_id}")
        except Exception as e:
            logger.warning(f"Falha ao re-enfileirar job #{job_id}: {e}")

async def startup(ctx):
    """
    Funcao que roda no startup do worker ARQ do Clipper.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    logger.info("Clipper Worker Conectado.")

    # Recovery: resetar jobs orfaos que ficaram travados em estados intermediarios
    stuck_statuses = ["processing", "downloading", "transcribing", "editing", "stitching"]
    with safe_session() as db:
        stuck_jobs = db.query(ClipJob).filter(ClipJob.status.in_(stuck_statuses)).all()
        if stuck_jobs:
            for job in stuck_jobs:
                logger.warning(f"Job #{job.id} orfao (status={job.status}). Resetando para pending.")
                job.status = "pending"
                job.current_step = "Reagendado apos recovery do worker"
                job.progress_pct = 0
            db.commit()
            logger.info(f"{len(stuck_jobs)} jobs orfaos resetados para reprocessamento.")

    # Iniciar Clipper Scheduler Loop (scan automatico de targets)
    try:
        from core.clipper.scheduler import clipper_scheduler_loop
        import asyncio
        ctx["scheduler_task"] = asyncio.create_task(clipper_scheduler_loop(poll_interval=60))
        logger.info("Clipper Scheduler Loop iniciado (poll=60s).")
    except Exception as e:
        logger.error(f"Falha ao iniciar Clipper Scheduler: {e}", exc_info=True)


async def shutdown(ctx):
    # Cancelar scheduler loop se estiver rodando
    scheduler_task = ctx.get("scheduler_task")
    if scheduler_task and not scheduler_task.done():
        scheduler_task.cancel()
        logger.info("Clipper Scheduler Loop cancelado.")
    logger.info("Clipper Worker Desligando.")




# Config do redis via env
from core.config import REDIS_URL
redis_url = REDIS_URL

class WorkerSettings:
    """Configuracao lida pelo script `arq` na linha de comando."""
    functions = [process_clip_job]
    redis_settings = RedisSettings.from_dsn(redis_url)
    queue_name = "clipper:queue"
    max_jobs = 1  # Conservador devido a VRAM/RAM (Whisper e FFmpeg limitados a 1 por vez neste container)
    on_startup = startup
    on_shutdown = shutdown
    job_timeout = 1800  # Pode demorar bastante (download + whisper + edicao + stitch)
