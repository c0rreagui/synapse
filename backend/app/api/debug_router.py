import os
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from core.browser import launch_browser, close_browser

router = APIRouter(prefix="/debug", tags=["Debug"])
logger = logging.getLogger(__name__)

class DebugResponse(BaseModel):
    status: str
    message: str
    screenshot_path: Optional[str] = None

# Ensure static dir exists
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

@router.post("/check-ip", response_model=DebugResponse)
async def check_ip_stealth():
    """
    Launch a visible browser, check IP on whoer.net, take a screenshot.
    This acts as a "Smoke Test" for the automation engine.
    """
    logger.info("Starting Smoke Test: Check IP")
    
    p = None
    browser = None
    
    try:
        # Launch visible browser for debug purposes
        p, browser, context, page = await launch_browser(headless=False)
        
        # Navigate to iphey.com (better reliability than whoer)
        logger.info("Navigating to iphey.com...")
        await page.goto("https://iphey.com", timeout=60000, wait_until="domcontentloaded")
        
        # Wait a bit for visuals to load
        await page.wait_for_timeout(5000)
        
        # Take screenshot
        screenshot_path = os.path.join(STATIC_DIR, "debug_ip_check.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        logger.info(f"Screenshot saved to {screenshot_path}")
        
        return DebugResponse(
            status="success",
            message="Browser launched and navigated successfully. Check server screen.",
            screenshot_path="/static/debug_ip_check.png"
        )
        
    except Exception as e:
        logger.error(f"Smoke Test Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Always clean up
        if p and browser:
            await close_browser(p, browser)
            logger.info("Browser closed.")
