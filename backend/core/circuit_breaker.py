
import os
import json
import time
import logging
from datetime import datetime, timedelta
from core.config import DATA_DIR, CIRCUIT_BREAKER_THRESHOLD, CIRCUIT_BREAKER_WINDOW

logger = logging.getLogger(__name__)

STATE_FILE = os.path.join(DATA_DIR, "circuit_breaker_state.json")

class CircuitBreaker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CircuitBreaker, cls).__new__(cls)
            cls._instance.state = "CLOSED" 
            cls._instance.failure_count = 0
            cls._instance.last_failure_time = 0.0
            cls.load_state(cls._instance)
        return cls._instance

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                    self.state = data.get("state", "CLOSED")
                    self.failure_count = data.get("failure_count", 0)
                    self.last_failure_time = data.get("last_failure_time", 0.0)
            except Exception as e:
                logger.error(f"Failed to load circuit breaker state: {e}")

    def save_state(self):
        try:
            data = {
                "state": self.state,
                "failure_count": self.failure_count,
                "last_failure_time": self.last_failure_time
            }
            with open(STATE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save circuit breaker state: {e}")

    async def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        logger.warning(f"⚠️ Circuit Breaker: Failure recorded. Count: {self.failure_count}/{CIRCUIT_BREAKER_THRESHOLD}")

        if self.failure_count >= CIRCUIT_BREAKER_THRESHOLD:
            if self.state != "OPEN":
                self.state = "OPEN"
                logger.critical(f"🛑 CIRCUIT BREAKER TRIPPED! System Paused.")
                # Notify User
                try:
                    from core.notifications import notification_manager
                    await notification_manager.send_alert(
                        "🛑 System Paused (Circuit Breaker)", 
                        f"Failure threshold ({CIRCUIT_BREAKER_THRESHOLD}) reached in window ({CIRCUIT_BREAKER_WINDOW}s). System operation paused to prevent bans.",
                        0xFF0000 
                    )
                except ImportError:
                    pass
        
        self.save_state()

    async def record_success(self):
        if self.failure_count > 0:
            self.failure_count = 0
            self.state = "CLOSED"
            logger.info("✅ Circuit Breaker: Success recorded. Count reset.")
            self.save_state()

    def is_open(self) -> bool:
        if self.state == "CLOSED":
            return False
            
        if self.state == "OPEN":
            # Check if window passed to attempt retry (HALF_OPEN logic could go here)
            time_since_failure = time.time() - self.last_failure_time
            if time_since_failure > CIRCUIT_BREAKER_WINDOW:
                logger.info(f"Circuit Breaker cooling down... allowing single retry (HALF-OPEN).")
                # We return False (allow retry), but keep state OPEN until success confirms it works.
                return False
                
            return True
            
        return False

    async def reset(self):
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.save_state()
        logger.info("🔄 Circuit Breaker Manually Reset")

circuit_breaker = CircuitBreaker()
