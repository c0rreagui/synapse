"""
Uniquifier — Gerador de Variantes Únicas por Perfil (Anti-Duplicate Detection)
================================================================================

Recebe um vídeo já editado (9:16, com legendas queimadas) e gera N variantes
únicas — uma por perfil TikTok — para que a plataforma classifique cada upload
como conteúdo original.

Cada variante recebe uma combinação determinística de transforms:
    - Sub-pixel crop + rescale (quebra pHash espacial)
    - Micro-speed variation (quebra hash temporal)
    - Color micro-grade (quebra assinatura visual)
    - Noise pattern único (altera pixels frame a frame)
    - Micro-tempo + pitch shift audio (quebra Chromaprint)
    - Lowpass variation (altera high-freq fingerprint)
    - Encoding params únicos (CRF, bitrate, audio bitrate)
    - Metadata com timestamp único

Os params são gerados via seed determinística = hash(source_path + profile_slug),
garantindo reprodutibilidade e unicidade por perfil.
"""

import asyncio
import hashlib
import logging
import os
import random
import shutil
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from core.config import DATA_DIR

logger = logging.getLogger("Uniquifier")

VARIANTS_DIR = os.path.join(DATA_DIR, "clipper", "variants")
os.makedirs(VARIANTS_DIR, exist_ok=True)

# ── Ranges de variação (imperceptíveis ao olho/ouvido humano) ──────────

# Video
CROP_OFFSET_RANGE = (2, 6)       # pixels removidos por borda
SPEED_RANGE = (1.005, 1.035)     # variação de velocidade (stacks com ASB)
BRIGHTNESS_RANGE = (-0.02, 0.02)
CONTRAST_RANGE = (0.97, 1.03)
SATURATION_RANGE = (0.97, 1.03)
NOISE_RANGE = (1, 4)

# Audio
TEMPO_RANGE = (0.99, 1.01)
PITCH_RANGE = (0.998, 1.002)
LOWPASS_RANGE = (18000, 19500)   # Hz — afeta frequências inaudíveis

# Encoding
CRF_RANGE = (18, 23)
VIDEO_BITRATE_RANGE = (4200, 5800)  # kbps
AUDIO_BITRATE_RANGE = (186, 198)    # kbps

# Concurrency
DEFAULT_MAX_CONCURRENT = 2
DEFAULT_TIMEOUT_SECONDS = 180

# Output
FINAL_WIDTH = 1080
FINAL_HEIGHT = 1920

# Disk space
MIN_FREE_DISK_GB = 2  # Mínimo de espaço livre para gerar variantes


class InsufficientDiskError(Exception):
    """Disco insuficiente para gerar variantes únicas."""
    pass


def _check_disk_space(path: str = VARIANTS_DIR) -> float:
    """Retorna espaço livre em GB no filesystem do path."""
    usage = shutil.disk_usage(path)
    return usage.free / (1024 ** 3)


def _generate_variant_params(source_path: str, profile_slug: str, index: int) -> Dict[str, Any]:
    """
    Gera parâmetros de variação determinísticos para um par (source, profile).
    Mesma combinação sempre produz mesmos params (idempotente).
    """
    seed_str = f"{source_path}:{profile_slug}:{index}"
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    # Video transforms
    crop_dx = rng.randint(*CROP_OFFSET_RANGE)
    crop_dy = rng.randint(*CROP_OFFSET_RANGE)
    crop_ox = rng.randint(0, crop_dx // 2)
    crop_oy = rng.randint(0, crop_dy // 2)

    speed = round(rng.uniform(*SPEED_RANGE), 4)
    brightness = round(rng.uniform(*BRIGHTNESS_RANGE), 4)
    contrast = round(rng.uniform(*CONTRAST_RANGE), 4)
    saturation = round(rng.uniform(*SATURATION_RANGE), 4)
    noise_intensity = rng.randint(*NOISE_RANGE)

    # Invisible overlay: drawbox em posição única
    overlay_x = rng.randint(0, FINAL_WIDTH - 2)
    overlay_y = rng.randint(0, FINAL_HEIGHT - 2)

    # Audio transforms
    tempo = round(rng.uniform(*TEMPO_RANGE), 4)
    pitch = round(rng.uniform(*PITCH_RANGE), 4)
    lowpass_freq = rng.randint(*LOWPASS_RANGE)

    # Encoding
    crf = rng.randint(*CRF_RANGE)
    video_bitrate = rng.randint(*VIDEO_BITRATE_RANGE)
    audio_bitrate = rng.randint(*AUDIO_BITRATE_RANGE)
    preset = rng.choice(["medium", "medium", "slow"])

    # Metadata timestamp único (offset por index para garantir unicidade)
    fake_ts = datetime.now(timezone.utc) - timedelta(
        hours=rng.randint(1, 720),
        minutes=rng.randint(0, 59),
        seconds=rng.randint(0, 59),
    )

    return {
        "crop": {"dx": crop_dx, "dy": crop_dy, "ox": crop_ox, "oy": crop_oy},
        "speed": speed,
        "color": {"brightness": brightness, "contrast": contrast, "saturation": saturation},
        "noise": noise_intensity,
        "overlay": {"x": overlay_x, "y": overlay_y},
        "audio": {"tempo": tempo, "pitch": pitch, "lowpass": lowpass_freq},
        "encoding": {
            "crf": crf,
            "video_bitrate": f"{video_bitrate}k",
            "audio_bitrate": f"{audio_bitrate}k",
            "preset": preset,
        },
        "creation_time": fake_ts.isoformat(),
    }


def _build_ffmpeg_cmd(
    source_path: str,
    output_path: str,
    params: Dict[str, Any],
) -> List[str]:
    """Constrói o comando FFmpeg completo para gerar uma variante."""

    crop = params["crop"]
    speed = params["speed"]
    color = params["color"]
    noise = params["noise"]
    overlay = params["overlay"]
    audio = params["audio"]
    enc = params["encoding"]

    # ── Video filter chain ──
    vf_parts = [
        # 1. Sub-pixel crop (remove dx/dy pixels, offset ox/oy)
        f"crop=in_w-{crop['dx']}:in_h-{crop['dy']}:{crop['ox']}:{crop['oy']}",
        # Rescale back to target resolution
        f"scale={FINAL_WIDTH}:{FINAL_HEIGHT}:flags=lanczos",
        # 2. Micro-speed variation
        f"setpts=PTS/{speed}",
        # 3. Noise pattern
        f"noise=c0s={noise}:c1s={noise}:c2s={noise}:allf=t+u",
        # 4. Color micro-grade
        f"eq=brightness={color['brightness']}:contrast={color['contrast']}:saturation={color['saturation']}",
        # 5. Invisible overlay (1px transparent dot em posição única)
        f"drawbox=x={overlay['x']}:y={overlay['y']}:w=1:h=1:color=black@0.01:t=fill",
    ]
    vf = ",".join(vf_parts)

    # ── Audio filter chain ──
    af_parts = [
        # 1. Micro-tempo (compensa speed change + adiciona variação)
        f"atempo={audio['tempo']}",
        # 2. Pitch micro-shift via sample rate manipulation
        f"asetrate=44100*{audio['pitch']},aresample=44100",
        # 3. Lowpass variation (afeta apenas high-freq inaudíveis)
        f"lowpass=f={audio['lowpass']}",
    ]
    af = ",".join(af_parts)

    cmd = [
        "ffmpeg", "-y",
        "-i", source_path,
        "-vf", vf,
        "-af", af,
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level:v", "4.1",
        "-preset", enc["preset"],
        "-crf", str(enc["crf"]),
        "-r", "60",
        "-fps_mode", "cfr",
        "-b:v", enc["video_bitrate"],
        "-maxrate", enc["video_bitrate"],
        "-bufsize", "10M",
        "-c:a", "aac",
        "-b:a", enc["audio_bitrate"],
        "-ar", "44100",
        "-map_metadata", "-1",
        "-metadata", f"creation_time={params['creation_time']}",
        "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    return cmd


async def generate_variant(
    source_path: str,
    profile_slug: str,
    variant_index: int,
    output_dir: Optional[str] = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    """
    Gera uma variante única do vídeo fonte para um perfil específico.

    Returns:
        {
            "success": bool,
            "variant_path": str,
            "profile_slug": str,
            "params": dict,
            "file_size": int,
            "error": str | None,
        }
    """
    out_dir = output_dir or VARIANTS_DIR
    os.makedirs(out_dir, exist_ok=True)

    stem = os.path.splitext(os.path.basename(source_path))[0]
    output_path = os.path.join(out_dir, f"{stem}_var_{profile_slug}.mp4")

    params = _generate_variant_params(source_path, profile_slug, variant_index)
    cmd = _build_ffmpeg_cmd(source_path, output_path, params)

    logger.info(
        f"Uniquifier: Gerando variante para @{profile_slug} "
        f"(speed={params['speed']}, crop={params['crop']['dx']}px, "
        f"noise={params['noise']}, crf={params['encoding']['crf']})"
    )

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
            error_msg = stderr.decode(errors="replace")[-500:]
            logger.error(f"Uniquifier: FFmpeg falhou para @{profile_slug}: {error_msg}")
            return {
                "success": False,
                "variant_path": source_path,
                "profile_slug": profile_slug,
                "params": params,
                "file_size": 0,
                "error": error_msg,
            }

        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        logger.info(
            f"Uniquifier: Variante @{profile_slug} gerada "
            f"({file_size / 1024 / 1024:.1f} MB)"
        )

        return {
            "success": True,
            "variant_path": output_path,
            "profile_slug": profile_slug,
            "params": params,
            "file_size": file_size,
            "error": None,
        }

    except asyncio.TimeoutError:
        logger.error(f"Uniquifier: Timeout ({timeout_seconds}s) para @{profile_slug}")
        # Limpar arquivo parcial
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
        return {
            "success": False,
            "variant_path": source_path,
            "profile_slug": profile_slug,
            "params": params,
            "file_size": 0,
            "error": f"Timeout after {timeout_seconds}s",
        }

    except Exception as e:
        logger.error(f"Uniquifier: Exceção para @{profile_slug}: {e}")
        return {
            "success": False,
            "variant_path": source_path,
            "profile_slug": profile_slug,
            "params": params,
            "file_size": 0,
            "error": str(e),
        }


async def generate_variants(
    source_path: str,
    profile_slugs: List[str],
    output_dir: Optional[str] = None,
    max_concurrent: int = DEFAULT_MAX_CONCURRENT,
) -> List[Dict[str, Any]]:
    """
    Gera N variantes únicas do vídeo fonte, uma por profile.
    Usa asyncio.Semaphore para limitar FFmpeg concorrente.

    Se houver apenas 1 perfil, retorna o vídeo original sem re-encode.

    Returns:
        Lista de dicts com resultado de cada variante (mesma ordem de profile_slugs).
    """
    if not os.path.exists(source_path):
        logger.error(f"Uniquifier: Arquivo fonte não encontrado: {source_path}")
        return [
            {
                "success": False,
                "variant_path": source_path,
                "profile_slug": slug,
                "params": {},
                "file_size": 0,
                "error": "Source file not found",
            }
            for slug in profile_slugs
        ]

    # Perfil único: sem necessidade de variante
    if len(profile_slugs) == 1:
        logger.info("Uniquifier: Perfil único — retornando vídeo original")
        return [
            {
                "success": True,
                "variant_path": source_path,
                "profile_slug": profile_slugs[0],
                "params": {},
                "file_size": os.path.getsize(source_path),
                "error": None,
            }
        ]

    # ── Pre-flight disk check ──
    free_gb = _check_disk_space()
    if free_gb < MIN_FREE_DISK_GB:
        logger.warning(
            f"Uniquifier: Espaço livre insuficiente ({free_gb:.1f} GB). "
            f"Tentando liberar via GC..."
        )
        try:
            from core.clipper.garbage_collector import run_gc
            run_gc()
        except Exception as e:
            logger.error(f"Uniquifier: GC falhou: {e}")

        free_gb = _check_disk_space()
        if free_gb < MIN_FREE_DISK_GB:
            raise InsufficientDiskError(
                f"Espaço em disco insuficiente para gerar variantes únicas "
                f"({free_gb:.1f} GB livre, mínimo {MIN_FREE_DISK_GB} GB). "
                f"Aguarde uploads anteriores serem postados (limpeza automática em 24h) "
                f"ou libere espaço manualmente."
            )
        logger.info(f"Uniquifier: GC liberou espaço — {free_gb:.1f} GB livre agora")

    logger.info(
        f"Uniquifier: Gerando {len(profile_slugs)} variantes para "
        f"{os.path.basename(source_path)} (max_concurrent={max_concurrent})"
    )

    semaphore = asyncio.Semaphore(max_concurrent)

    async def _limited_generate(slug: str, idx: int) -> Dict[str, Any]:
        async with semaphore:
            return await generate_variant(
                source_path=source_path,
                profile_slug=slug,
                variant_index=idx,
                output_dir=output_dir,
            )

    tasks = [
        _limited_generate(slug, idx)
        for idx, slug in enumerate(profile_slugs)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Tratar exceções inesperadas do gather
    final_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Uniquifier: Exceção gather para @{profile_slugs[i]}: {result}")
            final_results.append({
                "success": False,
                "variant_path": source_path,
                "profile_slug": profile_slugs[i],
                "params": {},
                "file_size": 0,
                "error": str(result),
            })
        else:
            final_results.append(result)

    success_count = sum(1 for r in final_results if r["success"])
    logger.info(
        f"Uniquifier: {success_count}/{len(profile_slugs)} variantes geradas com sucesso"
    )

    return final_results
