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
import json
import logging
import random
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

# Proporcao facecam vs gameplay (default 40/60)
FACECAM_RATIO = 0.40   # 40% do frame = facecam
GAMEPLAY_RATIO = 0.60   # 60% do frame = gameplay

FACECAM_HEIGHT = int(FINAL_HEIGHT * FACECAM_RATIO)   # 768
GAMEPLAY_HEIGHT = int(FINAL_HEIGHT * GAMEPLAY_RATIO)  # 1152

# Anti-shadowban: presets de proporção sorteados por job
FACECAM_RATIO_PRESETS = [
    (0.30, 0.70),  # Gameplay dominante
    (0.40, 0.60),  # Padrão equilibrado
    (0.50, 0.50),  # Split igual
]

# Encoding TikTok-friendly (com leve variação anti-fingerprint)
def _randomized_encoding():
    """Retorna parâmetros de encoding com variação sutil para cada vídeo."""
    crf = str(random.randint(19, 22))
    bitrate_k = random.randint(4500, 5500)
    video_br = f"{bitrate_k}k"
    audio_br = random.choice(["192k", "196k", "188k"])
    preset = random.choice(["medium", "medium", "slow"])  # 66% medium, 33% slow
    return crf, video_br, audio_br, preset

VIDEO_BITRATE = "5M"
AUDIO_BITRATE = "192k"
PRESET = "medium"
CRF = "20"


# ── Ken Burns: Zoom dinâmico para layouts estáticos ──────────────────
# Cria movimento sutil onde a câmera seria fixa (podcast/street).
# Técnica: scale para 8% maior → crop animado que encolhe → rescale para final.
KB_ZOOM = 1.08     # 8% extra de headroom para o zoom
KB_RATE = 25       # Segundos para atingir zoom máximo (depois estabiliza)


def _ken_burns_filters() -> str:
    """
    Fragmento FFmpeg para efeito Ken Burns (zoom-in lento).
    Substitui o 'scale=1080:1920' final nos layouts podcast/street.
    Expressões entre aspas simples protegem vírgulas do parser FFmpeg.
    """
    kb_w = int(FINAL_WIDTH * KB_ZOOM)    # 1166
    kb_h = int(FINAL_HEIGHT * KB_ZOOM)   # 2074
    dw = kb_w - FINAL_WIDTH              # 86
    dh = kb_h - FINAL_HEIGHT             # 154
    dx = dw // 2                          # 43
    dy = dh // 2                          # 77

    return (
        f"scale={kb_w}:{kb_h}:flags=lanczos,"
        f"crop="
        f"w='{kb_w}-{dw}*min(t/{KB_RATE},1)':"
        f"h='{kb_h}-{dh}*min(t/{KB_RATE},1)':"
        f"x='{dx}*min(t/{KB_RATE},1)':"
        f"y='{dy}*min(t/{KB_RATE},1)',"
        f"scale={FINAL_WIDTH}:{FINAL_HEIGHT}:flags=lanczos"
    )


# ── Anti-Shadowban: Fingerprint Evasion ──────────────────────────────
# Micro-variações imperceptíveis que destroem hash matching das plataformas.
# Cada job gera params únicos para que nenhum vídeo exportado seja idêntico.

ASB_SPEED_RANGE = (1.01, 1.04)   # Variação de velocidade (imperceptível)
ASB_GRAIN_RANGE = (1, 3)         # Intensidade do noise overlay

ASB_COLOR_PRESETS = [
    "eq=contrast=1.03:saturation=0.98:brightness=0.01",   # quente-contrastado
    "eq=contrast=0.97:saturation=1.03:brightness=-0.01",   # frio-saturado
    "eq=contrast=1.02:saturation=1.02:brightness=0.02",   # vibrante-claro
    "eq=contrast=1.01:saturation=0.96:brightness=0.00",   # suave-desaturado
    "eq=contrast=0.99:saturation=1.04:brightness=-0.02",   # saturado-escuro
]


def generate_asb_params() -> Dict[str, Any]:
    """Gera parâmetros anti-shadowban aleatórios. Chamar UMA VEZ por job."""
    ratio = random.choice(FACECAM_RATIO_PRESETS)
    return {
        "speed": round(random.uniform(*ASB_SPEED_RANGE), 3),
        "grain": random.randint(*ASB_GRAIN_RANGE),
        "color_idx": random.randint(0, len(ASB_COLOR_PRESETS) - 1),
        "facecam_ratio": ratio[0],
        "gameplay_ratio": ratio[1],
    }


def _apply_antishadowban(
    filter_str: str,
    output_label: str,
    speed: float,
    grain: int,
    color_idx: int,
) -> Tuple[str, str]:
    """
    Encadeia filtros anti-shadowban no final do filter_complex.
    - setpts: altera velocidade do vídeo (quebra hash temporal)
    - noise: grain aleatório (quebra hash de pixels)
    - eq: color grading sutil (quebra assinatura visual)
    Retorna (novo_filter_str, novo_output_label).
    """
    color = ASB_COLOR_PRESETS[color_idx % len(ASB_COLOR_PRESETS)]
    extra = [
        f"{output_label}setpts=(PTS-STARTPTS)/{speed}[_asb_spd]",
        f"[_asb_spd]noise=c0s={grain}:c1s={grain}:c2s={grain}:allf=t+u[_asb_grn]",
        f"[_asb_grn]{color}[_asb_out]",
    ]
    return filter_str + ";\n" + ";\n".join(extra), "[_asb_out]"


def _build_edit_filter_facecam(
    source_width: int,
    source_height: int,
    ass_path: Optional[str],
    facecam_box: Tuple[int, int, int, int],
    cam_ratio: float = FACECAM_RATIO,
    game_ratio: float = GAMEPLAY_RATIO,
) -> tuple:
    """
    Layout COM facecam: Facecam no topo + Gameplay na base.
    Proporção variável via cam_ratio/game_ratio (anti-shadowban).
    Facecam flutua sobre background desfocado da gameplay.
    """
    cam_h = int(FINAL_HEIGHT * cam_ratio)
    game_h = FINAL_HEIGHT - cam_h  # Garantir que soma = 1920 exato

    facecam_x, facecam_y, facecam_src_w, facecam_src_h = facecam_box
    logger.info(
        f"Facecam crop (vision): x={facecam_x} y={facecam_y} w={facecam_src_w} h={facecam_src_h} "
        f"| ratio={cam_ratio:.0%}/{game_ratio:.0%}"
    )

    # Facecam foreground: escalar proporcionalmente à altura disponível
    cam_fg_w = int(900 * (cam_ratio / 0.40))  # Escala relativa ao padrão 40%
    cam_fg_w = min(cam_fg_w, FINAL_WIDTH - 40)  # Margem mínima lateral

    # Gameplay: regiao maior, centro do frame
    gameplay_src_h = int(source_height * 0.75)
    gameplay_src_w = int(gameplay_src_h * (FINAL_WIDTH / game_h))
    gameplay_src_w = min(gameplay_src_w, source_width)
    gameplay_x = (source_width - gameplay_src_w) // 2
    gameplay_y = (source_height - gameplay_src_h) // 2

    filter_parts = [
        f"[0:v]split=3[cam_src][game_bg_src][game_base_src]",

        # Background do Topo: blur + escurecimento
        f"[game_bg_src]scale={FINAL_WIDTH}:{cam_h}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={FINAL_WIDTH}:{cam_h},"
        f"gblur=sigma=20,"
        f"colorchannelmixer=rr=0.4:gg=0.4:bb=0.4[top_bg]",

        # Facecam foreground
        f"[cam_src]crop={facecam_src_w}:{facecam_src_h}:{facecam_x}:{facecam_y},"
        f"scale={cam_fg_w}:-1:flags=lanczos[cam_fg]",

        # Sobrepor facecam no bg
        f"[top_bg][cam_fg]overlay=(W-w)/2:(H-h)/2[top_final]",

        # Gameplay base
        f"[game_base_src]crop={gameplay_src_w}:{gameplay_src_h}:{gameplay_x}:{gameplay_y},"
        f"scale={FINAL_WIDTH}:{game_h}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={FINAL_WIDTH}:{game_h}[base_final]",

        # Empilhar verticalmente
        f"[top_final][base_final]vstack=inputs=2[stacked]",
    ]

    if ass_path:
        safe_path = ass_path.replace("\\", "/").replace(":", "\\:")
        filter_parts.append(f"[stacked]ass='{safe_path}'[final]")
        output_label = "[final]"
    else:
        output_label = "[stacked]"

    return ";\n".join(filter_parts), output_label


def _build_edit_filter_gameplay_only(
    source_width: int,
    source_height: int,
    ass_path: Optional[str],
) -> tuple:
    """
    Layout SEM facecam (gameplay pura): center-crop 9:16 da gameplay inteira.
    Ideal para clips sem webcam (ex: Rocket League, gameplay full-screen).

    Layout final (1080x1920):
    ┌──────────────────┐
    │                  │
    │  GAMEPLAY FULL   │
    │  (center crop    │
    │   9:16 do frame) │
    │                  │
    │   LEGENDAS .ass  │
    └──────────────────┘
    """
    logger.info("Layout GAMEPLAY-ONLY: sem facecam detectada, usando center-crop 9:16")

    # Calcular crop 9:16 do centro do frame source
    # Queremos manter a maior area possivel em aspecto 9:16
    target_ratio = FINAL_WIDTH / FINAL_HEIGHT  # 0.5625

    source_ratio = source_width / source_height
    if source_ratio > target_ratio:
        # Source mais largo que 9:16: crop horizontal (manter altura, cortar lados)
        crop_h = source_height
        crop_w = int(source_height * target_ratio)
    else:
        # Source mais alto que 9:16: crop vertical (manter largura, cortar topo/base)
        crop_w = source_width
        crop_h = int(source_width / target_ratio)

    crop_x = (source_width - crop_w) // 2
    crop_y = (source_height - crop_h) // 2

    filter_parts = [
        # Center crop para 9:16 + scale para resolucao final
        f"[0:v]crop={crop_w}:{crop_h}:{crop_x}:{crop_y},"
        f"scale={FINAL_WIDTH}:{FINAL_HEIGHT}:flags=lanczos[scaled]",
    ]

    if ass_path:
        safe_path = ass_path.replace("\\", "/").replace(":", "\\:")
        filter_parts.append(f"[scaled]ass='{safe_path}'[final]")
        output_label = "[final]"
    else:
        output_label = "[scaled]"

    return ";\n".join(filter_parts), output_label


def _build_edit_filter_podcast(
    source_width: int,
    source_height: int,
    ass_path: Optional[str],
    facecam_box: Optional[Tuple[int, int, int, int]] = None,
) -> tuple:
    """
    Layout PODCAST (Just Chatting): Fullscreen centrado no rosto do streamer.
    Sem split-screen. O streamer ocupa a tela toda com blur lateral.

    Layout final (1080x1920):
    ┌──────────────────┐
    │   BLUR LATERAL   │
    │  ┌────────────┐  │
    │  │  STREAMER   │  │
    │  │  (centrado  │  │
    │  │  no rosto)  │  │
    │  └────────────┘  │
    │   LEGENDAS .ass  │
    └──────────────────┘
    """
    logger.info("Layout PODCAST: fullscreen centrado no rosto, blur lateral")

    target_ratio = FINAL_WIDTH / FINAL_HEIGHT  # 0.5625

    if facecam_box:
        # Centralizar crop no rosto detectado
        fx, fy, fw, fh = facecam_box
        face_cx = fx + fw // 2
        face_cy = fy + fh // 2

        # Crop 9:16 centrado no rosto, usando a maior area possivel
        crop_h = source_height
        crop_w = int(crop_h * target_ratio)
        if crop_w > source_width:
            crop_w = source_width
            crop_h = int(crop_w / target_ratio)

        crop_x = max(0, min(face_cx - crop_w // 2, source_width - crop_w))
        crop_y = max(0, min(face_cy - crop_h // 2, source_height - crop_h))
    else:
        # Sem rosto: center-crop padrão
        crop_h = source_height
        crop_w = int(crop_h * target_ratio)
        if crop_w > source_width:
            crop_w = source_width
            crop_h = int(crop_w / target_ratio)
        crop_x = (source_width - crop_w) // 2
        crop_y = (source_height - crop_h) // 2

    filter_parts = [
        # Blur background (fullscreen)
        f"[0:v]scale={FINAL_WIDTH}:{FINAL_HEIGHT}:force_original_aspect_ratio=increase:flags=fast_bilinear,"
        f"crop={FINAL_WIDTH}:{FINAL_HEIGHT},"
        f"gblur=sigma=30,"
        f"colorchannelmixer=rr=0.3:gg=0.3:bb=0.3[bg]",

        # Crop centrado no rosto + Ken Burns zoom-in
        f"[0:v]crop={crop_w}:{crop_h}:{crop_x}:{crop_y},"
        f"{_ken_burns_filters()}[fg]",

        # Sobrepor foreground no background
        f"[bg][fg]overlay=0:0[composed]",
    ]

    if ass_path:
        safe_path = ass_path.replace("\\", "/").replace(":", "\\:")
        filter_parts.append(f"[composed]ass='{safe_path}'[final]")
        output_label = "[final]"
    else:
        output_label = "[composed]"

    return ";\n".join(filter_parts), output_label


def _build_edit_filter_street(
    source_width: int,
    source_height: int,
    ass_path: Optional[str],
    facecam_box: Optional[Tuple[int, int, int, int]] = None,
) -> tuple:
    """
    Layout STREET (IRL): Fullscreen com contexto expandido ao redor do streamer.
    Mostra mais cenário/ambiente, crop mais aberto.

    Layout final (1080x1920):
    ┌──────────────────┐
    │   LEGENDAS .ass  │  <- topo (não cobrir ação)
    │                  │
    │  CENÁRIO + STREAM│
    │  (crop expandido │
    │   contexto max)  │
    │                  │
    └──────────────────┘
    """
    logger.info("Layout STREET (IRL): fullscreen com contexto expandido")

    target_ratio = FINAL_WIDTH / FINAL_HEIGHT

    if facecam_box:
        fx, fy, fw, fh = facecam_box
        face_cx = fx + fw // 2

        # Crop mais aberto: centralizar horizontalmente no rosto mas manter max vertical
        crop_h = source_height
        crop_w = int(crop_h * target_ratio)
        if crop_w > source_width:
            crop_w = source_width
            crop_h = int(crop_w / target_ratio)

        crop_x = max(0, min(face_cx - crop_w // 2, source_width - crop_w))
        crop_y = 0  # Manter topo do frame (contexto de rua)
    else:
        crop_h = source_height
        crop_w = int(crop_h * target_ratio)
        if crop_w > source_width:
            crop_w = source_width
            crop_h = int(crop_w / target_ratio)
        crop_x = (source_width - crop_w) // 2
        crop_y = 0

    filter_parts = [
        # Ken Burns zoom-in para criar movimento em cenas IRL estáticas
        f"[0:v]crop={crop_w}:{crop_h}:{crop_x}:{crop_y},"
        f"{_ken_burns_filters()}[scaled]",
    ]

    if ass_path:
        safe_path = ass_path.replace("\\", "/").replace(":", "\\:")
        # Legendas no TOPO para IRL (não cobrir ação na parte inferior)
        filter_parts.append(f"[scaled]ass='{safe_path}'[final]")
        output_label = "[final]"
    else:
        output_label = "[scaled]"

    return ";\n".join(filter_parts), output_label


def _build_edit_filter(
    source_width: int,
    source_height: int,
    ass_path: Optional[str] = None,
    facecam_box: Optional[Tuple[int, int, int, int]] = None,
    layout_mode: str = "gameplay",
    cam_ratio: float = FACECAM_RATIO,
    game_ratio: float = GAMEPLAY_RATIO,
) -> tuple:
    """
    Router: escolhe o layout correto baseado no layout_mode.
    - podcast: fullscreen centrado no rosto (Just Chatting)
    - street: fullscreen contexto expandido (IRL)
    - gameplay: split facecam + gameplay (proporção variável)
    """
    if layout_mode == "podcast":
        return _build_edit_filter_podcast(source_width, source_height, ass_path, facecam_box)
    elif layout_mode == "street":
        return _build_edit_filter_street(source_width, source_height, ass_path, facecam_box)
    elif facecam_box:
        return _build_edit_filter_facecam(
            source_width, source_height, ass_path, facecam_box,
            cam_ratio=cam_ratio, game_ratio=game_ratio,
        )
    else:
        return _build_edit_filter_gameplay_only(source_width, source_height, ass_path)


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
    layout_mode: str = "gameplay",
    asb_params: Optional[Dict[str, Any]] = None,
    clip_title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Processa um unico clipe: recorta facecam/gameplay, verticaliza 9:16,
    e "queima" legendas .ass no video.

    Args:
        video_path: Caminho do video fonte (tipicamente 16:9)
        ass_path: Caminho do arquivo .ass (opcional)
        output_path: Caminho de saida (opcional, gera em OUTPUT_DIR)
        timeout_seconds: Timeout maximo para o FFmpeg
        asb_params: Anti-shadowban params (de generate_asb_params()). None = gerar auto.
        clip_title: Titulo do clip para metadados do MP4.

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
    logger.info(f"Analisando video (layout_mode={layout_mode})...")
    facecam_box = detect_facecam_box(video_path, channel_name=channel_name)

    # ── Anti-Shadowban: params ──
    if asb_params is None:
        asb_params = generate_asb_params()

    asb_speed = asb_params["speed"]
    asb_grain = asb_params["grain"]
    asb_color = asb_params["color_idx"]
    cam_ratio = asb_params.get("facecam_ratio", FACECAM_RATIO)
    game_ratio = asb_params.get("gameplay_ratio", GAMEPLAY_RATIO)

    # Construir filtro FFmpeg baseado no layout_mode (com proporção variável)
    filter_str, output_label = _build_edit_filter(
        source_w, source_h, ass_path, facecam_box, layout_mode,
        cam_ratio=cam_ratio, game_ratio=game_ratio,
    )

    filter_str, output_label = _apply_antishadowban(
        filter_str, output_label, asb_speed, asb_grain, asb_color
    )

    # Audio: atempo compensa a variação de speed + loudnorm para TikTok
    af_filter = f"asetpts=PTS-STARTPTS,atempo={asb_speed},loudnorm=I=-14:LRA=11:TP=-1.5"

    logger.info(
        f"ASB: speed={asb_speed}x, grain={asb_grain}, "
        f"color={asb_color}, ratio={cam_ratio:.0%}/{game_ratio:.0%}, "
        f"title={'yes' if clip_title else 'no'}"
    )

    # Encoding com variação anti-fingerprint
    r_crf, r_vbr, r_abr, r_preset = _randomized_encoding()

    # Comando FFmpeg
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-filter_complex", filter_str,
        "-map", output_label,
        "-map", "0:a?",           # Audio original (se existir)
        "-af", af_filter,
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level:v", "4.1",
        "-preset", r_preset,
        "-crf", r_crf,
        "-r", "60",
        "-fps_mode", "cfr",
        "-b:v", r_vbr,
        "-maxrate", r_vbr,
        "-bufsize", "10M",
        "-c:a", "aac",
        "-b:a", r_abr,
        "-ar", "44100",
        "-map_metadata", "-1",
        "-movflags", "+faststart",  # Otimiza para streaming
        "-pix_fmt", "yuv420p",      # Compatibilidade maxima (iOS Safari)
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
        if output_path and os.path.exists(output_path):
            os.remove(output_path)
        return _error_result(f"FFmpeg timeout apos {timeout_seconds}s")

    if process.returncode != 0:
        error_log = stderr.decode("utf-8", errors="replace").strip()
        # Pegar as ultimas 5 linhas do log de erro
        error_lines = error_log.split("\n")[-5:]
        if output_path and os.path.exists(output_path):
            os.remove(output_path)
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
