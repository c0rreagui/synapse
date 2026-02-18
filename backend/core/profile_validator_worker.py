
import asyncio
import os
import sys
import logging
import json # Ensure json is imported

# Add parent path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.browser import launch_browser, close_browser
from core.session_manager import get_session_path, get_profile_user_agent

logger = logging.getLogger(__name__)

async def validate_profile_worker(profile_id: str, headless: bool = True) -> dict:
    """
    WORKER FUNCTION: Performs the actual browser validation.
    Called by validator_cli.py (subprocess).
    """
    try:
        # 1. Resolve Session Path & UA
        session_path = get_session_path(profile_id)
        if not os.path.exists(session_path):
            return {"status": "error", "message": "Session file not found"}
            
        user_agent = get_profile_user_agent(profile_id)
        
        # 2. Launch Browser
        p, browser, context, page = await launch_browser(
            headless=headless,
            storage_state=session_path,
            user_agent=user_agent
        )
        
        try:
            # 3. Check Session via "Manage Account" or Profile Page
            # We go to the profile page of the user themselves
            # But we might not know the username from ID immediately if filenames are obfuscated.
            # However, profile_id usually IS the username in this system (or p{username}).
            
            username = profile_id
            if username.startswith("p"):
                username = username[1:]
                
            target_url = f"https://www.tiktok.com/@{username}"
            
            logger.info(f"Worker visiting: {target_url}")
            
            # Go to page
            await page.goto(target_url, timeout=60000, wait_until='domcontentloaded')
            await page.wait_for_timeout(3000)
            
            # 4. Analyze State
            current_url = page.url
            # content = await page.content() # Heavy, maybe skip unless needed
            
            is_login_redirect = "login" in current_url and "tiktok.com" in current_url
            
            # Check for specific "Edit profile" button (strong indicator of ownership/login)
            # or just "Follow" button (indicator of public view)
            # But we want to know if session is VALID.
            
            # Actually, best check for session validity is if we are NOT asked to login
            # and if we can see specific logged-in elements.
            
            # Try a more reliable check: "View Profile" icon in top right
            
            is_logged_in = False
            try:
                # Avatar container in header usually indicates login
                # data-e2e="profile-icon" is common
                if await page.locator('[data-e2e="profile-icon"]').count() > 0:
                    is_logged_in = True
            except: pass
            
            if is_login_redirect:
                return {"status": "invalid", "message": "Redirected to login"}
                
            if is_logged_in:
                 return {"status": "valid", "message": "Logged in successfully", "username": username}
            else:
                 # Just browsing publicly?
                 # If we see "Follow" button instead of "Edit profile", then we are NOT logged in as that user.
                 try:
                    is_edit_profile = await page.locator('button:has-text("Edit profile")').count() > 0
                    if is_edit_profile:
                        return {"status": "valid", "message": "Edit Profile visible (Owner Mode)"}
                 except: pass

                 return {"status": "warning", "message": "Profile accessible but not logged in (Guest mode?)"}

        finally:
            await close_browser(p, browser)

    except Exception as e:
        logger.error(f"Worker validation failed: {e}")
        return {"status": "error", "message": str(e)}
