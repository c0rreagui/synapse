"""
Clipper Stitcher - Costura de Clipes
=====================================

Concatenacao de clipes processados com crossfade suave.
O chunking de ~90s no monitor.py garante que os clipes ja possuem
duracao adequada, dispensando padding artificial.

Estrategias:
    1. Clipe unico -> passthrough (copia direta)
    2. Multiplos clipes -> crossfade de 0.5s entre eles
    3. Fallback -> concat simples (corte seco)

Requisitos:
    - FFmpeg com libx264 no PATH
"""

import os
import uuid
import asyncio
import json
import logging
import shutil
import time
from hashlib import md5
from typing import List, Optional, Dict, Any

from core.config import DATA_DIR

logger = logging.getLogger("ClipperStitcher")

# Diretorios
OUTPUT_DIR = os.path.join(DATA_DIR, "clipper", "output")
ASSETS_DIR = os.path.join(DATA_DIR, "clipper", "assets")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# Configuracao
CROSSFADE_DURATION = 0.5       # Duracao do crossfade entre clipes

# Encoding
VIDEO_BITRATE = "5M"
CRF = "20"
PRESET = "medium"


async def _get_duration(file_path: str) -> float:
    """Obtem duracao de um video via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
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
        data = json.loads(stdout.decode("utf-8", errors="replace"))
        return float(data.get("format", {}).get("duration", 0))

    return 0.0




async def crossfade_two_clips(
    clip1_path: str,
    clip2_path: str,
    output_path: str,
    fade_duration: float = CROSSFADE_DURATION,
    timeout_seconds: int = 300,
) -> Dict[str, Any]:
    """
    Costura dois clipes com crossfade de audio e video.

    Args:
        clip1_path: Primeiro clipe
        clip2_path: Segundo clipe
        output_path: Caminho de saida
        fade_duration: Duracao do crossfade em segundos
        timeout_seconds: Timeout maximo

    Returns:
        Dict com: success, output_path, duration, error
    """
    if not os.path.exists(clip1_path):
        return _error_result(f"Clipe 1 nao encontrado: {clip1_path}")
    if not os.path.exists(clip2_path):
        return _error_result(f"Clipe 2 nao encontrado: {clip2_path}")

    # Obter duracao do primeiro clipe para calcular offset do crossfade
    clip1_dur = await _get_duration(clip1_path)
    if clip1_dur <= fade_duration:
        return _error_result(f"Clipe 1 muito curto ({clip1_dur:.1f}s) para crossfade de {fade_duration}s")

    offset = clip1_dur - fade_duration

    # Filtro complexo: xfade (video) + acrossfade (audio)
    filter_complex = (
        f"[0:v][1:v]xfade=transition=fade:duration={fade_duration}:offset={offset}[v];"
        f"[0:a][1:a]acrossfade=d={fade_duration}:c1=tri:c2=tri[a]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", clip1_path,
        "-i", clip2_path,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", PRESET,
        "-crf", CRF,
        "-b:v", VIDEO_BITRATE,
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]

    logger.info(
        f"Crossfade: {os.path.basename(clip1_path)} + {os.path.basename(clip2_path)} "
        f"(offset={offset:.1f}s, fade={fade_duration}s)"
    )

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        _, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        process.kill()
        if os.path.exists(output_path):
            os.remove(output_path)
        return _error_result(f"FFmpeg crossfade timeout apos {timeout_seconds}s")

    if process.returncode != 0:
        error = stderr.decode("utf-8", errors="replace").strip()
        error_lines = error.split("\n")[-5:]
        if os.path.exists(output_path):
            os.remove(output_path)
        return _error_result(f"FFmpeg crossfade falhou: {' | '.join(error_lines)}")

    if not os.path.exists(output_path):
        return _error_result("Arquivo de saida do crossfade nao gerado.")

    duration = await _get_duration(output_path)
    file_size = os.path.getsize(output_path)

    logger.info(f"Crossfade concluido: {duration:.1f}s, {file_size / 1024 / 1024:.1f}MB")

    return {
        "success": True,
        "output_path": output_path,
        "duration": duration,
        "file_size": file_size,
        "error": None,
    }


async def concat_simple(
    clip_paths: List[str],
    output_path: str,
    timeout_seconds: int = 300,
) -> Dict[str, Any]:
    """
    Concatena clips sem crossfade (corte seco).
    Usado como fallback se crossfade falhar.
    """
    if not clip_paths:
        return _error_result("Nenhum clipe para concatenar.")

    import uuid
    # Criar concat file (aleatorio para evitar race conditions em H20)
    concat_file = os.path.join(OUTPUT_DIR, f"_concat_list_{uuid.uuid4().hex[:8]}.txt")
    with open(concat_file, "w", encoding="utf-8") as f:
        for path in clip_paths:
            safe = path.replace("\\", "/").replace("'", "\\'")
            f.write(f"file '{safe}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c:v", "libx264",
        "-preset", PRESET,
        "-crf", CRF,
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        _, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        process.kill()
        _cleanup(concat_file)
        return _error_result(f"FFmpeg concat timeout apos {timeout_seconds}s")

    _cleanup(concat_file)

    if process.returncode != 0:
        error = stderr.decode("utf-8", errors="replace").strip()
        return _error_result(f"FFmpeg concat falhou: {error[-300:]}")

    if not os.path.exists(output_path):
        return _error_result("Arquivo concatenado nao gerado.")

    duration = await _get_duration(output_path)
    return {
        "success": True,
        "output_path": output_path,
        "duration": duration,
        "file_size": os.path.getsize(output_path),
        "error": None,
    }


async def ensure_minimum_duration(
    edited_clips: List[str],
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Pipeline principal do stitcher.
    Como os clipes agora sao agrupados em chunks de ~90s na origem,
    nao precisamos mais de padding artificial (telas pretas).
    Apenas fazemos o crossfade se houver multiplos clipes.

    Args:
        edited_clips: Lista de caminhos dos clipes ja editados em 9:16
        output_path: Caminho de saida final

    Returns:
        Dict com: success, output_path, duration, strategy, error
    """
    if not edited_clips:
        return _error_result("Nenhum clipe editado fornecido.")

    # Filtrar clipes que existem
    valid_clips = [c for c in edited_clips if os.path.exists(c)]
    if not valid_clips:
        return _error_result("Nenhum clipe editado encontrado no disco.")

    # Calcular duracoes
    durations = []
    for clip in valid_clips:
        dur = await _get_duration(clip)
        durations.append(dur)

    total_duration = sum(durations)

    if output_path is None:
        unique_id = uuid.uuid4().hex[:12]

        base_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        exports_dir = os.path.join(base_backend_dir, "data", "exports")
        os.makedirs(exports_dir, exist_ok=True)

        output_path = os.path.join(exports_dir, f"stitch_{unique_id}.mp4")

    logger.info(
        f"Stitcher: {len(valid_clips)} clipe(s), "
        f"duracao total estimada={total_duration:.1f}s"
    )

    # Estrategia 1: Clipe unico, ja e o resultado final
    if len(valid_clips) == 1:
        logger.info("Estrategia: Clipe unico. Nenhuma costura necessaria.")
        try:
            shutil.copy2(valid_clips[0], output_path)
        except (OSError, IOError) as e:
            return _error_result(f"Falha ao copiar clipe unico: {e}")
        return _success_result(output_path, total_duration, "single_clip")

    # Estrategia 2: Multiplos clipes, usar crossfade
    logger.info("Estrategia: Crossfade entre multiplos clipes.")
    result = await _stitch_with_crossfade(valid_clips, output_path)
    if result["success"]:
        return {**result, "strategy": "crossfade"}
    
    # Fallback se crossfade falhar
    logger.warning(f"Crossfade falhou: {result['error']}. Tentando concat simples...")
    result = await concat_simple(valid_clips, output_path)
    if result["success"]:
        return {**result, "strategy": "concat_simple"}
        
    return result


async def _stitch_with_crossfade(clips: List[str], output_path: str) -> Dict[str, Any]:
    """Costura todos os clipes com crossfade sequencial."""
    if len(clips) < 2:
        return _error_result("Precisa de pelo menos 2 clipes para crossfade.")

    # Crossfade sequencial: clip1 + clip2 -> temp, temp + clip3 -> temp2, ...
    current = clips[0]
    for i in range(1, len(clips)):
        # uuid4 garante unicidade mesmo em jobs paralelos (evita collision de _stitch_temp_N.mp4)
        temp_suffix = uuid.uuid4().hex[:8]
        temp_out = os.path.join(OUTPUT_DIR, f"_stitch_temp_{temp_suffix}.mp4")
        is_last = (i == len(clips) - 1)
        final_out = output_path if is_last else temp_out

        result = await crossfade_two_clips(current, clips[i], final_out)
        if not result["success"]:
            _cleanup(temp_out)
            return result

        # Limpar intermediario anterior (exceto o input original)
        if current != clips[0] and current != clips[i]:
            _cleanup(current)

        current = final_out

    duration = await _get_duration(output_path)
    return {
        "success": True,
        "output_path": output_path,
        "duration": duration,
        "file_size": os.path.getsize(output_path),
        "error": None,
    }




def _success_result(output_path: str, duration: float, strategy: str) -> Dict[str, Any]:
    """Resultado padrao de sucesso."""
    return {
        "success": True,
        "output_path": output_path,
        "duration": duration,
        "file_size": os.path.getsize(output_path) if os.path.exists(output_path) else 0,
        "strategy": strategy,
        "error": None,
    }


def _error_result(error: str) -> Dict[str, Any]:
    """Resultado padrao de erro."""
    logger.error(f"Stitcher: {error}")
    return {
        "success": False,
        "output_path": None,
        "duration": 0,
        "file_size": 0,
        "strategy": None,
        "error": error,
    }


def _cleanup(path: str) -> None:
    """Remove arquivo temporario, logando se houver erro de permissao."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError as exc:
        logger.warning(f"Stitcher: nao foi possivel remover temp file {path!r}: {exc}")
