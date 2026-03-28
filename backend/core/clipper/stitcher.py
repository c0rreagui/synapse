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
import random
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

# Configuracao (com variação anti-fingerprint)
CROSSFADE_DURATION = 0.5       # Base — variado em runtime via _rand_crossfade()
def _rand_crossfade():
    return round(random.uniform(0.35, 0.65), 2)

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
        try:
            data = json.loads(stdout.decode("utf-8", errors="replace"))
            return float(data.get("format", {}).get("duration", 0))
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"ffprobe JSON parse failed for {file_path}: {e}")
            return 0.0

    return 0.0




async def _has_audio_stream(file_path: str) -> bool:
    """Verifica se um video possui stream de audio."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-select_streams", "a",
        "-show_entries", "stream=codec_type",
        "-of", "csv=p=0",
        file_path,
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await asyncio.wait_for(process.communicate(), timeout=10)
    return bool(stdout.decode().strip())


async def crossfade_two_clips(
    clip1_path: str,
    clip2_path: str,
    output_path: str,
    fade_duration: float = None,
    timeout_seconds: int = 300,
) -> Dict[str, Any]:
    if fade_duration is None:
        fade_duration = _rand_crossfade()
    """
    Costura dois clipes com crossfade de audio e video.
    Resiliente a clips sem audio ou com audio incompativel.
    """
    if not os.path.exists(clip1_path):
        return _error_result(f"Clipe 1 nao encontrado: {clip1_path}")
    if not os.path.exists(clip2_path):
        return _error_result(f"Clipe 2 nao encontrado: {clip2_path}")

    # Obter duracoes
    clip1_dur = await _get_duration(clip1_path)
    clip2_dur = await _get_duration(clip2_path)
    if clip1_dur <= fade_duration:
        return _error_result(f"Clipe 1 muito curto ({clip1_dur:.1f}s) para crossfade de {fade_duration}s")
    if clip2_dur <= fade_duration:
        return _error_result(f"Clipe 2 muito curto ({clip2_dur:.1f}s) para crossfade de {fade_duration}s")

    offset = clip1_dur - fade_duration

    # Verificar audio em ambos os clips
    has_audio1 = await _has_audio_stream(clip1_path)
    has_audio2 = await _has_audio_stream(clip2_path)

    # Construir filtro adaptativo baseado na disponibilidade de audio
    if has_audio1 and has_audio2:
        # Ambos tem audio: normalizar formato antes do crossfade
        filter_complex = (
            f"[0:v]settb=1/60,setpts=PTS-STARTPTS[v0];"
            f"[1:v]settb=1/60,setpts=PTS-STARTPTS[v1];"
            f"[v0][v1]xfade=transition=fade:duration={fade_duration}:offset={offset}[v];"
            f"[0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[a0];"
            f"[1:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[a1];"
            f"[a0][a1]acrossfade=d={fade_duration}:c1=tri:c2=tri[a]"
        )
    elif has_audio1 or has_audio2:
        # Apenas um tem audio: gerar silencio pro outro
        if has_audio1:
            filter_complex = (
                f"[0:v]settb=1/60,setpts=PTS-STARTPTS[v0];"
                f"[1:v]settb=1/60,setpts=PTS-STARTPTS[v1];"
                f"[v0][v1]xfade=transition=fade:duration={fade_duration}:offset={offset}[v];"
                f"[0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[a0];"
                f"anullsrc=channel_layout=stereo:sample_rate=44100[silent];"
                f"[silent]atrim=0:{clip2_dur}[a1];"
                f"[a0][a1]acrossfade=d={fade_duration}:c1=tri:c2=tri[a]"
            )
        else:
            filter_complex = (
                f"[0:v]settb=1/60,setpts=PTS-STARTPTS[v0];"
                f"[1:v]settb=1/60,setpts=PTS-STARTPTS[v1];"
                f"[v0][v1]xfade=transition=fade:duration={fade_duration}:offset={offset}[v];"
                f"anullsrc=channel_layout=stereo:sample_rate=44100[silent];"
                f"[silent]atrim=0:{clip1_dur}[a0];"
                f"[1:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[a1];"
                f"[a0][a1]acrossfade=d={fade_duration}:c1=tri:c2=tri[a]"
            )
        logger.warning("Crossfade: audio ausente em um dos clips, gerando silencio")
    else:
        # Nenhum tem audio: crossfade apenas video, gerar audio silencioso
        total_dur = clip1_dur + clip2_dur - fade_duration
        filter_complex = (
            f"[0:v]settb=1/60,setpts=PTS-STARTPTS[v0];"
            f"[1:v]settb=1/60,setpts=PTS-STARTPTS[v1];"
            f"[v0][v1]xfade=transition=fade:duration={fade_duration}:offset={offset}[v];"
            f"anullsrc=channel_layout=stereo:sample_rate=44100,atrim=0:{total_dur}[a]"
        )
        logger.warning("Crossfade: nenhum clip tem audio, gerando silencio total")

    cmd = [
        "ffmpeg", "-y",
        "-i", clip1_path,
        "-i", clip2_path,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level:v", "4.1",
        "-preset", PRESET,
        "-crf", CRF,
        "-b:v", VIDEO_BITRATE,
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-map_metadata", "-1",
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
        _cleanup(output_path)
        return _error_result(f"FFmpeg crossfade timeout apos {timeout_seconds}s")
    except Exception:
        process.kill()
        _cleanup(output_path)
        raise

    if process.returncode != 0:
        error = stderr.decode("utf-8", errors="replace").strip()
        error_lines = error.split("\n")[-5:]
        _cleanup(output_path)
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
        "-profile:v", "high",
        "-level:v", "4.1",
        "-preset", PRESET,
        "-crf", CRF,
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-map_metadata", "-1",
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
    except Exception:
        process.kill()
        _cleanup(concat_file)
        raise

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
        effective_clip_dur = max(clip_dur, 1)
        # Clip muito curto para crossfade, usar concat simples
        reps = int(target_duration / effective_clip_dur) + 2
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

    try:
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
                temp_files.clear()
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
        return trim_result
    finally:
        # Cleanup todos os temps
        for tf in temp_files:
            if tf != output_path:
                _cleanup(tf)


async def _apply_loop_tail(
    clip_path: str,
    output_path: str,
    crossfade_sec: float = 1.5,
    timeout_seconds: int = 300,
) -> Dict[str, Any]:
    """
    Blend in-place para loop pixel-perfect no TikTok.

    Em vez de appendar o início ao final (que duplica frames), substituímos
    os últimos `crossfade_sec` do vídeo por um blend gradual:
      - No início da zona de transição: 100% vídeo original (final)
      - No final da zona de transição: 100% início do vídeo (primeiros frames)

    Resultado: o último frame do output é visualmente idêntico ao primeiro.
    Quando o TikTok reinicia automaticamente, a emenda é imperceptível.

    O vídeo mantém a mesma duração — nenhum frame extra é adicionado.
    """
    clip_dur = await _get_duration(clip_path)

    if clip_dur < crossfade_sec * 3:
        # Vídeo muito curto para blend seguro — cópia direta
        shutil.copy2(clip_path, output_path)
        dur = await _get_duration(output_path)
        return _success_result(output_path, dur, "loop_tail_fallback")

    # Limitar crossfade a no máximo 10% da duração do vídeo
    cf = min(crossfade_sec, clip_dur * 0.10)
    cf = max(cf, 0.5)  # Mínimo 0.5s para ser perceptível
    body_end = clip_dur - cf

    # FFmpeg filter_complex em passo único:
    # 1. Separa o vídeo em BODY (0..dur-cf) e TAIL (dur-cf..dur)
    # 2. Extrai HEAD (0..cf) e aplica fade-in de alpha (transparente → opaco)
    # 3. Overlay HEAD sobre TAIL → zona de blend
    # 4. Concat BODY + BLEND → output com mesma duração
    # 5. Áudio: body_audio + crossfade(tail_audio, head_audio)
    filter_complex = (
        # Vídeo: split em 3 cópias
        f"[0:v]split=3[body_src][tail_src][head_src];"

        # BODY: do início até o ponto de transição
        f"[body_src]trim=0:{body_end:.4f},setpts=PTS-STARTPTS[body_v];"

        # TAIL: os últimos cf segundos (base da zona de blend)
        f"[tail_src]trim={body_end:.4f}:{clip_dur:.4f},setpts=PTS-STARTPTS[tail_v];"

        # HEAD: os primeiros cf segundos, com alpha fade-in (0→1)
        # Isso faz o início "aparecer" gradualmente sobre o final
        f"[head_src]trim=0:{cf:.4f},setpts=PTS-STARTPTS,"
        f"format=yuva420p,fade=t=in:st=0:d={cf:.4f}:alpha=1[head_fade];"

        # Overlay: HEAD (com alpha crescente) sobre TAIL
        # No t=0: alpha=0 → 100% TAIL (final do vídeo)
        # No t=cf: alpha=1 → 100% HEAD (início do vídeo)
        f"[tail_v]format=yuva420p[tail_rgba];"
        f"[tail_rgba][head_fade]overlay=format=auto,format=yuv420p[blend_v];"

        # Concatenar BODY + BLEND
        f"[body_v][blend_v]concat=n=2:v=1:a=0[v_out];"

        # Áudio: mesma lógica — body_audio + crossfade de tail/head
        f"[0:a]atrim=0:{body_end:.4f},asetpts=PTS-STARTPTS[body_a];"
        f"[0:a]atrim={body_end:.4f}:{clip_dur:.4f},asetpts=PTS-STARTPTS[tail_a];"
        f"[0:a]atrim=0:{cf:.4f},asetpts=PTS-STARTPTS[head_a];"
        f"[tail_a][head_a]acrossfade=d={cf:.4f}:c1=tri:c2=tri[blend_a];"
        f"[body_a][blend_a]concat=n=2:v=0:a=1[a_out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", clip_path,
        "-filter_complex", filter_complex,
        "-map", "[v_out]",
        "-map", "[a_out]",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level:v", "4.1",
        "-preset", PRESET,
        "-crf", CRF,
        "-b:v", VIDEO_BITRATE,
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-map_metadata", "-1",
        "-movflags", "+faststart",
        output_path,
    ]

    logger.info(
        f"LoopTail pixel-perfect: dur={clip_dur:.1f}s, cf={cf:.2f}s, "
        f"body=0-{body_end:.1f}s, blend zone={body_end:.1f}-{clip_dur:.1f}s"
    )

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    try:
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        proc.kill()
        _cleanup(output_path)
        # Fallback: cópia direta
        shutil.copy2(clip_path, output_path)
        dur = await _get_duration(output_path)
        return _success_result(output_path, dur, "loop_tail_fallback")

    if proc.returncode != 0:
        error = stderr.decode("utf-8", errors="replace").strip()
        error_lines = error.split("\n")[-5:]
        logger.warning(f"LoopTail blend falhou: {' | '.join(error_lines)}")
        _cleanup(output_path)
        # Fallback: cópia direta
        shutil.copy2(clip_path, output_path)
        dur = await _get_duration(output_path)
        return _success_result(output_path, dur, "loop_tail_fallback")

    if not os.path.exists(output_path):
        shutil.copy2(clip_path, output_path)
        dur = await _get_duration(output_path)
        return _success_result(output_path, dur, "loop_tail_fallback")

    duration = await _get_duration(output_path)
    file_size = os.path.getsize(output_path)
    logger.info(f"LoopTail pixel-perfect concluído: {duration:.1f}s, {file_size / 1024 / 1024:.1f}MB")

    return {
        "success": True,
        "output_path": output_path,
        "duration": duration,
        "file_size": file_size,
        "strategy": "loop_tail",
        "error": None,
    }


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
        "-c:v", "libx264", "-profile:v", "high", "-level:v", "4.1",
        "-preset", PRESET, "-crf", CRF,
        "-b:v", VIDEO_BITRATE,
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-map_metadata", "-1",
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
