import os
import logging
import sys
import asyncio
from typing import Optional, Tuple, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

# CRITICAL: Windows event loop fix is handled in main.py
# if sys.platform == 'win32':
#     asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

logger = logging.getLogger(__name__)

# Docker detection - check if running inside container
def is_running_in_docker() -> bool:
    """Detect if we're running inside a Docker container."""
    # Check for .dockerenv file (most reliable)
    if os.path.exists('/.dockerenv'):
        return True
    # Check cgroup (fallback for some container runtimes)
    try:
        with open('/proc/1/cgroup', 'rt') as f:
            return 'docker' in f.read() or 'containerd' in f.read()
    except:
        pass
    return False

IN_DOCKER = is_running_in_docker()

STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--disable-setuid-sandbox",
    "--disable-gpu",  # Required for headless in Docker
    "--no-first-run",
    "--no-default-browser-check",
    "--ignore-certificate-errors",
]

# Extra args needed for Docker/headless environment
DOCKER_HEADLESS_ARGS = [
    "--headless=new",  # New headless mode (Chrome 109+)
    "--disable-software-rasterizer",
    "--disable-background-networking",
    "--single-process",  # Sometimes needed in Docker
    "--disable-features=VizDisplayCompositor",
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
    
    # Force headless in Docker environment (no display available)
    if IN_DOCKER and not headless:
        logger.warning("[DOCKER] Forcing headless=True (no display available in container)")
        headless = True
    
    # Build args list
    browser_args = STEALTH_ARGS.copy()
    if IN_DOCKER or headless:
        browser_args.extend(DOCKER_HEADLESS_ARGS)
        logger.info(f"[BROWSER] Docker/Headless mode - added {len(DOCKER_HEADLESS_ARGS)} extra args")
    
    launch_options: Dict[str, Any] = {
        "headless": headless,
        "args": browser_args,
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
        # LAUNCH with environment-appropriate options
        browser = await p.chromium.launch(
            headless=headless,
            args=browser_args,
            ignore_default_args=["--enable-automation"],
        )
        logger.info(f"Browser launched (headless={headless})")
        
        context_options: Dict[str, Any] = {
            "viewport": viewport or {"width": 1920, "height": 1080},
            "user_agent": user_agent,  # Re-enable realistic user agent
            "locale": "pt-BR",
            "timezone_id": "America/Sao_Paulo",
        }

        if storage_state and os.path.exists(storage_state):
             context_options["storage_state"] = storage_state
             logger.info(f"✅ Loading session from: {storage_state}")
        
        context = await browser.new_context(**context_options)
        
        # Stealth injection - hide webdriver detection
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt', 'en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 5});
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
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
