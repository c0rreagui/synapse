"""
Clipper Editor - Orquestrador FFmpeg para Montagem 9:16
========================================================

Recebe video(s) bruto(s) de stream (tipicamente 16:9) e produz
um video vertical 9:16 com:
    - Facecam (50% do frame)
        * Fundo: gameplay desfocada e escurecida
        * Frente: webcam em aspect-ratio original flutuando centralizada
    - Gameplay recortada na base (50% do frame)
    - Legenda .ass "queimada" (hardcoded) no video
    - Codec H.264 otimizado para TikTok/Shorts

Layout final (1080x1920):
    ┌──────────────────┐
    │   FACECAM (50%)  │  <- 1080x960, Scale-to-Fill + crop
    ├──────────────────┤
    │  GAMEPLAY (50%)  │  <- 1080x960, Scale-to-Fill + crop
    ├──────────────────┤
    │   LEGENDAS .ass  │  <- Overlay via filtro "ass"
    └──────────────────┘

Requisitos:
    - FFmpeg compilado com libass, libx264
    - FFmpeg no PATH
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, Tuple

from core.config import DATA_DIR
from .vision import detect_facecam_box

logger = logging.getLogger("ClipperEditor")

# Diretorios
OUTPUT_DIR = os.path.join(DATA_DIR, "clipper", "output")
TEMP_DIR = os.path.join(DATA_DIR, "clipper", "temp")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Dimensoes do frame final (TikTok/Shorts 9:16)
FINAL_WIDTH = 1080
FINAL_HEIGHT = 1920

# Proporcao facecam vs gameplay (40/60)
FACECAM_RATIO = 0.40   # 40% do frame = facecam
GAMEPLAY_RATIO = 0.60   # 60% do frame = gameplay

FACECAM_HEIGHT = int(FINAL_HEIGHT * FACECAM_RATIO)   # 960
GAMEPLAY_HEIGHT = int(FINAL_HEIGHT * GAMEPLAY_RATIO)  # 960

# Encoding TikTok-friendly
VIDEO_BITRATE = "5M"
AUDIO_BITRATE = "192k"
PRESET = "medium"  # Balance velocidade/qualidade
CRF = "20"


def _build_edit_filter(
    source_width: int,
    source_height: int,
    ass_path: Optional[str] = None,
    facecam_box: Optional[Tuple[int, int, int, int]] = None,
) -> str:
    """
    Constroi o filtro complexo FFmpeg para layout 9:16.

    O filtro:
    1. Cria duas copias do input
    2. Crop da facecam (regiao superior central, tipicamente onde fica a webcam)
    3. Crop da gameplay (regiao inferior central ou full frame)
    4. Escala ambos para largura 1080
    5. Empilha verticalmente
    6. Overlay do .ass se fornecido
    """
    # Calcular crop regions do source (assumindo 16:9)
    if facecam_box:
        facecam_x, facecam_y, facecam_src_w, facecam_src_h = facecam_box
        logger.info(f"Usando facecam crop dinamica (vision): x={facecam_x} y={facecam_y} w={facecam_src_w} h={facecam_src_h}")
    else:
        # Facecam: canto superior, pegar regiao quadrada central (top 40% do source)
        logger.info("Usando facecam crop estatica (fallback)")
        facecam_src_h = int(source_height * 0.45)
        facecam_src_w = int(facecam_src_h * (FINAL_WIDTH / FACECAM_HEIGHT))
        facecam_src_w = min(facecam_src_w, source_width)
        facecam_x = (source_width - facecam_src_w) // 2
        facecam_y = 0  # Topo do frame source

    # Gameplay: regiao maior, centro do frame
    gameplay_src_h = int(source_height * 0.75)
    gameplay_src_w = int(gameplay_src_h * (FINAL_WIDTH / GAMEPLAY_HEIGHT))
    gameplay_src_w = min(gameplay_src_w, source_width)
    gameplay_x = (source_width - gameplay_src_w) // 2
    gameplay_y = (source_height - gameplay_src_h) // 2

    filter_parts = [
        # Split input em 3 streams: cam original, background do topo, gameplay da base
        f"[0:v]split=3[cam_src][game_bg_src][game_base_src]",
        
        # 1. Background do Topo: Gameplay escalada pra preencher, crop, blur forte e escurecimento
        f"[game_bg_src]scale={FINAL_WIDTH}:{FACECAM_HEIGHT}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={FINAL_WIDTH}:{FACECAM_HEIGHT},"
        f"gblur=sigma=20,"
        f"colorchannelmixer=rr=0.4:gg=0.4:bb=0.4[top_bg]",
        
        # 2. Facecam Dinamica (Foreground): Crop natural expandido do MTCNN + escala segura min/max
        f"[cam_src]crop={facecam_src_w}:{facecam_src_h}:{facecam_x}:{facecam_y},"
        f"scale=900:-1:flags=lanczos[cam_fg]",
        
        # 3. Sobrepor Facecam no bg desfocado (Centralizado no Topo)
        f"[top_bg][cam_fg]overlay=(W-w)/2:(H-h)/2[top_final]",
        
        # 4. Gameplay Base: Scale-to-Fill (preenche sem bordas)
        f"[game_base_src]crop={gameplay_src_w}:{gameplay_src_h}:{gameplay_x}:{gameplay_y},"
        f"scale={FINAL_WIDTH}:{GAMEPLAY_HEIGHT}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={FINAL_WIDTH}:{GAMEPLAY_HEIGHT}[base_final]",
        
        # 5. Empilhar verticalmente Topo + Base
        f"[top_final][base_final]vstack=inputs=2[stacked]",
    ]

    # Overlay de legendas .ass
    if ass_path:
        # Escapar path para Windows (backslashes -> forward slashes, : -> \\:)
        safe_path = ass_path.replace("\\", "/").replace(":", "\\:")
        filter_parts.append(f"[stacked]ass='{safe_path}'[final]")
        output_label = "[final]"
    else:
        output_label = "[stacked]"

    filter_str = ";\n".join(filter_parts)
    return filter_str, output_label


async def _probe_video(video_path: str) -> Dict[str, Any]:
    """
    Obtem informacoes do video via ffprobe.
    Retorna dict com: width, height, duration, codec, fps
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        video_path,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=15)

    if process.returncode != 0:
        error = stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"ffprobe falhou para {video_path}: {error[:200]}")

    import json
    data = json.loads(stdout.decode("utf-8", errors="replace"))

    # Encontrar stream de video
    video_stream = None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            video_stream = stream
            break

    if not video_stream:
        raise RuntimeError(f"Nenhum stream de video encontrado em {video_path}")

    fmt = data.get("format", {})

    # Parsear FPS de r_frame_rate (ex: "30/1" ou "30000/1001")
    fps_str = video_stream.get("r_frame_rate", "30/1")
    fps_parts = fps_str.split("/")
    fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0

    return {
        "width": int(video_stream.get("width", 1920)),
        "height": int(video_stream.get("height", 1080)),
        "duration": float(fmt.get("duration", 0)),
        "codec": video_stream.get("codec_name", "unknown"),
        "fps": round(fps, 2),
    }


async def edit_clip(
    video_path: str,
    ass_path: Optional[str] = None,
    output_path: Optional[str] = None,
    timeout_seconds: int = 300,
    channel_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Processa um unico clipe: recorta facecam/gameplay, verticaliza 9:16,
    e "queima" legendas .ass no video.

    Args:
        video_path: Caminho do video fonte (tipicamente 16:9)
        ass_path: Caminho do arquivo .ass (opcional)
        output_path: Caminho de saida (opcional, gera em OUTPUT_DIR)
        timeout_seconds: Timeout maximo para o FFmpeg

    Returns:
        Dict com: success, output_path, duration, file_size, error
    """
    if not os.path.exists(video_path):
        return _error_result(f"Video fonte nao encontrado: {video_path}")

    if ass_path and not os.path.exists(ass_path):
        logger.warning(f"Arquivo .ass nao encontrado: {ass_path}. Editando sem legendas.")
        ass_path = None

    # Probar video source para obter dimensoes
    try:
        probe = await _probe_video(video_path)
    except RuntimeError as e:
        return _error_result(str(e))

    source_w = probe["width"]
    source_h = probe["height"]

    logger.info(
        f"Editando: {os.path.basename(video_path)} "
        f"({source_w}x{source_h}, {probe['duration']:.1f}s, {probe['fps']}fps)"
    )

    # Gerar output path
    if output_path is None:
        base = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(OUTPUT_DIR, f"{base}_9x16.mp4")

    # Analise visual para buscar a facecam
    logger.info("Analisando video para deteccao dinamica da facecam...")
    facecam_box = detect_facecam_box(video_path, channel_name=channel_name)

    # Construir filtro FFmpeg
    filter_str, output_label = _build_edit_filter(source_w, source_h, ass_path, facecam_box)

    # Comando FFmpeg
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-filter_complex", filter_str,
        "-map", output_label,
        "-map", "0:a?",           # Audio original (se existir)
        "-af", "loudnorm=I=-14:LRA=11:TP=-1.5",  # Masterizacao TikTok
        "-c:v", "libx264",
        "-preset", PRESET,
        "-crf", CRF,
        "-b:v", VIDEO_BITRATE,
        "-maxrate", VIDEO_BITRATE,
        "-bufsize", "10M",
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        "-ar", "44100",
        "-movflags", "+faststart",  # Otimiza para streaming
        "-pix_fmt", "yuv420p",      # Compatibilidade maxima
        output_path,
    ]

    logger.info(f"FFmpeg: Processando {os.path.basename(video_path)}...")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        _, stderr = await asyncio.wait_for(
            process.communicate(), timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        process.kill()
        return _error_result(f"FFmpeg timeout apos {timeout_seconds}s")

    if process.returncode != 0:
        error_log = stderr.decode("utf-8", errors="replace").strip()
        # Pegar as ultimas 5 linhas do log de erro
        error_lines = error_log.split("\n")[-5:]
        return _error_result(f"FFmpeg exit code {process.returncode}: {' | '.join(error_lines)}")

    if not os.path.exists(output_path):
        return _error_result("Arquivo de saida nao gerado pelo FFmpeg.")

    file_size = os.path.getsize(output_path)
    if file_size < 10000:  # <10KB provavelmente corrompido
        return _error_result(f"Arquivo de saida muito pequeno ({file_size} bytes), possivelmente corrompido.")

    # Probar output
    try:
        out_probe = await _probe_video(output_path)
        duration = out_probe["duration"]
    except Exception:
        duration = 0.0

    logger.info(
        f"Edicao concluida: {os.path.basename(output_path)} "
        f"({file_size / 1024 / 1024:.1f}MB, {duration:.1f}s, {FINAL_WIDTH}x{FINAL_HEIGHT})"
    )

    return {
        "success": True,
        "output_path": output_path,
        "duration": duration,
        "file_size": file_size,
        "resolution": f"{FINAL_WIDTH}x{FINAL_HEIGHT}",
        "error": None,
    }


def _error_result(error: str) -> Dict[str, Any]:
    """Retorna resultado padrao de erro."""
    logger.error(f"Editor: {error}")
    return {
        "success": False,
        "output_path": None,
        "duration": 0,
        "file_size": 0,
        "resolution": None,
        "error": error,
    }
