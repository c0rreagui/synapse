from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime, timezone

army_profiles = Table(
    "army_profiles",
    Base.metadata,
    Column("army_id", Integer, ForeignKey("armies.id", ondelete="CASCADE"), primary_key=True),
    Column("profile_id", Integer, ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True),
)

class Army(Base):
    __tablename__ = "armies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    color = Column(String, default="#00f0ff")
    icon = Column(String, default="swords")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    profiles = relationship("Profile", secondary=army_profiles, back_populates="armies")

class Proxy(Base):
    __tablename__ = "proxies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="Proxy Node")
    nickname = Column(String, nullable=True)  # User-friendly display name (e.g. "BR-São Paulo")
    server = Column(String, nullable=False) # e.g. "http://123.45.67.89:8080"
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    active = Column(Boolean, default=True)

    # --- Fingerprint Overrides (Optional default per proxy node) ---
    fingerprint_ua = Column(String, nullable=True)
    fingerprint_locale = Column(String, nullable=True)   # e.g. "en-US", "pt-BR"
    fingerprint_timezone = Column(String, nullable=True) # e.g. "America/New_York"
    geolocation_latitude = Column(String, nullable=True)
    geolocation_longitude = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    profiles = relationship("Profile", back_populates="proxy")

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True) # e.g. "tiktok_profile_01" (legacy key) or "username"
    username = Column(String, unique=True, index=True)
    label = Column(String)
    icon = Column(String, default="👤")
    type = Column(String, default="cuts") # 'main' or 'cuts'
    active = Column(Boolean, default=True)
    avatar_url = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    
    # JSON columns for flexible data
    oracle_best_times = Column(JSON, default=list) # List of dicts
    last_seo_audit = Column(JSON, default=dict) # The BIG audit object
    
    # --- Anti-Detect: Proxy Identity (Relational) ---
    proxy_id = Column(Integer, ForeignKey("proxies.id"), nullable=True)
    # proxy_server / proxy_password: removidos do ORM (SYN-122 dead code).
    # Colunas podem existir no banco legado, mas são ignoradas pelo SQLAlchemy.
    # Usar proxy_id + relação proxy para novos dados.

    proxy = relationship("Proxy", back_populates="profiles")
    armies = relationship("Army", secondary=army_profiles, back_populates="profiles")

    # --- Dolphin{anty} Integration ---
    dolphin_profile_name = Column(String, nullable=True)    # Nome do perfil no Dolphin (ex: "DoseAlta TV")

    # --- Anti-Detect: Browser Fingerprint (Per-Profile) ---
    fingerprint_ua = Column(String, nullable=True)          # User-Agent fixo para este perfil
    fingerprint_viewport_w = Column(Integer, default=1920)
    fingerprint_viewport_h = Column(Integer, default=1080)
    fingerprint_locale = Column(String, default="pt-BR")
    fingerprint_timezone = Column(String, default="America/Sao_Paulo")

    # --- Anti-Detect: Geolocation (Consistente com IP do Proxy) ---
    geolocation_latitude = Column(String, nullable=True)   # Ex: "-23.5505"
    geolocation_longitude = Column(String, nullable=True)  # Ex: "-46.6333"

    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Future relations
    # audits = relationship("Audit", back_populates="profile")

class Audit(Base):
    """
    Stores historical audits for trending/analytics over time.
    Separated from the main profile to keep history.
    """
    __tablename__ = "audits"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    data = Column(JSON) # The full audit result snapshot
    score = Column(Integer) # Quick access to total score

    # profile = relationship("Profile", back_populates="audits")

class ScheduleItem(Base):
    __tablename__ = "schedule"

    id = Column(Integer, primary_key=True, index=True)
    profile_slug = Column(String, index=True) # Linking loosely to profile for now to ease migration
    video_path = Column(String)
    scheduled_time = Column(DateTime)
    status = Column(String, default="pending") # pending, posted, failed, processing
    error_message = Column(String, nullable=True)
    metadata_info = Column(JSON, default=dict) # Title, caption, tags

class Trend(Base):
    """
    Stores trending sounds/hashtags validated by Oracle.
    Migrated from trends.json to support history and analytics.
    """
    __tablename__ = "trends"

    id = Column(Integer, primary_key=True, index=True)
    niche = Column(String, index=True) # e.g. "dance", "comedy", "all"
    platform = Column(String, default="tiktok")
    
    # Core Data
    title = Column(String) # Hashtag name or Sound title
    identifier = Column(String, index=True) # e.g. "sound_123" or "hashtag_xyz" (for dedup)
    
    # Metrics
    volume = Column(Integer, default=0) # Usage count/Views
    growth_24h = Column(Integer, default=0) # Percentage growth * 100 (int for precision)
    score = Column(Integer, default=0) # Confidence score (0-100)
    
    cached_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime) # Explicit expiration for cache logic

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True) # User defined name
    content = Column(String) # The actual prompt text
    category = Column(String, default="General") # Viral, Professional, etc.
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class VideoQueue(Base):
    """
    Fila de videos para auto-agendamento incremental.
    Criado por SYN-67 (TikTok Studio Native Scheduler) e SYN-69 (Video Queue Persistence).
    """
    __tablename__ = "video_queue"

    id = Column(Integer, primary_key=True, index=True)
    profile_slug = Column(String, index=True)
    video_path = Column(String, nullable=False)
    caption = Column(String, default="")
    hashtags = Column(JSON, default=list)
    privacy_level = Column(String, default="public_to_everyone")

    # Posicao na fila (0-indexed)
    position = Column(Integer, nullable=False)

    # Configuracao de agendamento
    posts_per_day = Column(Integer, default=1)     # 1, 2 ou 3 posts por dia
    start_hour = Column(Integer, default=18)        # Mantido para backward-compat
    schedule_hours = Column(JSON, default=list)     # Ex: [12, 18] - horarios exatos por dia

    # Estado
    status = Column(String, default="queued", index=True)
    # queued     -> aguardando agendamento
    # scheduled  -> agendado no TikTok Studio com sucesso
    # failed     -> tentativa de agendamento falhou
    # cancelled  -> cancelado pelo usuario

    # Rastreabilidade
    schedule_item_id = Column(Integer, ForeignKey("schedule.id"), nullable=True)
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    scheduled_at = Column(DateTime, nullable=True)


class PendingApproval(Base):
    """
    Fila de curadoria Tinder-style.
    Vídeos finalizados pelo Clipper caem aqui para aprovação humana
    antes de serem injetados no scheduler via batch_manager/smart_logic.
    
    Created by: SYN-86 (Autonomous Twitch Pipeline)
    """
    __tablename__ = "pending_approvals"

    id = Column(Integer, primary_key=True, index=True)
    clip_job_id = Column(Integer, ForeignKey("clip_jobs.id"), nullable=True, index=True)
    video_path = Column(String, nullable=False)
    thumbnail_path = Column(String, nullable=True)
    
    # Metadata do streamer/clipe
    streamer_name = Column(String, nullable=True)
    title = Column(String, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    
    # Descrição gerada/editada para publicação
    caption = Column(String, nullable=True)       # Texto da descrição do TikTok
    hashtags = Column(JSON, default=list)          # Lista de hashtags ["#tag1", "#tag2"]
    caption_generated = Column(Boolean, default=False)  # True se foi gerada pelo Oracle

    # Estado da curadoria
    status = Column(String, default="pending", index=True)
    # pending -> approved -> rejected

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ─── Clipper Module Models ──────────────────────────────────────────────
# Importados aqui para garantir que o SQLAlchemy registre as tabelas
# quando Base.metadata.create_all() for executado.
from core.clipper.models import TwitchTarget, ClipJob, TwitchKnownStreamer  # noqa: F401, E402
