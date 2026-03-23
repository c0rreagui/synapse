import os
import re
import logging
import sys
import asyncio
import subprocess
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

# Path to Chromium in Docker: prefer system apt binary, fallback to Playwright's bundled one
def _resolve_chromium_path() -> Optional[str]:
    if not IN_DOCKER:
        return None
    # 1) System apt-installed chromium
    if os.path.isfile("/usr/bin/chromium"):
        return "/usr/bin/chromium"
    # 2) Playwright's bundled chromium (installed via `playwright install chromium`)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            pw_path = p.chromium.executable_path
            if pw_path and os.path.isfile(pw_path):
                return pw_path
    except Exception:
        pass
    # 3) Let Playwright auto-detect (no explicit path)
    return None

SYSTEM_CHROMIUM_PATH = _resolve_chromium_path()

# --- Dynamic Chrome Version Detection ---
def _get_chrome_version() -> str:
    """Detect the real Chromium version from the binary in the container."""
    paths_to_try = [
        SYSTEM_CHROMIUM_PATH,
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
    ]
    for path in paths_to_try:
        if path and os.path.isfile(path):
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True, text=True, timeout=5
                )
                # Parse "Chromium 146.0.7680.71 ..." or "Google Chrome 146..."
                match = re.search(r'(\d+)\.\d+\.\d+\.\d+', result.stdout)
                if match:
                    full_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    version = full_match.group(1) if full_match else f"{match.group(1)}.0.0.0"
                    logger.info(f"[STEALTH] Detected real Chrome version: {version}")
                    return version
            except Exception as e:
                logger.warning(f"[STEALTH] Failed to detect Chrome version from {path}: {e}")
    # Fallback: modern version
    logger.warning("[STEALTH] Could not detect Chrome version, using fallback 131.0.0.0")
    return "131.0.0.0"

CHROME_VERSION = _get_chrome_version()
CHROME_MAJOR = CHROME_VERSION.split(".")[0]

# Dynamic User-Agent based on real Chrome version
DYNAMIC_UA = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{CHROME_VERSION} Safari/537.36"

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
    # WebRTC leak protection — prevent real VPS IP from leaking through proxy
    "--webrtc-ip-handling-policy=disable_non_proxied_udp",
    "--enforce-webrtc-ip-permission-check",
]

# Extra args needed for Docker/headless environment
# NOTE: --single-process REMOVED — causes Chrome instability in Docker
# AND is a known fingerprint signal for anti-bot detection systems (TikTok).
DOCKER_HEADLESS_ARGS = [
    "--headless=new",  # New headless mode (Chrome 109+)
    "--disable-software-rasterizer",
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
        if os.environ.get("DISPLAY"):
            # Verify the DISPLAY is actually usable (Xvfb might have died)
            _display_num = os.environ["DISPLAY"].replace(":", "")
            _lock_path = f"/tmp/.X{_display_num}-lock"
            if os.path.exists(_lock_path):
                try:
                    with open(_lock_path) as _lf:
                        _xvfb_pid = int(_lf.read().strip())
                    os.kill(_xvfb_pid, 0)  # Check if alive
                    logger.info(f"[DOCKER] Xvfb DETECTED (DISPLAY={os.environ['DISPLAY']}, PID={_xvfb_pid}). Maintaining headless=False.")
                except (ProcessLookupError, OSError, ValueError):
                    logger.warning(f"[DOCKER] Stale DISPLAY={os.environ['DISPLAY']} (Xvfb dead). Restarting...")
                    os.environ.pop("DISPLAY", None)
                    try:
                        os.remove(_lock_path)
                    except OSError:
                        pass
            else:
                logger.info(f"[DOCKER] Xvfb DETECTED (DISPLAY={os.environ['DISPLAY']}). Maintaining headless=False.")

        if not os.environ.get("DISPLAY"):
            # Auto-start Xvfb so we can run headful (avoids TikTok CAPTCHA on headless)
            try:
                # Clean stale lock files from previous sessions
                _lock_path = "/tmp/.X99-lock"
                if os.path.exists(_lock_path):
                    try:
                        os.remove(_lock_path)
                        logger.info("[DOCKER] Removed stale Xvfb lock file")
                    except OSError:
                        pass
                # Kill any zombie Xvfb processes
                subprocess.run(["pkill", "-9", "Xvfb"], capture_output=True)
                import time; time.sleep(0.5)

                _xvfb = subprocess.Popen(
                    ["Xvfb", ":99", "-screen", "0", "1920x1080x24", "-ac"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                os.environ["DISPLAY"] = ":99"
                import time; time.sleep(2)  # Wait longer for Xvfb to be ready
                # Verify Xvfb actually started
                if _xvfb.poll() is not None:
                    raise RuntimeError(f"Xvfb exited immediately with code {_xvfb.returncode}")
                logger.info(f"[DOCKER] Auto-started Xvfb :99 (PID {_xvfb.pid}). Running headful.")
            except Exception as e:
                logger.warning(f"[DOCKER] Failed to start Xvfb: {e}. Forcing headless=True.")
                headless = True
    

    # Build args list
    browser_args = STEALTH_ARGS.copy()
    if IN_DOCKER and headless:
        browser_args.extend(DOCKER_HEADLESS_ARGS)
        logger.info(f"[BROWSER] Docker headless mode - added {len(DOCKER_HEADLESS_ARGS)} extra args")
    elif IN_DOCKER and not headless:
        # Headful in Docker: add non-headless Docker args (no --headless=new!)
        browser_args.extend([
            "--disable-software-rasterizer",
        ])
        logger.info("[BROWSER] Docker headful mode (Xvfb)")
    elif headless:
        # On Windows/local, we might need fewer flags for stability
        # But we still want some basic ones for headless
        browser_args.append("--headless=new")
        logger.info("[BROWSER] Headless mode (native)")

    # Dynamically build --disable-features to avoid Chrome last-one-wins conflict
    disable_features = ["UserAgentClientHint"]  # Prevent Sec-CH-UA-Platform: "Linux" leak
    if IN_DOCKER and headless:
        disable_features.append("VizDisplayCompositor")
    browser_args.append(f"--disable-features={','.join(disable_features)}")

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

            # Inject cookies from storage_state into persistent context
            # (persistent context doesn't accept storage_state param, so we load manually)
            if storage_state and os.path.exists(storage_state):
                try:
                    import json
                    with open(storage_state, 'r') as f:
                        state = json.load(f)
                    cookies = state.get("cookies", [])
                    if cookies:
                        await context.add_cookies(cookies)
                        logger.info(f"[BROWSER] ✅ Injected {len(cookies)} cookies from {storage_state} into persistent context")
                except Exception as cookie_err:
                    logger.warning(f"[BROWSER] Failed to inject cookies from storage_state: {cookie_err}")

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
        
        # Apply playwright-stealth
        try:
            from playwright_stealth import stealth_async
            await stealth_async(page)
            logger.info("[STEALTH] playwright-stealth applied successfully.")
        except ImportError:
            logger.warning("[STEALTH] playwright-stealth not installed. Skipping advanced stealth injection.")
        except Exception as e:
            logger.warning(f"[STEALTH] Failed to apply playwright-stealth: {e}")

        # Hardware Spoofing to match a standard desktop profile
        await context.add_init_script("""
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
        """)
        
        # Stealth injection - comprehensive anti-detection (Common for both)
        await context.add_init_script(f"""
            // === 1. Hide webdriver flag ===
            Object.defineProperty(navigator, 'webdriver', {{get: () => undefined}});
            
            // === 2. Realistic navigator.languages ===
            Object.defineProperty(navigator, 'languages', {{get: () => ['pt-BR', 'pt', 'en-US', 'en']}});
            
            // === 3. Realistic navigator.plugins (PDF Viewer + Chrome PDF Plugin) ===
            (function() {{
                const makePlugin = (name, filename, desc) => {{
                    const p = Object.create(Plugin.prototype);
                    Object.defineProperties(p, {{
                        name: {{value: name, enumerable: true}},
                        filename: {{value: filename, enumerable: true}},
                        description: {{value: desc, enumerable: true}},
                        length: {{value: 1, enumerable: true}},
                    }});
                    return p;
                }};
                const plugins = [
                    makePlugin('PDF Viewer', 'internal-pdf-viewer', 'Portable Document Format'),
                    makePlugin('Chrome PDF Plugin', 'internal-pdf-viewer', 'Portable Document Format'),
                    makePlugin('Chrome PDF Viewer', 'mhjfbmdgcfjbbpaeojofohoefgiehjai', 'Portable Document Format'),
                    makePlugin('Microsoft Edge PDF Viewer', 'internal-pdf-viewer', 'Portable Document Format'),
                    makePlugin('WebKit built-in PDF', 'internal-pdf-viewer', 'Portable Document Format'),
                ];
                Object.defineProperty(navigator, 'plugins', {{
                    get: () => {{
                        const arr = Object.create(PluginArray.prototype);
                        plugins.forEach((p, i) => {{ arr[i] = p; }});
                        Object.defineProperty(arr, 'length', {{value: plugins.length}});
                        arr.item = (i) => plugins[i];
                        arr.namedItem = (n) => plugins.find(p => p.name === n);
                        arr.refresh = () => {{}};
                        return arr;
                    }}
                }});
                Object.defineProperty(navigator, 'mimeTypes', {{
                    get: () => {{
                        const mt = Object.create(MimeTypeArray.prototype);
                        const pdf = Object.create(MimeType.prototype);
                        Object.defineProperties(pdf, {{
                            type: {{value: 'application/pdf'}},
                            suffixes: {{value: 'pdf'}},
                            description: {{value: 'Portable Document Format'}},
                            enabledPlugin: {{value: plugins[0]}},
                        }});
                        mt[0] = pdf;
                        Object.defineProperty(mt, 'length', {{value: 1}});
                        mt.item = (i) => i === 0 ? pdf : null;
                        mt.namedItem = (n) => n === 'application/pdf' ? pdf : null;
                        return mt;
                    }}
                }});
            }})();
            
            // === 4. Desktop maxTouchPoints (0 = no touchscreen) ===
            Object.defineProperty(navigator, 'maxTouchPoints', {{get: () => 0}});
            
            // === 5. Full chrome.runtime object ===
            window.chrome = {{
                runtime: {{
                    connect: function() {{ return {{ onMessage: {{ addListener: function() {{}} }}, postMessage: function() {{}} }}; }},
                    sendMessage: function(msg, cb) {{ if (cb) cb(); }},
                    getURL: function(path) {{ return 'chrome-extension://placeholder/' + path; }},
                    id: undefined,
                    onMessage: {{ addListener: function() {{}}, removeListener: function() {{}} }},
                    onConnect: {{ addListener: function() {{}}, removeListener: function() {{}} }},
                    getManifest: function() {{ return {{}}; }},
                }},
                loadTimes: function() {{ return {{ requestTime: Date.now() / 1000, startLoadTime: Date.now() / 1000 }}; }},
                csi: function() {{ return {{ pageT: Date.now(), startE: Date.now() }}; }},
                app: {{ isInstalled: false, InstallState: {{ INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' }}, RunningState: {{ CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }} }},
            }};
            
            // === 6. NavigatorUAData matching real Chrome version ===
            if (!navigator.userAgentData) {{
                Object.defineProperty(navigator, 'userAgentData', {{
                    get: () => ({{
                        brands: [
                            {{brand: 'Not/A)Brand', version: '8'}},
                            {{brand: 'Chromium', version: '{CHROME_MAJOR}'}},
                            {{brand: 'Google Chrome', version: '{CHROME_MAJOR}'}},
                        ],
                        mobile: false,
                        platform: 'Windows',
                        getHighEntropyValues: (hints) => Promise.resolve({{
                            architecture: 'x86',
                            bitness: '64',
                            brands: [
                                {{brand: 'Not/A)Brand', version: '8.0.0.0'}},
                                {{brand: 'Chromium', version: '{CHROME_VERSION}'}},
                                {{brand: 'Google Chrome', version: '{CHROME_VERSION}'}},
                            ],
                            fullVersionList: [
                                {{brand: 'Not/A)Brand', version: '8.0.0.0'}},
                                {{brand: 'Chromium', version: '{CHROME_VERSION}'}},
                                {{brand: 'Google Chrome', version: '{CHROME_VERSION}'}},
                            ],
                            mobile: false,
                            model: '',
                            platform: 'Windows',
                            platformVersion: '15.0.0',
                            uaFullVersion: '{CHROME_VERSION}',
                            wow64: false,
                        }}),
                    }})
                }});
            }}
            
            // === 7. Override permissions ===
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({{ state: Notification.permission }}) :
                    originalQuery(parameters)
            );
            
            // === 8. WebGL fingerprint protection (Linux-compatible renderer) ===
            (function() {{
                const getParameterOrig = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(param) {{
                    // UNMASKED_VENDOR_WEBGL
                    if (param === 0x9245) return 'Google Inc. (NVIDIA Corporation)';
                    // UNMASKED_RENDERER_WEBGL
                    if (param === 0x9246) return 'ANGLE (NVIDIA Corporation, NVIDIA GeForce GTX 1660 SUPER/PCIe/SSE2, OpenGL 4.5.0)';
                    return getParameterOrig.call(this, param);
                }};
                // Also patch WebGL2
                if (typeof WebGL2RenderingContext !== 'undefined') {{
                    const getParam2Orig = WebGL2RenderingContext.prototype.getParameter;
                    WebGL2RenderingContext.prototype.getParameter = function(param) {{
                        if (param === 0x9245) return 'Google Inc. (NVIDIA Corporation)';
                        if (param === 0x9246) return 'ANGLE (NVIDIA Corporation, NVIDIA GeForce GTX 1660 SUPER/PCIe/SSE2, OpenGL 4.5.0)';
                        return getParam2Orig.call(this, param);
                    }};
                }}
            }})();
            
            // === 9. Canvas fingerprint: no noise injection (deterministic is safer) ===
            
            // === 10. Disable Notification constructor to avoid headless leak ===
            if (typeof Notification !== 'undefined' && Notification.permission === 'denied') {{
                Object.defineProperty(Notification, 'permission', {{get: () => 'default'}});
            }}
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

    # --- Persistent Context Detection ---
    # If a browser profile directory exists for this profile, use persistent context
    # instead of ephemeral + storage_state. Carries accumulated trust (localStorage,
    # IndexedDB, service worker registrations) which helps bypass CAPTCHA.
    browser_profile_dir = None
    _profile_base = os.environ.get("BROWSER_PROFILES_DIR", "/app/data/browser_profiles")
    # Use the Playwright-compatible profile (created/trusted via VNC remote session).
    # This shares trust (cookies, localStorage, CAPTCHA clearance) with the VNC session.
    # VNC session must be stopped before the worker uses it.
    _pw_candidate = os.path.join(_profile_base, f"{profile_slug}_playwright")
    if os.path.isdir(_pw_candidate):
        browser_profile_dir = _pw_candidate
        # Remove stale lock files (from VNC session that was stopped)
        for lf in ["SingletonLock", "SingletonSocket", "SingletonCookie"]:
            lp = os.path.join(browser_profile_dir, lf)
            try:
                os.remove(lp)
            except OSError:
                pass
        logger.info(f"[BROWSER] ✅ Playwright profile found: {browser_profile_dir}")
    else:
        logger.info(f"[BROWSER] No persistent profile found, using ephemeral + storage_state")

    async def _attempt_launch():
        p, browser, context, page = await launch_browser(
            headless=headless,
            proxy=proxy_config,
            user_agent=identity["user_agent"],
            viewport=identity["viewport"],
            storage_state=storage_state,
            user_data_dir=browser_profile_dir,
        )

        # Apply geolocation if available
        if identity["geolocation"]:
            try:
                await context.set_geolocation(identity["geolocation"])
                await context.grant_permissions(["geolocation"])
                logger.info(f"[BROWSER] Geolocation definida: {identity['geolocation']}")
            except Exception as geo_err:
                logger.warning(f"[BROWSER] Falha ao definir geolocation: {geo_err}")

        # NOTE: Intl.DateTimeFormat override REMOVED — it returned an incomplete
        # resolvedOptions() object (missing calendar, numberingSystem, etc.)
        # which is trivially detected by anti-bot systems. The timezone is
        # already set correctly via Playwright's timezone_id context option.

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

