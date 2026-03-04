"""
Clipper Stitcher - Costura de Clipes para Garantir >60 Segundos
================================================================

Logica de concatenacao de clipes processados para atingir o threshold
de 60s exigido pelo Programa de Recompensas do TikTok.

Estrategias:
    1. Se soma dos clipes >= 65s -> usa os clipes ja editados sem costura
    2. Se 2+ clipes editados -> crossfade de 0.5s entre eles
    3. Se apenas 1 clipe < 65s -> adiciona padding (hook intro + CTA final)

Requisitos:
    - FFmpeg com libx264 no PATH
"""

import os
import asyncio
import logging
from typing import List, Optional, Dict, Any

from core.config import DATA_DIR

logger = logging.getLogger("ClipperStitcher")

# Diretorios
OUTPUT_DIR = os.path.join(DATA_DIR, "clipper", "output")
ASSETS_DIR = os.path.join(DATA_DIR, "clipper", "assets")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# Configuracao
MIN_DURATION_SECONDS = 65.0    # Margem de seguranca sobre os 60s do TikTok
CROSSFADE_DURATION = 0.5       # Duracao do crossfade entre clipes
HOOK_DURATION = 4.0            # Duracao do padding de intro
CTA_DURATION = 4.0             # Duracao do padding de CTA final

# Encoding
VIDEO_BITRATE = "5M"
CRF = "20"
PRESET = "medium"

# Cores para padding (borders/backgrounds)
HOOK_BG_COLOR = "0x111111"     # Fundo escuro
CTA_BG_COLOR = "0x111111"

# Texto para hooks e CTAs gerados automaticamente
DEFAULT_HOOK_TEXT = "VOCE PRECISA VER ISSO"
DEFAULT_CTA_TEXT = "SEGUE PRA MAIS CORTES"


async def _get_duration(file_path: str) -> float:
    """Obtem duracao de um video via ffprobe."""
    import json as json_lib

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
        data = json_lib.loads(stdout.decode("utf-8", errors="replace"))
        return float(data.get("format", {}).get("duration", 0))

    return 0.0


async def generate_padding_clip(
    text: str,
    duration: float,
    output_path: str,
    width: int = 1080,
    height: int = 1920,
    bg_color: str = HOOK_BG_COLOR,
    font_size: int = 60,
) -> bool:
    """
    Gera um clipe de padding (hook/CTA) com texto centralizado sobre
    fundo escuro usando FFmpeg.

    Returns:
        True se gerado com sucesso, False caso contrario.
    """
    # Escapar texto para FFmpeg drawtext
    safe_text = text.replace("'", "\\'").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={bg_color}:s={width}x{height}:d={duration}:r=30",
        "-f", "lavfi",
        "-i", f"anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t", str(duration),
        "-vf", (
            f"drawtext=text='{safe_text}':"
            f"fontsize={font_size}:fontcolor=white:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"font=Arial:borderw=3:bordercolor=black"
        ),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await asyncio.wait_for(process.communicate(), timeout=30)

    if process.returncode != 0:
        error = stderr.decode("utf-8", errors="replace").strip()
        logger.error(f"Falha ao gerar padding: {error[:200]}")
        return False

    return os.path.exists(output_path)


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
        return _error_result(f"FFmpeg crossfade timeout apos {timeout_seconds}s")

    if process.returncode != 0:
        error = stderr.decode("utf-8", errors="replace").strip()
        error_lines = error.split("\n")[-5:]
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

    # Criar concat file
    concat_file = os.path.join(OUTPUT_DIR, "_concat_list.txt")
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
    min_duration: float = MIN_DURATION_SECONDS,
    hook_text: str = DEFAULT_HOOK_TEXT,
    cta_text: str = DEFAULT_CTA_TEXT,
) -> Dict[str, Any]:
    """
    Pipeline principal do stitcher. Garante que o video final >= min_duration.

    Estrategia:
        1. Calcula duracao total dos clipes editados
        2. Se >= min_duration: retorna o primeiro clipe (ou concat se multiplos)
        3. Se < min_duration e 2+ clipes: crossfade entre eles
        4. Se < min_duration e 1 clipe: adiciona hook + CTA padding

    Args:
        edited_clips: Lista de caminhos dos clipes ja editados em 9:16
        output_path: Caminho de saida final
        min_duration: Duracao minima em segundos (default 65s)
        hook_text: Texto para o padding de intro
        cta_text: Texto para o padding de CTA

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
        from hashlib import md5
        import time
        hash_str = md5(str(time.time()).encode()).hexdigest()[:8]
        
        # Use dynamic EXPORTS directory instead of old OUTPUT_DIR
        base_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        exports_dir = os.path.join(base_backend_dir, "data", "exports")
        os.makedirs(exports_dir, exist_ok=True)
        
        output_path = os.path.join(exports_dir, f"stitch_{hash_str}.mp4")

    logger.info(
        f"Stitcher: {len(valid_clips)} clipe(s), "
        f"duracao total={total_duration:.1f}s (min={min_duration}s)"
    )

    # Estrategia 1: Duracao suficiente com um unico clipe
    if len(valid_clips) == 1 and total_duration >= min_duration:
        logger.info("Estrategia: Clipe unico >= min_duration. Sem costura necessaria.")
        # Copiar para output_path
        import shutil
        shutil.copy2(valid_clips[0], output_path)
        return _success_result(output_path, total_duration, "single_clip")

    # Estrategia 2: Multiplos clipes, usar crossfade
    if len(valid_clips) >= 2:
        logger.info("Estrategia: Crossfade entre multiplos clipes.")
        result = await _stitch_with_crossfade(valid_clips, output_path)
        if result["success"]:
            if result["duration"] >= min_duration:
                return {**result, "strategy": "crossfade"}
            # Crossfade nao foi suficiente, tentar adicionar padding
            logger.info("Crossfade insuficiente. Adicionando padding...")
            return await _add_padding_to_clip(
                result["output_path"], output_path, min_duration, hook_text, cta_text
            )
        # Crossfade falhou, tentar concat simples
        logger.warning(f"Crossfade falhou: {result['error']}. Tentando concat simples...")
        result = await concat_simple(valid_clips, output_path)
        if result["success"]:
            return {**result, "strategy": "concat_simple"}
        return result

    # Estrategia 3: Um clipe < min_duration, adicionar padding
    logger.info("Estrategia: Clipe unico curto. Adicionando hook + CTA padding.")
    return await _add_padding_to_clip(
        valid_clips[0], output_path, min_duration, hook_text, cta_text
    )


async def _stitch_with_crossfade(clips: List[str], output_path: str) -> Dict[str, Any]:
    """Costura todos os clipes com crossfade sequencial."""
    if len(clips) < 2:
        return _error_result("Precisa de pelo menos 2 clipes para crossfade.")

    # Crossfade sequencial: clip1 + clip2 -> temp, temp + clip3 -> temp2, ...
    current = clips[0]
    for i in range(1, len(clips)):
        temp_out = os.path.join(OUTPUT_DIR, f"_stitch_temp_{i}.mp4")
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


async def _add_padding_to_clip(
    clip_path: str,
    output_path: str,
    min_duration: float,
    hook_text: str,
    cta_text: str,
) -> Dict[str, Any]:
    """Adiciona hook no inicio e CTA no final para atingir min_duration."""
    clip_dur = await _get_duration(clip_path)
    deficit = min_duration - clip_dur

    if deficit <= 0:
        # Ja atinge min_duration, copiar
        import shutil
        shutil.copy2(clip_path, output_path)
        return _success_result(output_path, clip_dur, "no_padding_needed")

    # Dividir deficit entre hook e CTA
    hook_dur = min(HOOK_DURATION, deficit * 0.5)
    cta_dur = min(CTA_DURATION, deficit - hook_dur)

    # Se ainda nao cobrir, aumentar ambos proporcionalmente
    if hook_dur + cta_dur < deficit:
        extra = deficit - hook_dur - cta_dur
        hook_dur += extra * 0.5
        cta_dur += extra * 0.5

    clips_to_concat = []

    # Gerar hook
    if hook_dur >= 1.0:
        hook_path = os.path.join(OUTPUT_DIR, "_hook_padding.mp4")
        ok = await generate_padding_clip(hook_text, hook_dur, hook_path)
        if ok:
            clips_to_concat.append(hook_path)
        else:
            logger.warning("Falha ao gerar hook padding. Continuando sem hook.")

    # Clipe principal
    clips_to_concat.append(clip_path)

    # Gerar CTA
    if cta_dur >= 1.0:
        cta_path = os.path.join(OUTPUT_DIR, "_cta_padding.mp4")
        ok = await generate_padding_clip(cta_text, cta_dur, cta_path)
        if ok:
            clips_to_concat.append(cta_path)
        else:
            logger.warning("Falha ao gerar CTA padding. Continuando sem CTA.")

    if len(clips_to_concat) <= 1:
        # Nenhum padding gerado, retornar clipe original
        import shutil
        shutil.copy2(clip_path, output_path)
        return _success_result(output_path, clip_dur, "padding_failed_fallback")

    # Concatenar tudo
    result = await concat_simple(clips_to_concat, output_path)

    # Limpar temporarios de padding
    for p in clips_to_concat:
        if p != clip_path:
            _cleanup(p)

    if result["success"]:
        return {**result, "strategy": "hook_cta_padding"}

    return result


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
    """Remove arquivo temporario silenciosamente."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass
