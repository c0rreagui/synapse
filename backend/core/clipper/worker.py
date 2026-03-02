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
from core.clipper.monitor import monitor_loop

from core.database import safe_session
from core.clipper.models import ClipJob, TwitchTarget

logger = logging.getLogger("ClipperWorker")


async def process_clip_job(ctx, job_id: int):
    """
    Funcao principal orquestradora do pipeline de um unico ClipJob.
    1. Download (já baixa os 2 clips se achar)
    2. Whisper nos dois
    3. ASS nos dois
    4. FFmpeg Edit (cortar cam, ass, 9:16)
    5. Stitcher (juntar pra dar >60s)
    """
    logger.info(f"==> Iniciando processamento do ClipJob #{job_id}")

    # 1. Download
    dl_result = await download_job_clips(job_id)
    if not dl_result.get("success"):
        logger.error(f"Job #{job_id} falhou no Download.")
        return

    # 2. Transcricao (Whisper)
    tr_result = await transcribe_job_clips(job_id)
    if not tr_result.get("success"):
        logger.error(f"Job #{job_id} falhou na Transcricao.")
        return

    # Preparar para edicao
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if not job:
            return
        local_paths = job.clip_local_paths
        transcriptions = job.whisper_result
    
    if not local_paths or not transcriptions:
        logger.error(f"Job #{job_id} estado invalido para edicao.")
        return

    # Buscar channel_name para o fallback de visao
    channel_name = None
    try:
        with safe_session() as db:
            job_obj = db.query(ClipJob).filter(ClipJob.id == job_id).first()
            if job_obj and job_obj.target_id:
                target = db.query(TwitchTarget).filter(TwitchTarget.id == job_obj.target_id).first()
                if target:
                    channel_name = target.channel_name
    except Exception as e:
        logger.warning(f"Nao foi possivel buscar channel_name para job #{job_id}: {e}")

    # 3. Gerar ASS & 4. FFmpeg Edit (por clipe individual)
    edited_paths = []
    
    # Atualiza DB para "editing"
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        job.status = "editing"
        job.current_step = f"Editando 0/{len(local_paths)} clipes..."
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
            db.commit()

    if not edited_paths:
        with safe_session() as db:
            job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
            job.status = "failed"
            job.current_step = "Falha na edicao."
            job.error_message = "Nenhum clipe foi editado com sucesso."
            db.commit()
        return

    # 5. Stitching
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        job.status = "stitching"
        job.current_step = "Aplicando costura para garantir >60s..."
        db.commit()

    stitch_res = await ensure_minimum_duration(edited_clips=edited_paths)

    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if stitch_res.get("success"):
            job.status = "completed"
            job.current_step = "Concluido!"
            job.output_path = stitch_res.get("output_path")
            job.completed_at = datetime.now(timezone.utc)
            job.duration_seconds = stitch_res.get("duration", 0)
        else:
            job.status = "failed"
            job.current_step = "Falha na costura."
            job.error_message = f"Stitch error: {stitch_res.get('error')}"
        db.commit()


async def startup(ctx):
    """
    Funcao que roda no startup do worker ARQ do Clipper.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    logger.info("⚡ Clipper Worker Conectado.")
    

async def shutdown(ctx):
    logger.info("🛑 Clipper Worker Desligando.")


# Config do redis via env
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

class WorkerSettings:
    """Configuracao lida pelo script `arq` na linha de comando."""
    functions = [process_clip_job]
    redis_settings = RedisSettings.from_dsn(redis_url)
    queue_name = "clipper:queue"
    max_jobs = 1  # Conservador devido a VRAM/RAM (Whisper e FFmpeg limitados a 1 por vez neste container)
    on_startup = startup
    on_shutdown = shutdown
    job_timeout = 1800  # Pode demorar bastante (download + whisper + edição + stitch)
