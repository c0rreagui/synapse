"""
Phantom Models — SQLAlchemy models for action logging and trust scoring.

Tables:
    - phantom_actions: Immutable log of every action executed
    - phantom_trust_snapshots: Periodic trust score snapshots (time-series)
    - phantom_persona_assignments: Persona ↔ Profile mapping
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey, DateTime, Float
from core.database import Base


class PhantomAction(Base):
    """
    Immutable log of every action executed by the Phantom engine.

    Each row represents a single atomic action (one scroll, one like, one comment).
    The log is append-only — no updates or deletes.
    """
    __tablename__ = "phantom_actions"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False)

    # Action classification
    action_type = Column(String, index=True, nullable=False)      # "scroll", "watch", "like", "comment", "follow", "search", "explore"
    action_subtype = Column(String, nullable=True)                 # "fyp_scroll", "trending_watch", "niche_search"

    # Target context (what was the action applied to)
    target_video_id = Column(String, nullable=True)                # TikTok video ID if applicable
    target_user_handle = Column(String, nullable=True)             # @handle of target user
    content_niche = Column(String, nullable=True)                  # Detected niche: "comedy", "fashion", etc.

    # Execution result
    success = Column(Boolean, default=True)
    duration_ms = Column(Integer, nullable=True)                   # How long the action took
    error_code = Column(String, nullable=True)                     # "captcha", "rate_limit", "element_not_found"

    # Trust impact (pre-calculated at action time)
    trust_impact = Column(Integer, default=0)                      # Points added/subtracted

    # Flexible metadata
    metadata_json = Column(JSON, default=dict)
    # Examples:
    #   watch: {"watch_pct": 0.87, "video_length_s": 15}
    #   comment: {"text": "omg 💀", "reply_to": null}
    #   follow: {"reason": "trending_creator", "follower_count": 50000}

    # Timestamp
    executed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class PhantomTrustSnapshot(Base):
    """
    Periodic snapshot of trust score for a profile.

    Computed every N hours or after significant sessions.
    Enables time-series visualization of trust growth.
    """
    __tablename__ = "phantom_trust_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False)

    # Score dimensions (each 0-100)
    behavioral_consistency = Column(Float, nullable=False)
    engagement_quality = Column(Float, nullable=False)
    natural_progression = Column(Float, nullable=False)
    platform_adherence = Column(Float, nullable=False)
    session_health = Column(Float, nullable=False)

    # Composite score (weighted average)
    total_score = Column(Float, index=True, nullable=False)
    status = Column(String, nullable=False)  # "nascent", "warming", "building", "established", "trusted", "organic"

    # Context
    actions_counted = Column(Integer, default=0)
    window_days = Column(Integer, default=7)

    computed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class PhantomPersonaAssignment(Base):
    """
    Maps a Gen Z persona to a profile.

    Each profile gets exactly one persona (unique constraint).
    Custom overrides allow per-profile tweaks without changing the persona template.
    """
    __tablename__ = "phantom_persona_assignments"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)

    persona_key = Column(String, nullable=False)     # Key from PERSONAS dict in personas.py
    custom_overrides = Column(JSON, default=dict)     # Per-profile tweaks: {"peak_hours": [10, 11, 20, 21]}

    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
