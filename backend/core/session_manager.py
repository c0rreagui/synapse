import os
import logging
from playwright.async_api import BrowserContext

logger = logging.getLogger(__name__)

SESSIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sessions")

def ensure_session_dir():
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR, exist_ok=True)

async def save_session(context: BrowserContext, session_id: str):
    """
    Saves the browser context storage state (cookies, local storage) to a file.
    """
    ensure_session_dir()
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    try:
        await context.storage_state(path=path)
        logger.info(f"Session saved for {session_id} at {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save session for {session_id}: {str(e)}")
        return False

async def load_session(context: BrowserContext, session_id: str) -> bool:
    """
    Loads a storage state into a NEW context (must be done at context creation usually, 
    but Playwright doesn't support loading into existing context easily without hack).
    
    Actually, context.storage_state() is for export. 
    To import, we usually pass storage_state to browser.new_context().
    
    This function checks if session exists and returns the path to be used in new_context.
    """
    ensure_session_dir()
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(path):
        return path
    return None

def get_session_path(session_id: str) -> str:
    ensure_session_dir()
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")
