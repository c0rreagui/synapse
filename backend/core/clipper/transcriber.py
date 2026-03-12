"""
Clipper Transcriber - Transcricao Local via faster-whisper
===========================================================

Extrai audio de video e gera transcricao word-level (palavra por palavra)
usando faster-whisper (CTranslate2). Economiza 3-4x de memoria vs whisper
original e roda 4x mais rapido.

Gerenciamento de memoria:
    - Tenta CUDA (float16) se GPU disponivel
    - Fallback para CPU (int8) automaticamente
    - Libera modelo da memoria apos uso via context manager

Requisitos:
    - pip install faster-whisper
    - FFmpeg no PATH (para extracao de audio)
"""

import os
import asyncio
import logging
import tempfile
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from core.database import safe_session
from core.clipper.models import ClipJob
from core.config import DATA_DIR

logger = logging.getLogger("ClipperTranscriber")

# Diretorio para audio extraido temporariamente
AUDIO_TEMP_DIR = os.path.join(DATA_DIR, "clipper", "audio_temp")
os.makedirs(AUDIO_TEMP_DIR, exist_ok=True)

# Modelo padrao - "small" para CPU (medium demora 30min+ por clip em CPU)
# Em GPU com VRAM suficiente, usar WHISPER_MODEL_SIZE=medium via env
# Alternativas: "tiny", "base", "small", "medium", "large-v3"
DEFAULT_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")

# Roteamento de vocabulario por jogo (mantido curto p/ nao estourar tokens)
GAME_PROMPTS = {
    "grand theft auto v": (
        "GTA RP, fuga, VDM, RDM, safe, policia, perseguicao, cidade, "
        "personagem, roleplay, favela, beco, carro, helicóptero."
    ),
    "valorant": (
        "Valorant, clutch, ace, plant, defuse, eco, force buy, "
        "Jett, Reyna, Sage, Omen, operator, spike."
    ),
    "fortnite": (
        "Fortnite, build, edit, box fight, crank, pump, "
        "storm, loot, shield, victory royale."
    ),
    "league of legends": (
        "League of Legends, gank, jungle, lane, turret, baron, "
        "dragon, flash, ulti, combo, teamfight."
    ),
}

# Prompt generico de girias BR para qualquer jogo
BASE_PROMPT = (
    "live, stream, gameplay, twitch, chat, clip, "
    "mano, cara, bicho, brabo, salve, bora, partiu, ae, né."
)


def _build_initial_prompt(
    game_name: Optional[str] = None,
    channel_name: Optional[str] = None,
) -> str:
    """Monta o initial_prompt para o Whisper baseado nos metadados da Twitch."""
    parts = []

    # Adiciona vocabulario especifico do jogo
    if game_name:
        key = game_name.strip().lower()
        if key in GAME_PROMPTS:
            parts.append(GAME_PROMPTS[key])

    # Adiciona nome do canal como ancora
    if channel_name:
        name = channel_name.replace("_", " ")
        parts.append(name)

    # Sempre adiciona base
    parts.append(BASE_PROMPT)

    prompt = ", ".join(parts)
    logger.debug(f"Whisper initial_prompt: {prompt[:120]}...")
    return prompt


def _detect_compute_config() -> tuple:
    """
    Detecta o melhor device/compute_type para faster-whisper.

    Returns:
        (device, compute_type) - ex: ("cuda", "float16") ou ("cpu", "int8")
    """
    try:
        import torch
        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_mem / (1024**3)
            logger.info(f"GPU detectada: {torch.cuda.get_device_name(0)} ({vram_gb:.1f}GB VRAM)")
            # float16 para GPUs com bastante VRAM, int8_float16 para GPUs menores
            compute = "float16" if vram_gb >= 6 else "int8_float16"
            return "cuda", compute
    except (ImportError, Exception) as e:
        logger.info(f"CUDA nao disponivel ({e}). Usando CPU.")

    return "cpu", "int8"


class TranscriberContext:
    """
    Context manager que carrega o modelo faster-whisper e garante
    liberacao de memoria apos uso.

    Uso:
        async with TranscriberContext() as transcriber:
            result = transcriber.transcribe("video.mp4")
    """

    def __init__(self, model_size: str = DEFAULT_MODEL_SIZE):
        self.model_size = model_size
        self.model = None
        self.device = None
        self.compute_type = None

    def __enter__(self):
        from faster_whisper import WhisperModel

        self.device, self.compute_type = _detect_compute_config()
        logger.info(
            f"Carregando Whisper '{self.model_size}' em {self.device} "
            f"(compute: {self.compute_type})..."
        )

        self.model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        logger.info("Modelo Whisper carregado com sucesso.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._release()
        return False

    def _release(self):
        """Libera modelo e memoria GPU."""
        if self.model is not None:
            del self.model
            self.model = None

        if self.device == "cuda":
            try:
                import torch
                torch.cuda.empty_cache()
                logger.info("Cache CUDA liberado.")
            except ImportError:
                pass

        logger.info("Modelo Whisper descarregado da memoria.")

    def transcribe_file(
        self,
        audio_path: str,
        language: Optional[str] = "pt",
        game_name: Optional[str] = None,
        channel_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transcreve um arquivo de audio e retorna resultado word-level.

        Args:
            audio_path: Caminho do arquivo de audio (.wav, .mp3, .m4a, etc.)
            language: Codigo do idioma (ex: "pt", "en"). None = auto-detect.
            game_name: Nome do jogo (Twitch) para roteamento de vocabulario.
            channel_name: Nome do canal para ancora de contexto.

        Returns:
            Dict com:
                - text: Transcricao completa
                - language: Idioma detectado
                - segments: Lista de segmentos com words[]
                - words: Lista flat de {word, start, end}
        """
        if self.model is None:
            raise RuntimeError("Modelo nao carregado. Use 'with TranscriberContext()' como context manager.")

        prompt = _build_initial_prompt(game_name=game_name, channel_name=channel_name)

        segments_raw, info = self.model.transcribe(
            audio_path,
            language=language,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=300,
                speech_pad_ms=200,
            ),
            initial_prompt=prompt,
        )

        # Materializar o generator em lista
        segments = []
        all_words = []
        full_text_parts = []

        for segment in segments_raw:
            seg_words = []
            if segment.words:
                for w in segment.words:
                    word_entry = {
                        "word": w.word.strip(),
                        "start": round(w.start, 3),
                        "end": round(w.end, 3),
                    }
                    seg_words.append(word_entry)
                    all_words.append(word_entry)

            segments.append({
                "id": segment.id,
                "start": round(segment.start, 3),
                "end": round(segment.end, 3),
                "text": segment.text.strip(),
                "words": seg_words,
            })
            full_text_parts.append(segment.text.strip())

        result = {
            "text": " ".join(full_text_parts),
            "language": info.language,
            "language_probability": round(info.language_probability, 3),
            "duration": round(info.duration, 3),
            "segments": segments,
            "words": all_words,
            "word_count": len(all_words),
        }

        logger.info(
            f"Transcricao concluida: {len(all_words)} palavras, "
            f"idioma={info.language} ({info.language_probability:.0%}), "
            f"duracao={info.duration:.1f}s"
        )

        return result


async def extract_audio(video_path: str, output_path: Optional[str] = None) -> str:
    """
    Extrai a trilha de audio de um video usando FFmpeg.

    Args:
        video_path: Caminho do video
        output_path: Caminho de saida (opcional, gera temp se nao fornecido)

    Returns:
        Caminho do arquivo de audio gerado (.wav 16kHz mono)
    """
    if output_path is None:
        base = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(AUDIO_TEMP_DIR, f"{base}_audio.wav")

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",                    # Sem video
        "-acodec", "pcm_s16le",   # WAV PCM 16-bit
        "-ar", "16000",           # 16kHz (ideal para Whisper)
        "-ac", "1",               # Mono
        output_path,
    ]

    logger.info(f"Extraindo audio: {video_path} -> {output_path}")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await asyncio.wait_for(process.communicate(), timeout=300)

    if process.returncode != 0:
        error = stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"FFmpeg falhou ao extrair audio: {error[:300]}")

    if not os.path.exists(output_path) or os.path.getsize(output_path) < 100:
        raise RuntimeError(f"Audio extraido invalido ou vazio: {output_path}")

    logger.info(f"Audio extraido: {output_path} ({os.path.getsize(output_path) / 1024:.0f}KB)")
    return output_path


async def transcribe_video(video_path: str, language: Optional[str] = "pt") -> Dict[str, Any]:
    """
    Pipeline completo: extrai audio do video e transcreve com word-level timestamps.

    Args:
        video_path: Caminho do arquivo de video
        language: Idioma forcado ("pt" = default)

    Returns:
        Dict com resultado word-level (ver TranscriberContext.transcribe_file)
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video nao encontrado: {video_path}")

    # 1. Extrair audio
    audio_path = await extract_audio(video_path)

    try:
        # 2. Transcrever (sync, roda em thread para nao bloquear event loop)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _transcribe_sync, audio_path, language)
        return result
    finally:
        # 3. Limpar audio temporario
        _cleanup_temp(audio_path)


def _transcribe_sync(audio_path: str, language: Optional[str] = "pt") -> Dict[str, Any]:
    """Execucao sincrona da transcricao (para rodar em executor)."""
    try:
        with TranscriberContext() as ctx:
            return ctx.transcribe_file(audio_path, language=language)
    except Exception as e:
        logger.error(f"Transcricao falhou para {audio_path}: {e}", exc_info=True)
        raise


def _cleanup_temp(path: str) -> None:
    """Remove arquivo temporario com log silencioso."""
    try:
        if os.path.exists(path):
            os.remove(path)
            logger.debug(f"Temp removido: {path}")
    except OSError as e:
        logger.warning(f"Falha ao remover temp {path}: {e}")


async def transcribe_job_clips(job_id: int) -> Dict[str, Any]:
    """
    Transcreve todos os clipes de um ClipJob.
    Atualiza o status do job e armazena o resultado word-level.

    Args:
        job_id: ID do ClipJob

    Returns:
        Dict com: success, transcriptions (lista), total_words
    """
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if not job:
            return {"success": False, "transcriptions": [], "total_words": 0, "error": "Job nao encontrado."}

        local_paths = job.clip_local_paths or []
        job.status = "transcribing"
        job.current_step = f"Transcrevendo {len(local_paths)} clipe(s)..."
        db.commit()

    if not local_paths:
        _fail_job(job_id, "Nenhum clipe local para transcrever.")
        return {"success": False, "transcriptions": [], "total_words": 0, "error": "Sem clipes locais."}

    transcriptions = []
    total_words = 0
    errors = []

    for i, path in enumerate(local_paths):
        try:
            logger.info(f"Job #{job_id}: Transcrevendo clipe {i + 1}/{len(local_paths)}: {path}")
            result = await transcribe_video(path)
            transcriptions.append(result)
            total_words += result.get("word_count", 0)

            _update_job_progress(job_id, i + 1, len(local_paths))

        except Exception as e:
            error_msg = f"Clipe {i} ({path}): {e}"
            logger.error(f"Job #{job_id}: {error_msg}", exc_info=True)
            errors.append(error_msg)
            # Adiciona transcricao vazia para manter indice alinhado com clips
            transcriptions.append({"text": "", "words": [], "segments": [], "word_count": 0})

    # Salvar resultado no job
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if job:
            job.whisper_result = transcriptions
            if any(t.get("word_count", 0) > 0 for t in transcriptions):
                job.status = "editing"
                job.current_step = "Transcricao concluida. Aguardando edicao."
            else:
                job.status = "failed"
                job.error_message = "Nenhuma palavra transcrita. " + " | ".join(errors)
                job.current_step = "Falha na transcricao."
            db.commit()

    success = any(t.get("word_count", 0) > 0 for t in transcriptions)
    logger.info(f"Job #{job_id}: Transcricao finalizada. {total_words} palavras no total.")

    return {
        "success": success,
        "transcriptions": transcriptions,
        "total_words": total_words,
        "errors": errors,
    }


def _update_job_progress(job_id: int, current: int, total: int) -> None:
    """Atualiza progresso da transcricao no banco (Weight: 25-50%)."""
    base_progress = 25
    progress = base_progress + int((current / total) * 25)
    with safe_session() as db:
        j = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if j:
            j.progress_pct = progress
            j.current_step = f"Transcrevendo clipe {current}/{total}..."
            db.commit()


def _fail_job(job_id: int, error: str) -> None:
    """Marca um job como falhado."""
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = error
            job.current_step = "Falha."
            db.commit()
    logger.error(f"Job #{job_id} falhado: {error}")
