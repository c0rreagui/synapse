"""
Clipper Downloader - Download de Clipes via yt-dlp
===================================================

Responsavel por baixar fisicamente os clipes da Twitch selecionados
pelo monitor.py e atualizar os caminhos locais no ClipJob.

Utiliza yt-dlp para maxima compatibilidade e resiliencia com
URLs da Twitch (incluindo fallback para URLs de thumbnail -> mp4).

Requisitos:
    - yt-dlp instalado (pip install yt-dlp)
    - FFmpeg disponivel no PATH (para merge de streams)
"""

import os
import asyncio
import logging
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from core.database import safe_session
from core.clipper.models import ClipJob
from core.config import DATA_DIR

logger = logging.getLogger("ClipperDownloader")

# Diretorio para clipes baixados
CLIPS_DIR = os.path.join(DATA_DIR, "clipper", "clips")
os.makedirs(CLIPS_DIR, exist_ok=True)


def _sanitize_filename(text: str, max_len: int = 60) -> str:
    """Remove caracteres invalidos para nomes de arquivo."""
    invalid = '<>:"/\\|?*\n\r\t'
    for c in invalid:
        text = text.replace(c, "")
    text = text.strip().replace(" ", "_")
    return text[:max_len] if text else "clip"


def _build_output_path(job_id: int, clip_index: int, clip_title: str) -> str:
    """Constroi o caminho de saida para um clipe."""
    safe_title = _sanitize_filename(clip_title)
    filename = f"job{job_id}_clip{clip_index}_{safe_title}.mp4"
    return os.path.join(CLIPS_DIR, filename)


def _resolve_alt_extension(output_path: str) -> bool:
    """
    yt-dlp pode salvar com extensao diferente (.mkv, .webm).
    Tenta encontrar e renomear para .mp4.
    Retorna True se conseguiu resolver, False caso contrario.
    """
    base = os.path.splitext(output_path)[0]
    for ext in [".mp4", ".mkv", ".webm"]:
        alt_path = base + ext
        if os.path.exists(alt_path):
            if alt_path != output_path:
                os.rename(alt_path, output_path)
            return True
    return False


async def download_clip(
    url: str,
    output_path: str,
    timeout_seconds: int = 120,
) -> Dict[str, Any]:
    """
    Baixa um unico clipe da Twitch usando yt-dlp.

    Args:
        url: URL do clipe (https://clips.twitch.tv/...)
        output_path: Caminho do arquivo de saida
        timeout_seconds: Timeout maximo para o download

    Returns:
        Dict com: success, path, duration, file_size, error
    """
    if os.path.exists(output_path):
        # Ja baixado (idempotencia)
        file_size = os.path.getsize(output_path)
        if file_size > 1000:  # >1KB = provavelmente valido
            logger.info(f"Clipe ja existe: {output_path} ({file_size} bytes)")
            duration = await _get_duration(output_path)
            return {
                "success": True,
                "path": output_path,
                "duration": duration,
                "file_size": file_size,
                "error": None,
            }

    # Construir comando yt-dlp
    cmd = [
        "yt-dlp",
        "--no-warnings",
        "--no-playlist",
        "--format", "best[ext=mp4]/best",
        "--output", output_path,
        "--no-overwrites",
        "--retries", "3",
        "--fragment-retries", "3",
        "--socket-timeout", "30",
        url,
    ]

    logger.info(f"Baixando clipe: {url} -> {output_path}")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(
            process.communicate(), timeout=timeout_seconds
        )

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace").strip()
            logger.error(f"yt-dlp falhou (code {process.returncode}): {error_msg}")
            return {
                "success": False,
                "path": None,
                "duration": 0,
                "file_size": 0,
                "error": f"yt-dlp exit code {process.returncode}: {error_msg[:200]}",
            }

        if not os.path.exists(output_path):
            resolved = _resolve_alt_extension(output_path)
            if not resolved:
                return {
                    "success": False,
                    "path": None,
                    "duration": 0,
                    "file_size": 0,
                    "error": "Arquivo de saida nao encontrado apos download.",
                }

        file_size = os.path.getsize(output_path)
        duration = await _get_duration(output_path)

        logger.info(
            f"Clipe baixado: {os.path.basename(output_path)} "
            f"({file_size / 1024 / 1024:.1f}MB, {duration:.1f}s)"
        )

        return {
            "success": True,
            "path": output_path,
            "duration": duration,
            "file_size": file_size,
            "error": None,
        }

    except asyncio.TimeoutError:
        logger.error(f"Timeout ({timeout_seconds}s) ao baixar: {url}")
        return {
            "success": False,
            "path": None,
            "duration": 0,
            "file_size": 0,
            "error": f"Timeout apos {timeout_seconds}s",
        }
    except FileNotFoundError:
        logger.error("yt-dlp nao encontrado. Instale com: pip install yt-dlp")
        return {
            "success": False,
            "path": None,
            "duration": 0,
            "file_size": 0,
            "error": "yt-dlp nao instalado.",
        }
    except Exception as e:
        logger.error(f"Erro inesperado no download: {e}", exc_info=True)
        return {
            "success": False,
            "path": None,
            "duration": 0,
            "file_size": 0,
            "error": str(e),
        }


async def _get_duration(file_path: str) -> float:
    """
    Obtem a duracao de um arquivo de video usando ffprobe.
    Retorna 0.0 se falhar.
    """
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            file_path,
        ]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=15)

        if process.returncode == 0:
            info = json.loads(stdout.decode("utf-8", errors="replace"))
            return float(info.get("format", {}).get("duration", 0))
    except Exception as e:
        logger.warning(f"Nao foi possivel obter duracao de {file_path}: {e}")

    return 0.0


async def download_job_clips(job_id: int) -> Dict[str, Any]:
    """
    Baixa todos os clipes de um ClipJob.
    Atualiza o status do job para 'downloading' e depois para o proximo passo.
    """
    clip_urls, clip_metadata = _start_download_job(job_id)
    if clip_urls is None:
        return {"success": False, "local_paths": [], "total_duration": 0, "errors": ["Job nao encontrado."]}

    if not clip_urls:
        _fail_job(job_id, "Nenhuma URL de clipe no job.")
        return {"success": False, "local_paths": [], "total_duration": 0, "errors": ["Sem URLs."]}

    local_paths = []
    total_duration = 0.0
    errors = []

    for i, url in enumerate(clip_urls):
        title = clip_metadata[i].get("title", f"clip_{i}") if i < len(clip_metadata) else f"clip_{i}"
        output_path = _build_output_path(job_id, i, title)
        result = await download_clip(url, output_path)

        if result["success"]:
            local_paths.append(result["path"])
            total_duration += result.get("duration", 0)
        else:
            errors.append(f"Clip {i} ({url}): {result['error']}")

        _update_job_progress(job_id, i + 1, len(clip_urls))

    _finalize_job_download(job_id, local_paths, total_duration, errors)

    logger.info(
        f"Job #{job_id}: {len(local_paths)}/{len(clip_urls)} clipes baixados. "
        f"Duracao total: {total_duration:.1f}s"
    )
    return {
        "success": len(local_paths) > 0,
        "local_paths": local_paths,
        "total_duration": total_duration,
        "errors": errors,
    }


def _start_download_job(job_id: int):
    """Marca o job como downloading e retorna (clip_urls, clip_metadata) ou (None, None)."""
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if not job:
            logger.error(f"Job #{job_id} nao encontrado em _start_download_job.")
            return None, None
        clip_urls = job.clip_urls or []
        clip_metadata = job.clip_metadata or []
        job.status = "downloading"
        job.started_at = datetime.now(timezone.utc)
        job.current_step = f"Baixando {len(clip_urls)} clipe(s)..."
        db.commit()
    return clip_urls, clip_metadata


def _update_job_progress(job_id: int, current: int, total: int) -> None:
    """Atualiza o progresso de download no banco (Weight: 0-25%)."""
    progress = int((current / total) * 25)
    with safe_session() as db:
        j = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if j:
            j.progress_pct = progress
            j.current_step = f"Baixando clipe {current}/{total}..."
            db.commit()


def _finalize_job_download(
    job_id: int, local_paths: List[str], total_duration: float, errors: List[str]
) -> None:
    """Atualiza o job com os resultados finais do download."""
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if not job:
            logger.error(f"Job #{job_id} nao encontrado em _finalize_job_download.")
            return
        job.clip_local_paths = local_paths
        if local_paths:
            job.status = "transcribing"
            job.current_step = "Download concluido. Aguardando transcricao."
            job.duration_seconds = total_duration
        else:
            job.status = "failed"
            job.error_message = " | ".join(errors)
            job.current_step = "Falha no download de todos os clipes."
        db.commit()


def _fail_job(job_id: int, error: str):
    """Marca um job como falhado."""
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = error
            job.current_step = "Falha."
            db.commit()
    logger.error(f"Job #{job_id} falhado: {error}")
