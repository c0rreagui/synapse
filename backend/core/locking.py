import os
import time
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSIONS_DIR = os.path.join(BASE_DIR, "data", "sessions")

class SessionLockError(Exception):
    pass

@contextmanager
def session_lock(session_name: str, timeout: int = 600, retry_wait: int = 30, max_retries: int = 5):
    """
    File-based lock to prevent simultaneous usage of a profile.
    Puts a .lock file in data/sessions/.

    Instead of failing immediately when locked, retries up to max_retries times
    with retry_wait seconds between attempts. Stale locks (older than timeout)
    are automatically broken.
    """
    lock_file = os.path.join(SESSIONS_DIR, f"{session_name}.lock")

    # Ensure dir exists
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR, exist_ok=True)

    # 1. Acquire Lock (with retry)
    acquired = False
    for attempt in range(max_retries + 1):
        if os.path.exists(lock_file):
            try:
                mtime = os.path.getmtime(lock_file)
                age = time.time() - mtime
                if age > timeout:
                    logger.warning(f"[LOCK] Found stale lock for {session_name} (Age: {int(age)}s). Breaking lock.")
                    os.remove(lock_file)
                    # Lock broken, proceed to acquire below
                else:
                    # Lock is active
                    if attempt < max_retries:
                        logger.info(f"[LOCK] Session {session_name} locked (age={int(age)}s). Retry {attempt+1}/{max_retries} in {retry_wait}s...")
                        time.sleep(retry_wait)
                        continue
                    else:
                        logger.warning(f"[LOCK] Session {session_name} still locked after {max_retries} retries. Giving up.")
                        raise SessionLockError(f"Session {session_name} is locked.")
            except FileNotFoundError:
                # Race condition, file gone -> proceed
                pass
            except SessionLockError:
                raise
            except OSError:
                pass

        # Try to create the lock file
        try:
            with open(lock_file, 'w') as f:
                f.write(f"{time.time()}\n{os.getpid()}")
            acquired = True
            logger.info(f"[LOCK] Acquired lock for {session_name} (attempt {attempt+1})")
            break
        except OSError as e:
            logger.warning(f"[LOCK] Failed to create lock file: {e}")
            if attempt < max_retries:
                time.sleep(retry_wait)
            else:
                raise SessionLockError(f"Cannot create lock for {session_name}: {e}")

    if not acquired:
        raise SessionLockError(f"Session {session_name} is locked.")

    try:
        yield
    finally:
        # 2. Release Lock
        try:
            if os.path.exists(lock_file):
                os.remove(lock_file)
                logger.info(f"[LOCK] Released lock for {session_name}")
        except Exception as e:
            logger.error(f"Error releasing lock for {session_name}: {e}")
