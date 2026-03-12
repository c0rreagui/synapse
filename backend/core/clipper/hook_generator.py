import os
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional

from core.config import DATA_DIR
import subprocess

logger = logging.getLogger("HookGenerator")

HOOKS_DIR = os.path.join(DATA_DIR, "clipper", "hooks")
os.makedirs(HOOKS_DIR, exist_ok=True)

async def generate_outro_filler(
    streamer: str,
    target_duration: float,
    bg_video_path: str,
) -> Dict[str, Any]:
    """
    Gera um video de preenchimento (linguiça) para completar 1 minuto.
    Usa o primeiro frame do bg_video_path esfocado, e um TTS com uma
    mensagem pedindo para seguir o canal. O audio eh preenchido com silencio
    ate atingir a target_duration.
    """
    hook_id = uuid.uuid4().hex[:8]
    output_path = os.path.join(HOOKS_DIR, f"filler_{hook_id}.mp4")

    # Texto dinâmico e mais natural para o filler
    text_options = [
        "Curtiu o corte? Deixa o follow e fortalece a gente!",
        "Mais clipes como esse todo dia. Só dar aquele follow!",
        "Se você riu, já sabe né? Clica em seguir pra não perder os próximos!",
        "Gostou? Segue aí pra ajudar o canal a crescer!",
        "Conteúdo novo direto, já segue pra dar aquela moral!"
    ]
    import random
    text = random.choice(text_options)
         
    # 1. Gerar TTS via edge-tts
    audio_path = os.path.join(HOOKS_DIR, f"filler_audio_{hook_id}.mp3")
    tts_cmd = [
        "edge-tts",
        "--voice", "pt-BR-AntonioNeural",
        "--text", text,
        "--write-media", audio_path
    ]
    
    try:
        proc = await asyncio.create_subprocess_exec(*tts_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await asyncio.wait_for(proc.communicate(), timeout=30)
    except Exception as e:
        logger.error(f"Erro ao gerar TTS do filler: {e}")
        return {"success": False, "error": str(e)}

    # 2. Extrair 1 frame do bg_video_path
    frame_path = os.path.join(HOOKS_DIR, f"filler_frame_{hook_id}.jpg")
    frame_cmd = [
        "ffmpeg", "-y", "-i", bg_video_path, "-vframes", "1", "-q:v", "2", frame_path
    ]
    try:
        proc = await asyncio.create_subprocess_exec(*frame_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await asyncio.wait_for(proc.communicate(), timeout=20)
    except Exception as e:
        logger.error(f"Erro ao extrair frame do bg_video: {e}")
        return {"success": False, "error": str(e)}

    # 3. Gerar ASS de legenda
    ass_path = os.path.join(HOOKS_DIR, f"filler_sub_{hook_id}.ass")
    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: HookStyle,The Bold Font,90,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,0,5,100,100,100,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:01:00.00,HookStyle,,0,0,0,,{text}
"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)
        
    # 4. Construir o video final de padding usando -loop do input da imagem e o -t especificado
    # O apad preenche o audio para durar target_duration.
    # Escapar ass_path para filtro FFmpeg (Windows compat)
    safe_ass = ass_path.replace("\\", "/").replace(":", "\\:")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", frame_path,
        "-i", audio_path,
        "-filter_complex", f"[0:v]gblur=sigma=50,ass='{safe_ass}'[v];[1:a]apad[a]",
        "-map", "[v]",
        "-map", "[a]",
        "-t", str(target_duration),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-r", "60",
        "-pix_fmt", "yuv420p",
        output_path
    ]

    try:
        proc = await asyncio.create_subprocess_exec(*ffmpeg_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        if proc.returncode != 0:
             logger.error(f"FFmpeg falhou ao gerar filler: {stderr.decode()[:500]}")
             return {"success": False, "error": "FFmpeg error"}
    except Exception as e:
        logger.error(f"Erro no ffmpeg do filler: {e}")
        return {"success": False, "error": str(e)}

    if not os.path.exists(output_path):
        return {"success": False, "error": "Video filler nao foi gerado"}

    # Cleanup temp files
    for tmp in [audio_path, ass_path, frame_path]:
        try:
            os.remove(tmp)
        except OSError:
            pass

    return {"success": True, "output_path": output_path, "duration": target_duration}

