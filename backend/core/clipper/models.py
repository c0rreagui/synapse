"""
Clipper Models - Modelos SQLAlchemy para o Pipeline de Cortes
=============================================================

TwitchTarget: Canal da Twitch monitorado pelo CronJob.
ClipJob: Estado do pipeline de processamento para cada lote de clipes.
"""

from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey, DateTime, Float, UniqueConstraint
from datetime import datetime, timezone
from enum import Enum
from typing import TypedDict, List
from pydantic import BaseModel

from core.database import Base

class JobStatus(str, Enum):
    PENDING = "pending"
    WAITING_CLIPS = "waiting_clips"  # Aguardando mais clips para atingir 61s mínimo
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    EDITING = "editing"
    STITCHING = "stitching"
    COMPLETED = "completed"
    FAILED = "failed"

class ClipMetadataDict(TypedDict, total=False):
    title: str
    views: int
    duration: float
    creator: str
    game: str


class TwitchTarget(Base):
    """
    Canal da Twitch que o Synapse monitora para novos clipes.
    O usuario cadastra a URL do perfil e o sistema faz polling periodico.
    """
    __tablename__ = "twitch_targets"

    id = Column(Integer, primary_key=True, index=True)
    channel_url = Column(String, unique=True, nullable=False)
    channel_name = Column(String, index=True, nullable=False)

    # Tipo de alvo: "channel" ou "category"
    target_type = Column(String, default="channel", index=True)

    # Roteamento Multi-Agência (Exército de Cortes vinculado a um Perfil)
    army_id = Column(Integer, ForeignKey("armies.id", ondelete="SET NULL"), nullable=True)

    # Twitch API identifiers (preenchidos automaticamente no primeiro fetch)
    broadcaster_id = Column(String, nullable=True, index=True)
    category_id = Column(String, nullable=True, index=True) # Para type="category"
    profile_image_url = Column(String, nullable=True)
    offline_image_url = Column(String, nullable=True)

    # Configuracao de monitoramento
    active = Column(Boolean, default=True)
    auto_approve = Column(Boolean, default=False)  # Se True, pula curadoria e envia direto pro Scheduler
    check_interval_minutes = Column(Integer, default=15)
    max_clips_per_check = Column(Integer, default=100)  # Maximo Twitch API = 100
    min_clip_views = Column(Integer, default=10)  # Filtro de qualidade para suportar canais menores
    lookback_hours = Column(Integer, default=24)  # Janela de busca maior para achar os clipes

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

    id = Column(Integer, primary_key=True)
    target_id = Column(Integer, ForeignKey("twitch_targets.id"), nullable=False)

    # Clipes consumidos neste job
    clip_urls = Column(JSON, default=list) # Array of clip URLs to process
    clip_metadata = Column(JSON, default=list)      # type: list[ClipMetadataDict] | None
    clip_local_paths = Column(JSON, default=list)   # Caminhos pos-download

    # Estado do pipeline
    status = Column(String, default=JobStatus.PENDING)  # pending, downloading, transcribing, editing, stitching, completed, failed
    current_step = Column(String, nullable=True)    # Detalhe do passo atual
    progress_pct = Column(Integer, default=0)       # 0-100

    # Resultados intermediarios
    whisper_result = Column(JSON, nullable=True)    # Transcricao word-level

    # Produto final
    output_path = Column(String, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Erros
    error_message = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)  # Quantas vezes este job foi retentado
    priority = Column(Integer, default=0)  # 0=normal, 1=high (processado primeiro)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class TwitchKnownStreamer(Base):
    """
    Streamer PT-BR descoberto pelo Radar de Lives (SYN-126).
    Mantém uma whitelist por categoria para coleta cirúrgica de clipes.
    """
    __tablename__ = "twitch_known_streamers"
    __table_args__ = (
        UniqueConstraint("broadcaster_id", "category_id", name="uq_streamer_category"),
    )

    id = Column(Integer, primary_key=True, index=True)
    broadcaster_id = Column(String, nullable=False, index=True)
    broadcaster_name = Column(String, nullable=False)
    category_id = Column(String, nullable=False, index=True)
    language = Column(String, default="pt")
    discovered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen_live = Column(DateTime, nullable=True)
    clip_count = Column(Integer, default=0)  # Total de clipes coletados deste streamer
