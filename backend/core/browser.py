import os
import logging
from typing import Optional, Tuple, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

logger = logging.getLogger(__name__)

# Standard stealth arguments to reduce detection
STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--disable-setuid-sandbox",
    "--disable-gpu",  # Sometimes helps, sometimes hurts. Keeping for headless stability.
    "--no-first-run",
    "--no-default-browser-check",
    "--ignore-certificate-errors",
]

# MAGIC User-Agent - Tested and confirmed to bypass TikTok detection
MAGIC_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

async def launch_browser(
    headless: bool = True,
    proxy: Optional[Dict[str, str]] = None,
    user_agent: str = MAGIC_USER_AGENT,
    viewport: Optional[Dict[str, int]] = None,
    storage_state: Optional[str] = None
) -> Tuple[Playwright, Browser, BrowserContext, Page]:
    """
    Launches a Chromium browser with stealth settings.
    
    Args:
        headless: Whether to run in headless mode.
        proxy: Proxy settings dictionary (server, username, password).
        user_agent: Custom User-Agent string.
        viewport: Viewport size dictionary (width, height).
        storage_state: Path to the storage state file (cookies) to load.
        
    Returns:
        Tuple containing (playwright, browser, context, page)
    """
    p = await async_playwright().start()
    
    launch_options: Dict[str, Any] = {
        "headless": headless,
        "args": STEALTH_ARGS,
        "ignore_default_args": ["--enable-automation"],  # Key for stealth
    }

    if proxy:
        launch_options["proxy"] = {
            "server": proxy.get("server"),
            "username": proxy.get("username"),
            "password": proxy.get("password"),
        }
        logger.info(f"Launching browser with proxy: {proxy.get('server')}")

    try:
        browser = await p.chromium.launch(**launch_options)
        
        context_options = {
            "user_agent": user_agent,
            "viewport": viewport or {"width": 1920, "height": 1080},
            "ignore_https_errors": True,
            "java_script_enabled": True,
            "bypass_csp": True,
        }

        if storage_state and os.path.exists(storage_state):
             context_options["storage_state"] = storage_state
             logger.info(f"Loading session from: {storage_state}")
        
        context = await browser.new_context(**context_options)
        
        # Apply stealth scripts to context
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = await context.new_page()
        
        logger.info(f"Browser launched successfully (Headless: {headless})")
        return p, browser, context, page
        
    except Exception as e:
        logger.error(f"Failed to launch browser: {str(e)}")
        await p.stop()
        raise e

async def close_browser(p: Playwright, browser: Browser):
    """Safely closes browser and playwright instance."""
    if browser:
        await browser.close()
    if p:
        await p.stop()
