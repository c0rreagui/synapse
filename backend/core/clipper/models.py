"""
Clipper Models - Modelos SQLAlchemy para o Pipeline de Cortes
=============================================================

TwitchTarget: Canal da Twitch monitorado pelo CronJob.
ClipJob: Estado do pipeline de processamento para cada lote de clipes.
"""

from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey, DateTime, Float
from datetime import datetime, timezone

from core.database import Base


class TwitchTarget(Base):
    """
    Canal da Twitch que o Synapse monitora para novos clipes.
    O usuario cadastra a URL do perfil e o sistema faz polling periodico.
    """
    __tablename__ = "twitch_targets"

    id = Column(Integer, primary_key=True, index=True)
    channel_url = Column(String, unique=True, nullable=False)
    channel_name = Column(String, index=True, nullable=False)

    # Twitch API identifiers (preenchidos automaticamente no primeiro fetch)
    broadcaster_id = Column(String, nullable=True, index=True)

    # Configuracao de monitoramento
    active = Column(Boolean, default=True)
    check_interval_minutes = Column(Integer, default=15)
    max_clips_per_check = Column(Integer, default=5)
    min_clip_views = Column(Integer, default=100)  # Filtro de qualidade

    # Estado do monitoramento
    last_checked_at = Column(DateTime, nullable=True)
    last_clip_found_at = Column(DateTime, nullable=True)
    total_clips_processed = Column(Integer, default=0)
    consecutive_empty_checks = Column(Integer, default=0)

    # Metadados
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ClipJob(Base):
    """
    Representa um job unitario do pipeline de cortes.
    Cada job consome 1+ clipes e produz 1 video final (>60s, formato 9:16).

    Status flow:
        pending -> downloading -> transcribing -> editing -> stitching -> completed
                                                                       -> failed
    """
    __tablename__ = "clip_jobs"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("twitch_targets.id"), nullable=False, index=True)

    # Clipes consumidos neste job
    clip_urls = Column(JSON, default=list)          # ["https://clips.twitch.tv/..."]
    clip_metadata = Column(JSON, default=list)      # [{title, views, duration, creator}]
    clip_local_paths = Column(JSON, default=list)   # Caminhos pos-download

    # Estado do pipeline
    status = Column(String, default="pending", index=True)
    # pending | downloading | transcribing | editing | stitching | completed | failed
    current_step = Column(String, nullable=True)    # Detalhe do passo atual
    progress_pct = Column(Integer, default=0)       # 0-100

    # Resultados intermediarios
    whisper_result = Column(JSON, nullable=True)    # Transcricao word-level
    ass_subtitle_path = Column(String, nullable=True)

    # Produto final
    output_path = Column(String, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)

    # Erros
    error_message = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=2)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
