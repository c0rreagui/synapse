import asyncio
import logging
from typing import Dict, Optional
import os
import time

logger = logging.getLogger(__name__)

class BrowserManager:
    def __init__(self):
        self._active_sessions: Dict[str, str] = {} # profile_id -> status ("repairing", "running_task")
        self._session_started: Dict[str, float] = {} # profile_id -> timestamp when started
        self._locks: Dict[str, asyncio.Lock] = {}
        self._timeout_seconds = 120  # 2 minutes auto-timeout for stuck sessions
        
    def get_lock(self, profile_id: str) -> asyncio.Lock:
        if profile_id not in self._locks:
            self._locks[profile_id] = asyncio.Lock()
        return self._locks[profile_id]

    def is_busy(self, profile_id: str) -> bool:
        # Auto-cleanup stale sessions before checking
        self._cleanup_stale_sessions()
        return profile_id in self._active_sessions

    def _cleanup_stale_sessions(self):
        """Remove sessions that have been running longer than timeout."""
        current_time = time.time()
        stale_profiles = []
        for profile_id, start_time in list(self._session_started.items()):
            if current_time - start_time > self._timeout_seconds:
                stale_profiles.append(profile_id)
        
        for profile_id in stale_profiles:
            logger.warning(f"Auto-clearing stale session for {profile_id} (timed out after {self._timeout_seconds}s)")
            self.clear_status(profile_id)

    def set_status(self, profile_id: str, status: str):
        self._active_sessions[profile_id] = status
        self._session_started[profile_id] = time.time()
        
    def clear_status(self, profile_id: str):
        if profile_id in self._active_sessions:
            del self._active_sessions[profile_id]
        if profile_id in self._session_started:
            del self._session_started[profile_id]
    
    def force_clear_all(self):
        """Force clear all active sessions (emergency reset)."""
        logger.warning("Force clearing all browser sessions")
        self._active_sessions.clear()
        self._session_started.clear()

    async def launch_repair_session(self, profile_id: str):
        """
        Launches an interactive, headful browser for the user to fix the session.
        Opens browser directly (not via subprocess) for better control.
        """
        if self.is_busy(profile_id):
            logger.warning(f"Profile {profile_id} is already busy: {self._active_sessions[profile_id]}")
            return False

        self.set_status(profile_id, "repairing")
        
        try:
            from core.browser import launch_browser, close_browser
            from core.session_manager import get_session_path, save_session, update_profile_status, update_profile_metadata
            from core.network_utils import get_upload_url
            
            session_path = get_session_path(profile_id)
            if not os.path.exists(session_path):
                logger.error(f"Session file not found for {profile_id}")
                return False
            
            logger.info(f"[REPAIR] Opening browser for {profile_id}")
            
            # Launch headful (visible) browser
            p, browser, context, page = await launch_browser(
                headless=False,
                storage_state=session_path
            )
            
            try:
                # Navigate to TikTok Studio
                logger.info(f"[REPAIR] Navigating to TikTok Studio...")
                await page.goto(get_upload_url(), timeout=60000, wait_until="domcontentloaded")
                
                logger.info("[REPAIR] Browser opened. Waiting for user to complete login...")
                
                # Wait for browser to close (user action) or timeout after 10 minutes
                try:
                    await page.wait_for_timeout(600000)  # 10 minutes max
                except Exception:
                    pass  # Browser closed by user or timeout
                
                # Save the updated session
                logger.info("[REPAIR] Saving updated session...")
                await save_session(context, profile_id)
                
                # Clear error screenshot and reactivate profile
                update_profile_metadata(profile_id, {"last_error_screenshot": None})
                update_profile_status(profile_id, True)
                
                logger.info("[REPAIR] Session saved successfully!")
                return True
                
            finally:
                if p:
                    await close_browser(p, browser)
                    
        except Exception as e:
            logger.error(f"Failed to launch repair session: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.clear_status(profile_id)

browser_manager = BrowserManager()
