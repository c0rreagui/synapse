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
    "--disable-infobars",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--disable-setuid-sandbox",
    # NOTE: --disable-gpu removed — only used in headless mode (DOCKER_HEADLESS_ARGS).
    # Passing it to VNC sessions (headless=False) breaks WebGL stealth.
    "--no-first-run",
    "--no-default-browser-check",
    "--ignore-certificate-errors",
    # WebRTC leak protection — block ALL non-proxied connections (UDP + TCP)
    "--webrtc-ip-handling-policy=disable_non_proxied_udp",
    "--enforce-webrtc-ip-permission-check",
    # Close CDP debugging port — TikTok probes for open DevTools protocol
    "--remote-debugging-port=0",
    # DNS-over-HTTPS to prevent DNS queries leaking to VPS provider
    "--dns-over-https-mode=secure",
    "--dns-over-https-templates=https://dns.google/dns-query",
]

# Extra args needed for Docker/headless environment
# NOTE: --single-process REMOVED — causes Chrome instability in Docker
# AND is a known fingerprint signal for anti-bot detection systems (TikTok).
DOCKER_HEADLESS_ARGS = [
    "--headless=new",  # New headless mode (Chrome 109+)
    "--disable-software-rasterizer",
    "--disable-gpu",  # Only for headless — never pass to VNC sessions
]

# Identidade Dinâmica centralizada em core.network_utils
from core.network_utils import get_random_user_agent, DEFAULT_LOCALE, DEFAULT_TIMEZONE

from core.process_manager import process_manager

def _generate_fingerprint(seed: str = "") -> Dict[str, Any]:
    """Gera fingerprint de hardware determinístico baseado no seed (profile slug).
    Cada perfil terá hardware 'diferente' mas consistente entre sessões."""
    import hashlib
    h = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    cores_options = [4, 6, 8, 10, 12, 16]
    memory_options = [4, 8, 8, 16]
    gpu_options = [
        "ANGLE (NVIDIA Corporation, NVIDIA GeForce GTX 1660 SUPER/PCIe/SSE2, OpenGL 4.5.0)",
        "ANGLE (NVIDIA Corporation, NVIDIA GeForce RTX 2060/PCIe/SSE2, OpenGL 4.5.0)",
        "ANGLE (NVIDIA Corporation, NVIDIA GeForce GTX 1070/PCIe/SSE2, OpenGL 4.5.0)",
        "ANGLE (NVIDIA Corporation, NVIDIA GeForce RTX 3060/PCIe/SSE2, OpenGL 4.5.0)",
        "ANGLE (Intel, Intel(R) UHD Graphics 630, OpenGL 4.5.0)",
        "ANGLE (AMD, AMD Radeon RX 580/PCIe/SSE2, OpenGL 4.5.0)",
    ]
    vendor_map = {
        "NVIDIA": "Google Inc. (NVIDIA Corporation)",
        "Intel": "Google Inc. (Intel)",
        "AMD": "Google Inc. (AMD)",
    }
    # maxTouchPoints: 0 = no touchscreen (desktop), 1-5 = touchscreen laptop
    touch_options = [0, 0, 0, 0, 1, 5, 10]  # 57% desktop, 43% touch
    # Common desktop resolutions (weighted toward 1920x1080)
    viewport_options = [
        {"width": 1920, "height": 1080},
        {"width": 1920, "height": 1080},
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1536, "height": 864},
        {"width": 1440, "height": 900},
        {"width": 2560, "height": 1440},
    ]
    gpu = gpu_options[h % len(gpu_options)]
    vendor_key = "NVIDIA" if "NVIDIA" in gpu else ("Intel" if "Intel" in gpu else "AMD")
    return {
        "cores": cores_options[(h >> 4) % len(cores_options)],
        "memory": memory_options[(h >> 8) % len(memory_options)],
        "gpu_renderer": gpu,
        "gpu_vendor": vendor_map[vendor_key],
        "max_touch_points": touch_options[(h >> 12) % len(touch_options)],
        "viewport": viewport_options[(h >> 16) % len(viewport_options)],
        # Deterministic noise seeds for canvas/audio fingerprinting (0-15 int, tiny float)
        "canvas_noise": (h >> 20) % 16,
        "audio_noise": ((h >> 24) & 0xFF) / 1e12,
    }


async def launch_browser(
    headless: bool = True,
    proxy: Optional[Dict[str, str]] = None,
    user_agent: str = None, # Será pegue do network_utils se None
    viewport: Optional[Dict[str, int]] = None,
    storage_state: Optional[str] = None,
    user_data_dir: Optional[str] = None, # Persistent Context Path
    fingerprint_seed: str = "", # Seed para fingerprint único por perfil
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
        # Fingerprint único por perfil (determinístico via seed)
        fp = _generate_fingerprint(fingerprint_seed or user_data_dir or "default")
        fp_cores = fp["cores"]
        fp_memory = fp["memory"]
        fp_gpu_renderer = fp["gpu_renderer"]
        fp_gpu_vendor = fp["gpu_vendor"]
        fp_touch = fp["max_touch_points"]

        await context.add_init_script(f"""
            Object.defineProperty(navigator, 'hardwareConcurrency', {{get: () => {fp_cores}}});
            Object.defineProperty(navigator, 'deviceMemory', {{get: () => {fp_memory}}});
        """)
        
        # Stealth injection - comprehensive anti-detection (Common for both)
        await context.add_init_script(f"""
            // === 1. Hide webdriver flag ===
            Object.defineProperty(navigator, 'webdriver', {{get: () => false}});
            
            // === 2. Platform consistency (must match UA "Windows NT 10.0") ===
            Object.defineProperty(navigator, 'platform', {{get: () => 'Win32'}});
            Object.defineProperty(navigator, 'oscpu', {{get: () => undefined}});

            // === 3. Realistic navigator.languages ===
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
            
            // === 4. maxTouchPoints (per-profile via fingerprint) ===
            Object.defineProperty(navigator, 'maxTouchPoints', {{get: () => {fp_touch}}});
            
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
                webstore: {{ onInstallStageChanged: {{}}, onDownloadProgress: {{}} }},
            }};
            // Protect chrome object from detection via toString
            window.chrome.runtime.connect.toString = () => 'function connect() {{ [native code] }}';
            window.chrome.runtime.sendMessage.toString = () => 'function sendMessage() {{ [native code] }}';
            
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
            
            // === 7. Override permissions (all common types) ===
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => {{
                const granted = ['notifications', 'geolocation', 'microphone', 'camera'];
                if (granted.includes(parameters.name)) {{
                    return Promise.resolve({{ state: 'prompt', onchange: null }});
                }}
                return originalQuery(parameters);
            }};

            // === 7b. navigator.credentials (real browsers have this) ===
            if (!navigator.credentials) {{
                Object.defineProperty(navigator, 'credentials', {{
                    get: () => ({{
                        create: () => Promise.resolve(null),
                        get: () => Promise.resolve(null),
                        preventSilentAccess: () => Promise.resolve(),
                        store: () => Promise.resolve(),
                    }})
                }});
            }}

            // === 7c. navigator.connection (Network Information API) ===
            if (!navigator.connection) {{
                Object.defineProperty(navigator, 'connection', {{
                    get: () => ({{
                        effectiveType: '4g',
                        rtt: 50,
                        downlink: 10,
                        saveData: false,
                        onchange: null,
                        addEventListener: function() {{}},
                        removeEventListener: function() {{}},
                    }})
                }});
            }}

            // === 7d. navigator.getBattery() ===
            if (!navigator.getBattery) {{
                navigator.getBattery = () => Promise.resolve({{
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 1.0,
                    onchargingchange: null,
                    onchargingtimechange: null,
                    ondischargingtimechange: null,
                    onlevelchange: null,
                    addEventListener: function() {{}},
                    removeEventListener: function() {{}},
                }});
            }}

            // === 7e. mediaDevices.enumerateDevices() ===
            if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {{
                const origEnum = navigator.mediaDevices.enumerateDevices.bind(navigator.mediaDevices);
                navigator.mediaDevices.enumerateDevices = () => Promise.resolve([
                    {{deviceId: 'default', kind: 'audioinput', label: '', groupId: 'default'}},
                    {{deviceId: 'default', kind: 'audiooutput', label: '', groupId: 'default'}},
                    {{deviceId: 'default', kind: 'videoinput', label: '', groupId: 'default'}},
                ]);
            }}
            
            // === 8. WebGL fingerprint protection (unique per profile) ===
            (function() {{
                const gpuVendor = '{fp_gpu_vendor}';
                const gpuRenderer = '{fp_gpu_renderer}';
                const getParameterOrig = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(param) {{
                    if (param === 0x9245) return gpuVendor;
                    if (param === 0x9246) return gpuRenderer;
                    return getParameterOrig.call(this, param);
                }};
                if (typeof WebGL2RenderingContext !== 'undefined') {{
                    const getParam2Orig = WebGL2RenderingContext.prototype.getParameter;
                    WebGL2RenderingContext.prototype.getParameter = function(param) {{
                        if (param === 0x9245) return gpuVendor;
                        if (param === 0x9246) return gpuRenderer;
                        return getParam2Orig.call(this, param);
                    }};
                }}
            }})();
            
            // === 8a. WebGL extensions normalization ===
            (function() {{
                // Return a consistent set of extensions (common on desktop Chrome + NVIDIA/Intel/AMD)
                const commonExtensions = [
                    'ANGLE_instanced_arrays', 'EXT_blend_minmax', 'EXT_color_buffer_half_float',
                    'EXT_float_blend', 'EXT_frag_depth', 'EXT_shader_texture_lod',
                    'EXT_texture_filter_anisotropic', 'OES_element_index_uint',
                    'OES_standard_derivatives', 'OES_texture_float', 'OES_texture_float_linear',
                    'OES_texture_half_float', 'OES_texture_half_float_linear',
                    'OES_vertex_array_object', 'WEBGL_color_buffer_float',
                    'WEBGL_compressed_texture_s3tc', 'WEBGL_debug_renderer_info',
                    'WEBGL_depth_texture', 'WEBGL_draw_buffers', 'WEBGL_lose_context',
                ];
                const origGetExts = WebGLRenderingContext.prototype.getSupportedExtensions;
                WebGLRenderingContext.prototype.getSupportedExtensions = function() {{
                    return commonExtensions;
                }};
                if (typeof WebGL2RenderingContext !== 'undefined') {{
                    const origGetExts2 = WebGL2RenderingContext.prototype.getSupportedExtensions;
                    WebGL2RenderingContext.prototype.getSupportedExtensions = function() {{
                        return [...commonExtensions, 'EXT_color_buffer_float', 'OES_draw_buffers_indexed'];
                    }};
                }}
            }})();

            // === 8b. Canvas fingerprint noise (per-profile, deterministic) ===
            (function() {{
                // Seed-based noise: small pixel-level perturbation unique to this profile
                const seed = {fp_cores * 1000 + fp_memory * 100 + fp_touch};
                const noiseLevel = 0.02;  // Imperceptible noise
                const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function(type, quality) {{
                    const ctx = this.getContext('2d');
                    if (ctx && this.width > 0 && this.height > 0) {{
                        try {{
                            const imageData = ctx.getImageData(0, 0, Math.min(this.width, 16), Math.min(this.height, 16));
                            for (let i = 0; i < imageData.data.length; i += 4) {{
                                // Deterministic per-profile noise using seed
                                const noise = ((seed * (i + 1) * 9301 + 49297) % 233280) / 233280.0;
                                if (noise < noiseLevel) {{
                                    imageData.data[i] = imageData.data[i] ^ 1;  // Flip LSB of red channel
                                }}
                            }}
                            ctx.putImageData(imageData, 0, 0);
                        }} catch(e) {{}}  // Skip if tainted canvas (CORS)
                    }}
                    return origToDataURL.call(this, type, quality);
                }};
                // Also protect toBlob
                const origToBlob = HTMLCanvasElement.prototype.toBlob;
                HTMLCanvasElement.prototype.toBlob = function(cb, type, quality) {{
                    this.toDataURL(type, quality);  // Apply noise first
                    return origToBlob.call(this, cb, type, quality);
                }};
            }})();

            // === 8c. AudioContext fingerprint protection ===
            (function() {{
                if (typeof AudioContext !== 'undefined' || typeof webkitAudioContext !== 'undefined') {{
                    const AC = AudioContext || webkitAudioContext;
                    const origCreateOscillator = AC.prototype.createOscillator;
                    const origCreateDynamicsCompressor = AC.prototype.createDynamicsCompressor;
                    // Wrap createDynamicsCompressor to add subtle per-profile variation
                    AC.prototype.createDynamicsCompressor = function() {{
                        const compressor = origCreateDynamicsCompressor.call(this);
                        // Slightly vary default threshold per profile (imperceptible audio change)
                        const offset = ({fp_cores} % 5) * 0.001;
                        try {{
                            compressor.threshold.value = -24 + offset;
                            compressor.knee.value = 30 + offset;
                        }} catch(e) {{}}
                        return compressor;
                    }};
                    // Wrap getFloatFrequencyData to add noise
                    const origGetFloat = AnalyserNode.prototype.getFloatFrequencyData;
                    AnalyserNode.prototype.getFloatFrequencyData = function(array) {{
                        origGetFloat.call(this, array);
                        const noiseSeed = {fp_memory * 37 + fp_cores};
                        for (let i = 0; i < array.length; i++) {{
                            array[i] += ((noiseSeed * (i + 1) * 7919) % 100) / 100000.0;
                        }}
                    }};
                }}
            }})();

            // === 9. WebRTC IP leak prevention (JS-level) ===
            (function() {{
                const origRTC = window.RTCPeerConnection || window.webkitRTCPeerConnection;
                if (origRTC) {{
                    const Wrapped = function(config, constraints) {{
                        if (config && config.iceServers) {{
                            config.iceServers = [];
                        }}
                        return new origRTC(config, constraints);
                    }};
                    Wrapped.prototype = origRTC.prototype;
                    window.RTCPeerConnection = Wrapped;
                    if (window.webkitRTCPeerConnection) window.webkitRTCPeerConnection = Wrapped;
                }}
            }})();

            // === 10. Disable Notification constructor to avoid headless leak ===
            if (typeof Notification !== 'undefined' && Notification.permission === 'denied') {{
                Object.defineProperty(Notification, 'permission', {{get: () => 'default'}});
            }}

            // === 11. screen.orientation (Windows desktop default) ===
            try {{
                Object.defineProperty(screen, 'orientation', {{
                    get: () => ({{
                        angle: 0,
                        type: 'landscape-primary',
                        onchange: null,
                        addEventListener: function() {{}},
                        removeEventListener: function() {{}},
                        lock: function() {{ return Promise.reject(new DOMException('screen.orientation.lock() is not available on this device.')); }},
                        unlock: function() {{}},
                    }})
                }});
            }} catch(e) {{}}

            // === 12. window.external (IE/Edge legacy — Chrome on Windows has it) ===
            if (!window.external || Object.keys(window.external).length === 0) {{
                window.external = {{
                    AddSearchProvider: function() {{}},
                    IsSearchProviderInstalled: function() {{ return false; }},
                }};
            }}

            // === 13. window.name (should be empty on fresh navigation) ===
            if (window.name && window.name.length > 0) {{
                window.name = '';
            }}

            // === 14. Protect injected properties from Reflect.ownKeys detection ===
            // Wrap navigator.permissions.query toString to look native
            try {{
                const origPQ = navigator.permissions.query;
                navigator.permissions.query.toString = () => 'function query() {{ [native code] }}';
            }} catch(e) {{}}
            // Wrap getBattery
            try {{
                if (navigator.getBattery) {{
                    navigator.getBattery.toString = () => 'function getBattery() {{ [native code] }}';
                }}
            }} catch(e) {{}}
            // Wrap mediaDevices.enumerateDevices
            try {{
                if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {{
                    navigator.mediaDevices.enumerateDevices.toString = () => 'function enumerateDevices() {{ [native code] }}';
                }}
            }} catch(e) {{}}

            // === 15. requestIdleCallback normalization ===
            // In headless, idle callbacks fire immediately. Add realistic delay.
            if (window.requestIdleCallback) {{
                const origRIC = window.requestIdleCallback.bind(window);
                window.requestIdleCallback = function(cb, opts) {{
                    return origRIC(function(deadline) {{
                        // Wrap deadline to report realistic timeRemaining
                        const wrapped = {{
                            didTimeout: deadline.didTimeout,
                            timeRemaining: () => Math.min(deadline.timeRemaining(), 49.9),
                        }};
                        cb(wrapped);
                    }}, opts);
                }};
                window.requestIdleCallback.toString = () => 'function requestIdleCallback() {{ [native code] }}';
            }}

            // === 16. Sanitize Error.stack traces (remove Playwright/puppeteer references) ===
            (function() {{
                const origPrepare = Error.prepareStackTrace;
                Error.prepareStackTrace = function(error, stack) {{
                    if (origPrepare) {{
                        const result = origPrepare(error, stack);
                        if (typeof result === 'string') {{
                            return result.replace(/playwright|puppeteer|__playwright/gi, 'anonymous');
                        }}
                        return result;
                    }}
                    return error.stack;
                }};
            }})();
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


USE_DOLPHIN_UPLOADS = os.getenv("USE_DOLPHIN_UPLOADS", "false").lower() == "true"


async def launch_browser_for_profile(
    profile_slug: str,
    headless: bool = not IN_DOCKER,  # Docker: headful via Xvfb (avoids --headless=new detection)
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

    # Dolphin{anty} upload mode: use real Chrome + hardware-level fingerprint spoofing
    if USE_DOLPHIN_UPLOADS:
        try:
            from core.remote_session import launch_browser_via_dolphin
            logger.info(f"[BROWSER] USE_DOLPHIN_UPLOADS=true — lançando via Dolphin para '{profile_slug}'")
            return await launch_browser_via_dolphin(profile_slug)
        except Exception as dolphin_err:
            logger.warning(
                f"[BROWSER] Dolphin upload falhou ({dolphin_err}) — fallback para Playwright padrão"
            )
            # Falls through to standard Playwright flow below

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
        # Guard: do NOT use persistent profile if VNC session is active for this profile
        # (two Chromium instances sharing the same profile = corruption + detection)
        from core.remote_session import get_session_status
        vnc_status = get_session_status()
        if vnc_status.get("active") and vnc_status.get("profile_slug") == profile_slug:
            logger.warning(f"[BROWSER] VNC session active for '{profile_slug}' — using ephemeral context to avoid profile lock conflict")
        else:
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
            fingerprint_seed=profile_slug,
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

