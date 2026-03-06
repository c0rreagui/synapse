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

# Path to system Chromium (installed via apt in Docker)
SYSTEM_CHROMIUM_PATH = "/usr/bin/chromium" if IN_DOCKER else None

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

from core.process_manager import process_manager

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
    process_manager.register(p) # Register Playwright
    
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
                **({
                    "executable_path": SYSTEM_CHROMIUM_PATH
                } if SYSTEM_CHROMIUM_PATH else {}),
                **({"proxy": launch_options["proxy"]} if proxy else {})
            )
            # Register Context (which acts as browser)
            process_manager.register(context)
            
            browser = None 
            page = context.pages[0] if context.pages else await context.new_page()
            
        else:
            # STANDARD EPHEMERAL MODE
            launch_kwargs = {
                "headless": headless,
                "args": browser_args,
                "ignore_default_args": ["--enable-automation"],
            }
            if SYSTEM_CHROMIUM_PATH:
                launch_kwargs["executable_path"] = SYSTEM_CHROMIUM_PATH
            
            # CRITICAL: Inject proxy into launch_kwargs (was silently dropped before!)
            if proxy:
                launch_kwargs["proxy"] = {
                    "server": proxy.get("server"),
                    "username": proxy.get("username"),
                    "password": proxy.get("password"),
                }
                logger.info(f"[BROWSER] Proxy INJECTED into launch_kwargs: {proxy.get('server')}")
            
            browser = await p.chromium.launch(**launch_kwargs)
            process_manager.register(browser) # Register Browser
            
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
    from core.process_manager import process_manager
    if browser:
        process_manager.unregister(browser)
        await browser.close()
    if p:
        process_manager.unregister(p)
        await p.stop()


async def launch_browser_for_profile(
    profile_slug: str,
    headless: bool = True,
    storage_state: Optional[str] = None,
    max_retries: int = 3,
    base_timeout: int = 90000,  # 90s base (higher for proxy connections)
) -> Tuple[Playwright, Browser, BrowserContext, Page]:
    """
    Launches a browser with FULL identity isolation for a specific profile.
    
    Resolves proxy, User-Agent, viewport, geolocation, timezone and locale
    from the database Profile model. In production, raises MissingProxyError
    if no proxy is configured (HARD BLOCK).
    
    Includes retry with exponential backoff for proxy connection resilience.
    
    Args:
        profile_slug: The profile slug/ID to resolve identity for.
        headless: Whether to run headless.
        storage_state: Path to cookies/session JSON file.
        max_retries: Number of retries for launch failures.
        base_timeout: Base navigation timeout in ms (extended for proxies).
    
    Returns:
        Tuple of (playwright, browser, context, page)
    """
    from core.network_utils import get_profile_identity
    from core.retry_utils import retry_async

    # Resolve full identity (will raise MissingProxyError in production if no proxy)
    identity = get_profile_identity(profile_slug)

    proxy_config = None
    if identity["proxy"]:
        proxy_config = {
            "server": identity["proxy"]["server"],
            "username": identity["proxy"].get("username"),
            "password": identity["proxy"].get("password"),
        }
        logger.info(f"[BROWSER] Proxy configurado para '{profile_slug}': {identity['proxy']['server']}")

    logger.info(
        f"[BROWSER] Identidade isolada para '{profile_slug}': "
        f"UA={identity['user_agent'][:50]}..., "
        f"Viewport={identity['viewport']}, "
        f"Locale={identity['locale']}, "
        f"TZ={identity['timezone']}, "
        f"Proxy={'SIM' if proxy_config else 'NAO'}, "
        f"Geo={'SIM' if identity['geolocation'] else 'NAO'}"
    )

    async def _attempt_launch():
        p, browser, context, page = await launch_browser(
            headless=headless,
            proxy=proxy_config,
            user_agent=identity["user_agent"],
            viewport=identity["viewport"],
            storage_state=storage_state,
        )

        # Apply geolocation if available
        if identity["geolocation"]:
            try:
                await context.set_geolocation(identity["geolocation"])
                await context.grant_permissions(["geolocation"])
                logger.info(f"[BROWSER] Geolocation definida: {identity['geolocation']}")
            except Exception as geo_err:
                logger.warning(f"[BROWSER] Falha ao definir geolocation: {geo_err}")

        # Override timezone and locale at context level (stealth script)
        try:
            await context.add_init_script(f"""
                Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {{
                    value: function() {{
                        return {{ timeZone: '{identity["timezone"]}', locale: '{identity["locale"]}' }};
                    }}
                }});
            """)
        except Exception:
            pass  # Non-critical

        # Set default navigation timeout (extended for proxy latency)
        page.set_default_navigation_timeout(base_timeout)
        page.set_default_timeout(base_timeout)

        return p, browser, context, page

    # Retry with backoff for proxy/network failures
    return await retry_async(
        coro_factory=_attempt_launch,
        max_retries=max_retries,
        base_delay=3.0,
        max_delay=30.0,
        retryable_exceptions=(Exception,),
        context_label=f"launch_browser({profile_slug})"
    )


async def resilient_goto(
    page: Page,
    url: str,
    timeout: int = 120000,
    wait_until: str = "domcontentloaded",
    max_retries: int = 3,
):
    """
    Navigates to a URL with retry logic for proxy/network resilience.
    
    Args:
        page: Playwright Page instance.
        url: URL to navigate to.
        timeout: Navigation timeout in ms.
        wait_until: Load state to wait for.
        max_retries: Number of retry attempts.
    """
    from core.retry_utils import retry_async

    async def _attempt_goto():
        await page.goto(url, timeout=timeout, wait_until=wait_until)

    await retry_async(
        coro_factory=_attempt_goto,
        max_retries=max_retries,
        base_delay=3.0,
        max_delay=15.0,
        retryable_exceptions=(Exception,),
        context_label=f"page.goto({url[:60]})"
    )

