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




async def create_seamless_loop(
    clip_path: str,
    target_duration: float,
    output_path: str,
    crossfade_sec: float = 0.8,
    timeout_seconds: int = 600,
) -> Dict[str, Any]:
    """
    Cria um loop infinito suave de um clipe até atingir target_duration.

    Estratégia:
    1. Calcula quantas iterações completas + parcial são necessárias
    2. Cria um concat com N cópias do clipe
    3. Aplica crossfade entre cada junção para transição seamless
    4. Trim final para target_duration exato

    O crossfade entre o final e o início de cada repetição cria a ilusão
    de loop contínuo. No TikTok, quando o vídeo reinicia automaticamente,
    o espectador não percebe a emenda.
    """
    if not os.path.exists(clip_path):
        return _error_result(f"Clip não encontrado: {clip_path}")

    clip_dur = await _get_duration(clip_path)
    if clip_dur <= 0:
        return _error_result(f"Clip com duração inválida: {clip_dur}")

    if clip_dur >= target_duration:
        # Clip já é longo o suficiente — aplica loop-back nos últimos segundos
        return await _apply_loop_tail(clip_path, output_path, crossfade_sec, timeout_seconds)

    # Quantas cópias completas precisamos (com margem para crossfade)
    effective_clip_dur = clip_dur - crossfade_sec  # Cada junção "come" crossfade_sec
    if effective_clip_dur <= 0:
        # Clip muito curto para crossfade, usar concat simples
        reps = int(target_duration / clip_dur) + 2
        clip_list = [clip_path] * reps
        concat_result = await concat_simple(clip_list, output_path, timeout_seconds)
        if concat_result["success"]:
            return await _trim_to_duration(output_path, target_duration, timeout_seconds)
        return concat_result

    reps_needed = int(target_duration / effective_clip_dur) + 2  # +2 para margem
    reps_needed = min(reps_needed, 20)  # Safety cap

    logger.info(
        f"SeamlessLoop: clip={clip_dur:.1f}s, target={target_duration:.1f}s, "
        f"reps={reps_needed}, crossfade={crossfade_sec}s"
    )

    # Costura sequencial com crossfade entre cada iteração
    current = clip_path
    temp_files = []

    for i in range(1, reps_needed):
        temp_suffix = uuid.uuid4().hex[:8]
        temp_out = os.path.join(OUTPUT_DIR, f"_loop_temp_{temp_suffix}.mp4")
        temp_files.append(temp_out)

        result = await crossfade_two_clips(
            current, clip_path, temp_out,
            fade_duration=crossfade_sec,
            timeout_seconds=timeout_seconds,
        )

        if not result["success"]:
            # Fallback: concat simples se crossfade falhar
            logger.warning(f"SeamlessLoop crossfade falhou na rep {i}, tentando concat simples")
            for tf in temp_files:
                _cleanup(tf)
            clip_list = [clip_path] * reps_needed
            concat_result = await concat_simple(clip_list, output_path, timeout_seconds)
            if concat_result["success"]:
                return await _trim_to_duration(output_path, target_duration, timeout_seconds)
            return concat_result

        # Limpar intermediário anterior (nunca o input original)
        if current != clip_path:
            _cleanup(current)

        current = temp_out

        # Checar se já atingiu duração suficiente
        current_dur = await _get_duration(current)
        if current_dur >= target_duration + crossfade_sec:
            break

    # Trim para duração exata
    trim_result = await _trim_to_duration(current, target_duration, timeout_seconds, output_path)

    # Cleanup todos os temps
    for tf in temp_files:
        if tf != output_path:
            _cleanup(tf)

    return trim_result


async def _apply_loop_tail(
    clip_path: str,
    output_path: str,
    crossfade_sec: float = 0.8,
    timeout_seconds: int = 300,
) -> Dict[str, Any]:
    """
    Para clips que já são longos o suficiente: aplica um crossfade
    entre os últimos frames e os primeiros frames, criando a ilusão
    de loop quando o TikTok reinicia o vídeo.

    Extrai os primeiros crossfade_sec*2 do clip e faz crossfade com o final.
    """
    clip_dur = await _get_duration(clip_path)

    # Extrair os primeiros 2s do clip como "tail connector"
    tail_dur = min(crossfade_sec * 2.5, clip_dur * 0.15)  # Max 15% do clip
    tail_dur = max(tail_dur, crossfade_sec + 0.5)

    tail_path = os.path.join(OUTPUT_DIR, f"_loop_tail_{uuid.uuid4().hex[:8]}.mp4")

    # Extrair início do clip
    cmd_extract = [
        "ffmpeg", "-y",
        "-i", clip_path,
        "-t", str(tail_dur),
        "-c:v", "libx264", "-preset", PRESET, "-crf", CRF,
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        tail_path,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd_extract, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        await asyncio.wait_for(proc.communicate(), timeout=60)
    except asyncio.TimeoutError:
        _cleanup(tail_path)
        # Fallback: cópia direta
        shutil.copy2(clip_path, output_path)
        dur = await _get_duration(output_path)
        return _success_result(output_path, dur, "loop_tail_fallback")

    if proc.returncode != 0 or not os.path.exists(tail_path):
        shutil.copy2(clip_path, output_path)
        dur = await _get_duration(output_path)
        return _success_result(output_path, dur, "loop_tail_fallback")

    # Crossfade: clip principal + tail (início do clip)
    result = await crossfade_two_clips(
        clip_path, tail_path, output_path,
        fade_duration=crossfade_sec,
        timeout_seconds=timeout_seconds,
    )

    _cleanup(tail_path)

    if result["success"]:
        result["strategy"] = "loop_tail"
        return result

    # Fallback
    shutil.copy2(clip_path, output_path)
    dur = await _get_duration(output_path)
    return _success_result(output_path, dur, "loop_tail_fallback")


async def _trim_to_duration(
    input_path: str,
    target_duration: float,
    timeout_seconds: int = 120,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Corta um vídeo para a duração exata com re-encode suave."""
    current_dur = await _get_duration(input_path)

    # Se já está na duração certa (±0.5s), retorna como está
    if abs(current_dur - target_duration) <= 0.5:
        if output_path and output_path != input_path:
            shutil.copy2(input_path, output_path)
            return _success_result(output_path, current_dur, "seamless_loop")
        return _success_result(input_path, current_dur, "seamless_loop")

    if output_path is None:
        output_path = input_path  # Overwrite

    trim_path = os.path.join(OUTPUT_DIR, f"_trim_{uuid.uuid4().hex[:8]}.mp4")

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-t", f"{target_duration:.2f}",
        "-c:v", "libx264", "-preset", PRESET, "-crf", CRF,
        "-b:v", VIDEO_BITRATE,
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        trim_path,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        _cleanup(trim_path)
        return _error_result(f"Trim timeout após {timeout_seconds}s")

    if proc.returncode != 0:
        _cleanup(trim_path)
        error = stderr.decode("utf-8", errors="replace")[-300:]
        return _error_result(f"Trim falhou: {error}")

    # Mover para output final
    if output_path != trim_path:
        shutil.move(trim_path, output_path)

    duration = await _get_duration(output_path)
    return _success_result(output_path, duration, "seamless_loop")


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
