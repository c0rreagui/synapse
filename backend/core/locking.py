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
def session_lock(session_name: str, timeout: int = 600): # 10 min default timeout
    """
    File-based lock to prevent simultaneous usage of a profile.
    Puts a .lock file in data/sessions/.
    """
    lock_file = os.path.join(SESSIONS_DIR, f"{session_name}.lock")
    
    # Ensure dir exists
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        
    start_time = time.time()
    
    # 1. Acquire Lock
    if os.path.exists(lock_file):
        # Check if stale (older than timeout)
        try:
            mtime = os.path.getmtime(lock_file)
            if time.time() - mtime > timeout:
                logger.warning(f"🔓 Found stale lock for {session_name} (Age: {int(time.time()-mtime)}s). Breaking lock.")
                os.remove(lock_file)
            else:
                 logger.warning(f"🔒 Session {session_name} is currently locked by another process.")
                 raise SessionLockError(f"Session {session_name} is locked.")
        except FileNotFoundError:
            # Race condition, file gone -> proceed
            pass
        except OSError:
            pass

    try:
        # Create lock
        with open(lock_file, 'w') as f:
            f.write(str(time.time()))
        logger.info(f"🔒 Acquired lock for {session_name}")
        yield
    finally:
        # 2. Release Lock
        try:
            if os.path.exists(lock_file):
                os.remove(lock_file)
                logger.info(f"🔓 Released lock for {session_name}")
        except Exception as e:
            logger.error(f"Error releasing lock for {session_name}: {e}")
