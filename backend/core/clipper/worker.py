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

    # 1. Download
    dl_result = await download_job_clips(job_id)
    if not dl_result.get("success"):
        error_msg = dl_result.get("error", "Unknown error")
        logger.error(f"Job #{job_id} falhou no Download. Motivo: {error_msg}")
        with safe_session() as db:
            job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = f"Download error: {error_msg}"
                job.current_step = "Falha no download dos clipes."
                db.commit()
        return

    # 2. Transcricao (Whisper)
    tr_result = await transcribe_job_clips(job_id)
    if not tr_result.get("success"):
        error_msg = tr_result.get("error", "Unknown error")
        logger.error(f"Job #{job_id} falhou na Transcricao. Motivo: {error_msg}")
        with safe_session() as db:
            job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = f"Transcription error: {error_msg}"
                job.current_step = "Falha na transcrição de áudio."
                db.commit()
        return

    # Preparar para edicao
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if not job:
            return
        local_paths = job.clip_local_paths
        transcriptions = job.whisper_result
    
    if not local_paths or not transcriptions:
        logger.error(f"Job #{job_id} estado invalido para edicao. (Sem paths ou sem transcricao)")
        with safe_session() as db:
            job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = "Arquivos locais de vídeo ou transcrições não encontrados para edição."
                job.current_step = "Falha ao preparar para edição."
                db.commit()
        return

    # Buscar channel_name e auto_approve para o fallback de visao (reutiliza sessao existente)
    channel_name = None
    target_auto_approve = False
    with safe_session() as db:
        job_obj = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if job_obj and job_obj.target_id:
            target = db.query(TwitchTarget).filter(TwitchTarget.id == job_obj.target_id).first()
            if target:
                channel_name = target.channel_name
                target_auto_approve = target.auto_approve

    # 3. Gerar ASS & 4. FFmpeg Edit (por clipe individual)
    edited_paths = []
    
    # Atualiza DB para "editing"
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        job.status = "editing"
        job.current_step = f"Editando 0/{len(local_paths)} clipes..."
        job.progress_pct = 50
        db.commit()

    for idx, (path, trans) in enumerate(zip(local_paths, transcriptions)):
        # Gera ASS para o clipe especifico
        # Assumindo que a funcao default consiga lidar com transcricao singular numa lista
        ass_path = generate_ass_for_multiple(
            transcriptions=[trans],
            style_name="opus",
            time_offsets=[0.0]
        )
        
        # Edita no FFmpeg (9:16, facecam crop, ass burn)
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

        with safe_session() as db:
            job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
            job.current_step = f"Editando {idx + 1}/{len(local_paths)} clipes..."
            job.progress_pct = 50 + int(((idx + 1) / len(local_paths)) * 40)
            db.commit()

    if not edited_paths:
        err_msg = edit_res.get("error", "Unknown error") if 'edit_res' in locals() else "Nenhum clipe foi editado com sucesso."
        with safe_session() as db:
            job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.current_step = "Falha na edicao."
                job.error_message = f"Edit error: {err_msg}"
                db.commit()
        return

    # 5. Stitching
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        job.status = "stitching"
        job.current_step = "Aplicando costura final..."
        job.progress_pct = 90
        streamer_name = channel_name or ""
        clip_metadata = job.clip_metadata or []
        db.commit()

    # 5. Aplicar Outro Filler se duracao total for menor que 60s
    if streamer_name and len(edited_paths) > 0:
        try:
            from core.clipper.stitcher import _get_duration
            durations = []
            for ep in edited_paths:
                durations.append(await _get_duration(ep))
            
            total_duration = sum(durations)
            
            if total_duration < 60.0:
                missing = 60.0 - total_duration + 1.0 # 1s margin for safety
                with safe_session() as db:
                    j = db.query(ClipJob).filter(ClipJob.id == job_id).first()
                    j.current_step = f"Gerando {missing:.1f}s de filler para atingir 1m..."
                    db.commit()

                from core.clipper.hook_generator import generate_outro_filler
                bg_clip = edited_paths[0] # usar o primeiro clip pra extrair frame
                hook_res = await generate_outro_filler(
                    streamer=streamer_name,
                    target_duration=missing,
                    bg_video_path=bg_clip
                )
                if hook_res.get("success"):
                    hook_path = hook_res.get("output_path")
                    if hook_path and os.path.exists(hook_path):
                        edited_paths.append(hook_path)
                else:
                    logger.warning(f"Falha ao gerar filler para Job #{job_id}: {hook_res.get('error')}")

        except Exception as e:
            logger.error(f"Erro inesperado ao gerar filler: {e}")

    # 6. Stitching Final
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        job.status = "stitching"
        job.current_step = "Aplicando costura final..."
        job.progress_pct = 90
        db.commit()

    stitch_res = await ensure_minimum_duration(edited_clips=edited_paths)

    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if stitch_res.get("success"):
            job.status = "completed"
            job.current_step = "Concluido!"
            job.progress_pct = 100
            job.output_path = stitch_res.get("output_path")
            job.completed_at = datetime.now(timezone.utc)
            job.duration_seconds = stitch_res.get("duration", 0)
            db.commit()

            try:
                output_path = stitch_res.get("output_path")
                file_size = os.path.getsize(output_path) if output_path and os.path.exists(output_path) else 0

                if target_auto_approve:
                    # Direto pra fila inteligente de postagem se Auto-Approve True
                    with safe_session() as db2:
                        approval = PendingApproval(
                            clip_job_id=job_id,
                            video_path=output_path,
                            streamer_name=channel_name,
                            title=f"{channel_name or 'Clip'} #{job_id}",
                            duration_seconds=int(stitch_res.get("duration", 0)),
                            file_size_bytes=file_size,
                            status="approved",
                        )
                        db2.add(approval)
                        db2.commit()
                        db2.refresh(approval)
                        logger.info(f"⚡ Job #{job_id} Auto-Approved. Inserindo na Fila Inteligente...")

                        # Send to auto_scheduler queue
                        try:
                            from core.auto_scheduler.queue import create_queue
                            from core.auto_scheduler.scheduler import schedule_next_batch
                            from core.models import Profile
                            
                            profile = db2.query(Profile).filter(Profile.active == True).first()
                            
                            if profile:
                                create_queue(db2, profile.id, approval.id)
                                logger.info(f"✅ Job #{job_id} Auto-Enfileirado e Agendado com Sucesso")
                                # Schedule next batch if possible to accommodate the new item
                                schedule_next_batch(db2, profile.id)
                            else:
                                logger.error(f"⚠️ Auto-Approve: Job #{job_id} não tem profile ativo para ser enfileirado.")
                        except Exception as sq_err:
                            logger.error(f"⚠️ Erro ao enfileirar Job #{job_id} pro Scheduler: {sq_err}")
                else:
                    # Comportamento padrão: Pendente de aprovação manual
                    with safe_session() as db2:
                        approval = PendingApproval(
                            clip_job_id=job_id,
                            video_path=output_path,
                            streamer_name=channel_name,
                            title=f"{channel_name or 'Clip'} #{job_id}",
                            duration_seconds=int(stitch_res.get("duration", 0)),
                            file_size_bytes=file_size,
                            status="pending",
                        )
                        db2.add(approval)
                        db2.commit()
                        logger.info(f"✅ Job #{job_id} inserido na fila de curadoria (PendingApproval #{approval.id})")
            except Exception as e:
                logger.error(f"⚠️ Job #{job_id} concluído mas falhou ao inserir na curadoria/fila: {e}", exc_info=True)
        else:
            job.status = "failed"
            job.current_step = "Falha na costura."
            job.error_message = f"Stitch error: {stitch_res.get('error')}"
            db.commit()


async def process_clip_job(ctx, job_id: int):
    try:
        await _process_clip_job_inner(ctx, job_id)
    except Exception as e:
        logger.error(f"❌ Erro fatal orfão processando job #{job_id}: {e}", exc_info=True)
        try:
            import os
            with safe_session() as db:
                job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
                if job:
                    job.status = "failed"
                    job.error_message = str(e)[:500]
                    job.current_step = "Falha crítica no worker pipeline."
                    db.commit()
                    
                    if job.clip_local_paths:
                        for p in job.clip_local_paths:
                            if os.path.exists(p):
                                os.remove(p)
                    if hasattr(job, "output_path") and job.output_path and os.path.exists(job.output_path):
                        os.remove(job.output_path)
        except Exception as cleanup_err:
            logger.error(f"Falha secundária ao limpar recursos do job #{job_id}: {cleanup_err}")

async def startup(ctx):
    """
    Funcao que roda no startup do worker ARQ do Clipper.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    logger.info("⚡ Clipper Worker Conectado.")
    

async def shutdown(ctx):
    logger.info("🛑 Clipper Worker Desligando.")




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
    job_timeout = 1800  # Pode demorar bastante (download + whisper + edição + stitch)
