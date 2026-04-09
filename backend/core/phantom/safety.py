"""
Phantom Safety — Hard limits and guardrails.

Every action runner MUST check these limits before executing.
Violations are logged and the session is terminated immediately.
"""

import os
import logging
from dataclasses import dataclass

logger = logging.getLogger("PhantomSafety")


@dataclass(frozen=True)
class PhantomSafetyConfig:
    """
    Safety configuration. Limits are frozen at module load time.

    The kill switch (enabled) is dynamic — reads PHANTOM_ENABLED from env
    on every access, allowing runtime activation/deactivation without restart.
    """

    # Concurrency
    max_profiles_simultaneous: int = 5

    # Daily hard caps (per profile)
    max_actions_per_day: int = 150
    max_comments_per_day: int = 20
    max_follows_per_day: int = 15
    max_likes_per_day: int = 80
    max_searches_per_day: int = 25
    max_scroll_sessions_per_day: int = 10

    # Velocity
    min_action_interval_seconds: float = 3.0
    min_comment_interval_seconds: float = 45.0
    min_follow_interval_seconds: float = 30.0

    # Risk response
    forced_cooldown_after_captcha_seconds: int = 3600  # 1 hour
    auto_disable_after_ban: bool = True
    auto_disable_after_n_captchas: int = 3

    # Infrastructure
    require_proxy: bool = True

    # Kill switch
    @property
    def enabled(self) -> bool:
        return os.getenv("PHANTOM_ENABLED", "false").lower() == "true"


# Singleton — immutable, no override
SAFETY = PhantomSafetyConfig()


def check_kill_switch() -> bool:
    """Returns True if Phantom is allowed to run."""
    if not SAFETY.enabled:
        logger.warning("[PHANTOM] Kill switch is OFF. Set PHANTOM_ENABLED=true to enable.")
        return False
    return True


def check_proxy_requirement(profile_proxy_id: int | None) -> bool:
    """Ensures profile has a proxy assigned if required."""
    if SAFETY.require_proxy and not profile_proxy_id:
        logger.error("[PHANTOM] Profile has no proxy. Phantom requires proxy for all sessions.")
        return False
    return True
