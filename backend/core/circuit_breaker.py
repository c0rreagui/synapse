
import os
import json
import time
import logging
from datetime import datetime, timedelta
from core.config import DATA_DIR, CIRCUIT_BREAKER_THRESHOLD, CIRCUIT_BREAKER_WINDOW

logger = logging.getLogger(__name__)

STATE_DIR = os.path.join(DATA_DIR, "circuit_breaker")
os.makedirs(STATE_DIR, exist_ok=True)

# Legacy global state file (for migration)
LEGACY_STATE_FILE = os.path.join(DATA_DIR, "circuit_breaker_state.json")


class CircuitBreaker:
    """Per-profile circuit breaker. Each profile has independent failure tracking."""

    _instances = {}

    def __new__(cls, profile_slug: str = "global"):
        if profile_slug not in cls._instances:
            instance = super(CircuitBreaker, cls).__new__(cls)
            instance.profile_slug = profile_slug
            instance.state = "CLOSED"
            instance.failure_count = 0
            instance.last_failure_time = 0.0
            instance._state_file = os.path.join(STATE_DIR, f"{profile_slug}.json")
            instance.load_state()
            cls._instances[profile_slug] = instance
        return cls._instances[profile_slug]

    def load_state(self):
        if os.path.exists(self._state_file):
            try:
                with open(self._state_file, 'r') as f:
                    data = json.load(f)
                    self.state = data.get("state", "CLOSED")
                    self.failure_count = data.get("failure_count", 0)
                    self.last_failure_time = data.get("last_failure_time", 0.0)
            except Exception as e:
                logger.error(f"Failed to load circuit breaker state for {self.profile_slug}: {e}")

    def save_state(self):
        try:
            data = {
                "state": self.state,
                "failure_count": self.failure_count,
                "last_failure_time": self.last_failure_time,
                "profile_slug": self.profile_slug
            }
            tmp_path = self._state_file + ".tmp"
            with open(tmp_path, 'w') as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, self._state_file)
        except Exception as e:
            logger.error(f"Failed to save circuit breaker state for {self.profile_slug}: {e}")

    async def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        logger.warning(f"⚠️ Circuit Breaker [{self.profile_slug}]: Failure recorded. Count: {self.failure_count}/{CIRCUIT_BREAKER_THRESHOLD}")

        if self.state == "HALF_OPEN":
            self.state = "OPEN"
            logger.critical(f"🛑 CIRCUIT BREAKER [{self.profile_slug}]: HALF_OPEN retry failed. Back to OPEN.")
            self.save_state()
            return

        if self.failure_count >= CIRCUIT_BREAKER_THRESHOLD:
            if self.state != "OPEN":
                self.state = "OPEN"
                logger.critical(f"🛑 CIRCUIT BREAKER [{self.profile_slug}] TRIPPED! Profile Paused.")
                try:
                    from core.notifications import notification_manager
                    await notification_manager.send_alert(
                        f"🛑 Profile Paused (Circuit Breaker): {self.profile_slug}",
                        f"Failure threshold ({CIRCUIT_BREAKER_THRESHOLD}) reached. Profile paused to prevent bans.",
                        0xFF0000
                    )
                except ImportError:
                    pass

        self.save_state()

    async def record_success(self):
        if self.state == "HALF_OPEN":
            self.failure_count = 0
            self.state = "CLOSED"
            logger.info(f"✅ Circuit Breaker [{self.profile_slug}]: HALF_OPEN retry succeeded. CLOSED.")
            self.save_state()
        elif self.failure_count > 0:
            self.failure_count = 0
            self.state = "CLOSED"
            logger.info(f"✅ Circuit Breaker [{self.profile_slug}]: Success recorded. Count reset.")
            self.save_state()

    def is_open(self) -> bool:
        if self.state == "CLOSED":
            return False

        if self.state == "HALF_OPEN":
            return False

        if self.state == "OPEN":
            time_since_failure = time.time() - self.last_failure_time
            if time_since_failure > CIRCUIT_BREAKER_WINDOW:
                logger.info(f"Circuit Breaker [{self.profile_slug}] cooling down... allowing retry (HALF-OPEN).")
                self.state = "HALF_OPEN"
                self.save_state()
                return False

            return True

        return False

    async def reset(self):
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.save_state()
        logger.info(f"🔄 Circuit Breaker [{self.profile_slug}] Manually Reset")


def get_circuit_breaker(profile_slug: str = "global") -> CircuitBreaker:
    """Get or create a per-profile circuit breaker."""
    return CircuitBreaker(profile_slug)


# Backwards-compatible global instance (used by queue_worker, etc.)
circuit_breaker = CircuitBreaker("global")
