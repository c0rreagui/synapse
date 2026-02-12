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

# Identidade Dinâmica centralizada em core.network_utils
from core.network_utils import get_random_user_agent, DEFAULT_LOCALE, DEFAULT_TIMEZONE

async def launch_browser(
    headless: bool = True,
    proxy: Optional[Dict[str, str]] = None,
    user_agent: str = None, # Será pegue do network_utils se None
    viewport: Optional[Dict[str, int]] = None,
    storage_state: Optional[str] = None,
    user_data_dir: Optional[str] = None # NEW: Persistent Context Path
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
    
    # Resolve User-Agent if not provided
    if not user_agent:
        user_agent = get_random_user_agent()
        logger.info(f"[BROWSER] Dynamic identity assigned: {user_agent[:40]}...")
    if IN_DOCKER and not headless:
        logger.warning("[DOCKER] Forcing headless=True (no display available in container)")
        headless = True
    
    # Build args list
    browser_args = STEALTH_ARGS.copy()
    if IN_DOCKER:
        browser_args.extend(DOCKER_HEADLESS_ARGS)
        logger.info(f"[BROWSER] Docker mode - added {len(DOCKER_HEADLESS_ARGS)} extra args")
    elif headless:
        # On Windows/local, we might need fewer flags for stability
        # But we still want some basic ones for headless
        browser_args.append("--headless=new")
        logger.info("[BROWSER] Headless mode (native)")
    
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
        # PERSISTENT CONTEXT MODE
        if user_data_dir:
            logger.info(f"📂 Launching Persistent Context: {user_data_dir}")
            
            # Ensure dir exists
            if not os.path.exists(user_data_dir):
                os.makedirs(user_data_dir, exist_ok=True)
            
            context = await p.chromium.launch_persistent_context(
                user_data_dir,
                headless=headless,
                args=browser_args,
                viewport=viewport or {"width": 1920, "height": 1080},
                user_agent=user_agent,
                locale=DEFAULT_LOCALE,
                timezone_id=DEFAULT_TIMEZONE,
                ignore_default_args=["--enable-automation"],
                **({"proxy": launch_options["proxy"]} if proxy else {})
            )
            
            browser = None 
            page = context.pages[0] if context.pages else await context.new_page()
            
        else:
            # STANDARD EPHEMERAL MODE
            browser = await p.chromium.launch(
                headless=headless,
                args=browser_args,
                ignore_default_args=["--enable-automation"],
            )
            logger.info(f"Browser launched (headless={headless})")
            
            context_options: Dict[str, Any] = {
                "viewport": viewport or {"width": 1920, "height": 1080},
                "user_agent": user_agent,  # Re-enable realistic user agent
                "locale": DEFAULT_LOCALE,
                "timezone_id": DEFAULT_TIMEZONE,
            }

            if storage_state and os.path.exists(storage_state):
                 context_options["storage_state"] = storage_state
                 logger.info(f"✅ Loading session from: {storage_state}")
            
            context = await browser.new_context(**context_options)
            page = await context.new_page()
        
        # Stealth injection - hide webdriver detection (Common for both)
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
        
        logger.info(f"Browser launched successfully (Headless: {headless}, Persistent: {bool(user_data_dir)})")
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
