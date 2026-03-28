"""
Remote Browser Session Manager
Allows operators to manually interact with a browser running on the VPS
via noVNC (web-based VNC client). Used primarily for CAPTCHA solving.
"""
import os
import secrets
import signal
import asyncio
import logging
import json
import subprocess
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Singleton state for the active remote session
_active_session: Optional[Dict[str, Any]] = None

DISPLAY_NUM = 99
VNC_PORT = 5900
NOVNC_PORT = 6080
SESSION_TIMEOUT_HOURS = 4  # Auto-cleanup sessions older than this


def _kill_pid(pid: int):
    """Safely kill a process — try graceful SIGTERM first, then SIGKILL."""
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return
    # Give process 2s to exit gracefully
    import time
    for _ in range(4):
        time.sleep(0.5)
        try:
            os.kill(pid, 0)  # Check if still alive
        except OSError:
            return  # Process exited
    # Force kill if still alive
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        pass
    try:
        os.waitpid(pid, os.WNOHANG)
    except OSError:
        pass


def _build_stealth_init_script(fp: dict) -> str:
    """Returns the JavaScript init script for stealth browser overrides (per-profile fingerprint)."""
    from core.browser import CHROME_MAJOR
    return f"""
        Object.defineProperty(navigator, 'webdriver', {{get: () => false}});
        Object.defineProperty(navigator, 'platform', {{get: () => 'Win32'}});
        Object.defineProperty(navigator, 'oscpu', {{get: () => undefined}});
        Object.defineProperty(navigator, 'languages', {{get: () => ['pt-BR', 'pt', 'en-US', 'en']}});
        Object.defineProperty(navigator, 'hardwareConcurrency', {{get: () => {fp["cores"]}}});
        Object.defineProperty(navigator, 'deviceMemory', {{get: () => {fp["memory"]}}});
        Object.defineProperty(navigator, 'maxTouchPoints', {{get: () => {fp["max_touch_points"]}}});
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
                        architecture: 'x86', bitness: '64',
                        mobile: false, model: '', platform: 'Windows',
                        platformVersion: '15.0.0',
                    }}),
                }})
            }});
        }}
        (function() {{
            const gpuVendor = '{fp["gpu_vendor"]}';
            const gpuRenderer = '{fp["gpu_renderer"]}';
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
        try {{
            Object.defineProperty(screen, 'orientation', {{
                get: () => ({{
                    angle: 0,
                    type: 'landscape-primary',
                    onchange: null,
                    addEventListener: function() {{}},
                    removeEventListener: function() {{}},
                }})
            }});
        }} catch(e) {{}}
        if (!window.external || Object.keys(window.external).length === 0) {{
            window.external = {{
                AddSearchProvider: function() {{}},
                IsSearchProviderInstalled: function() {{ return false; }},
            }};
        }}
    """


def get_session_status() -> Dict[str, Any]:
    """Returns the current remote session status."""
    global _active_session
    if not _active_session:
        return {"active": False}

    # Auto-timeout: kill sessions that have been running too long
    started_at = _active_session.get("started_at")
    if started_at:
        import datetime
        try:
            start_dt = datetime.datetime.fromisoformat(started_at)
            elapsed_hours = (datetime.datetime.now() - start_dt).total_seconds() / 3600
            if elapsed_hours > SESSION_TIMEOUT_HOURS:
                logger.warning(f"[REMOTE] Session exceeded {SESSION_TIMEOUT_HOURS}h timeout ({elapsed_hours:.1f}h). Auto-stopping.")
                stop_session()
                return {"active": False}
        except (ValueError, TypeError):
            pass

    # Verify processes are still alive
    for key in ["xvfb_pid", "vnc_pid", "novnc_pid"]:
        pid = _active_session.get(key)
        if pid:
            try:
                os.kill(pid, 0)  # Signal 0 = check if alive
            except (ProcessLookupError, OSError):
                # Process died — session is stale
                logger.warning(f"[REMOTE] Process {key}={pid} is dead. Cleaning up session.")
                stop_session()
                return {"active": False}

    return {
        "active": True,
        "session_type": _active_session.get("session_type", "profile"),
        "profile_slug": _active_session.get("profile_slug"),
        "novnc_url": _active_session.get("novnc_url"),
        "started_at": _active_session.get("started_at"),
    }


async def start_session(profile_slug: str, host_url: str = "") -> Dict[str, Any]:
    """
    Starts a remote browser session with VNC access.

    1. Starts Xvfb (virtual display)
    2. Launches Chromium with persistent profile + cookies + proxy
    3. Navigates to TikTok Studio
    4. Starts x11vnc + noVNC websockify
    5. Returns the noVNC URL
    """
    global _active_session

    if _active_session:
        return {
            "error": "Já existe uma sessão remota ativa. Encerre-a primeiro.",
            "novnc_url": _active_session.get("novnc_url"),
        }

    logger.info(f"[REMOTE] Starting remote session for profile: {profile_slug}")

    # Kill any stale processes from previous sessions
    for proc_name in ["Xvfb", "x11vnc", "websockify", "chromium", "chrome"]:
        subprocess.run(["pkill", "-9", proc_name], capture_output=True)
    await asyncio.sleep(1)

    # Remove stale X lock file
    x_lock = f"/tmp/.X{DISPLAY_NUM}-lock"
    if os.path.exists(x_lock):
        try:
            os.remove(x_lock)
        except OSError:
            pass

    pids = {}

    try:
        # 1. Start Xvfb
        xvfb = subprocess.Popen(
            ["Xvfb", f":{DISPLAY_NUM}", "-screen", "0", "1920x1080x24", "-ac"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        os.environ["DISPLAY"] = f":{DISPLAY_NUM}"

        # Wait for Xvfb to be ready
        for i in range(20):
            await asyncio.sleep(0.3)
            if os.path.exists(x_lock):
                break
            # Check if Xvfb crashed
            if xvfb.poll() is not None:
                stderr = xvfb.stderr.read().decode() if xvfb.stderr else ""
                raise RuntimeError(f"Xvfb crashed: {stderr}")

        if not os.path.exists(x_lock):
            raise RuntimeError("Xvfb failed to create display lock file")

        pids["xvfb_pid"] = xvfb.pid
        logger.info(f"[REMOTE] Xvfb started on :{DISPLAY_NUM} (PID {xvfb.pid})")

        # 2. Resolve profile identity (proxy, cookies, etc.)
        from core.network_utils import get_profile_identity
        from core.session_manager import get_session_path

        identity = get_profile_identity(profile_slug)
        session_path = get_session_path(profile_slug)

        # Quick proxy health check before launching browser
        if identity.get("proxy"):
            try:
                import httpx
                proxy_cfg = identity["proxy"]
                server = proxy_cfg["server"]
                proto = "https" if "https" in server else "http"
                host_part = server.replace("http://", "").replace("https://", "")
                username = proxy_cfg.get("username", "")
                password = proxy_cfg.get("password", "")
                if username and password:
                    proxy_url = f"{proto}://{username}:{password}@{host_part}"
                else:
                    proxy_url = f"{proto}://{host_part}"
                async with httpx.AsyncClient(proxy=proxy_url, timeout=10) as client:
                    resp = await client.get("https://httpbin.org/ip")
                    proxy_ip = resp.json().get("origin", "?")
                    logger.info(f"[REMOTE] Proxy health OK: {proxy_ip}")
            except Exception as proxy_err:
                logger.warning(f"[REMOTE] Proxy health check failed: {proxy_err} — prosseguindo mesmo assim")

        # 3. Launch browser via Playwright (persistent context for cookie injection)
        from playwright.async_api import async_playwright

        pw = await async_playwright().start()

        proxy_config = None
        if identity.get("proxy"):
            proxy_config = identity["proxy"]

        # Use a dedicated Playwright-compatible profile (NOT the Brave profile)
        pw_profile_dir = f"/app/data/browser_profiles/{profile_slug}_playwright"
        os.makedirs(pw_profile_dir, exist_ok=True)

        # Configurar download path padrão via Chromium Preferences
        import json as _json
        default_dir = os.path.join(pw_profile_dir, "Default")
        os.makedirs(default_dir, exist_ok=True)
        prefs_path = os.path.join(default_dir, "Preferences")
        prefs = {}
        if os.path.exists(prefs_path):
            try:
                with open(prefs_path, "r") as f:
                    prefs = _json.load(f)
            except Exception:
                prefs = {}
        prefs.setdefault("download", {})
        prefs["download"]["default_directory"] = "/app/downloads"
        prefs["download"]["prompt_for_download"] = False
        with open(prefs_path, "w") as f:
            _json.dump(prefs, f)

        # Remove stale lock files from previous sessions
        # Use lexists() instead of exists() because SingletonLock is a symlink
        # and exists() returns False for broken symlinks (target = old container hostname)
        for lock_file in ["SingletonLock", "SingletonSocket", "SingletonCookie"]:
            lock_path = os.path.join(pw_profile_dir, lock_file)
            if os.path.lexists(lock_path):
                try:
                    os.remove(lock_path)
                    logger.info(f"[REMOTE] Removed stale lock: {lock_file}")
                except OSError:
                    pass

        # Use same User-Agent and stealth settings as the worker browser
        from core.network_utils import get_random_user_agent, DEFAULT_LOCALE, DEFAULT_TIMEZONE
        from core.browser import _generate_fingerprint

        ua = identity.get("user_agent") or get_random_user_agent()
        fp = _generate_fingerprint(profile_slug)

        # Pasta de downloads acessível pelo file picker
        downloads_dir = "/app/downloads"
        os.makedirs(downloads_dir, exist_ok=True)

        context = await pw.chromium.launch_persistent_context(
            pw_profile_dir,
            headless=False,
            channel="chromium",
            viewport={"width": 1920, "height": 1080},
            no_viewport=True,
            proxy=proxy_config,
            user_agent=ua,
            locale=DEFAULT_LOCALE,
            timezone_id=DEFAULT_TIMEZONE,
            downloads_path=downloads_dir,
            args=[
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-features=UserAgentClientHint",
                "--window-size=1920,1080",
                "--window-position=0,0",
            ],
            ignore_default_args=["--enable-automation"],
        )

        # Inject cookies from saved session
        if session_path and os.path.exists(session_path):
            try:
                with open(session_path, 'r') as f:
                    state = json.load(f)
                cookies = state.get("cookies", [])
                if cookies:
                    await context.add_cookies(cookies)
                    logger.info(f"[REMOTE] Injected {len(cookies)} cookies from {session_path}")
            except Exception as cookie_err:
                logger.warning(f"[REMOTE] Failed to inject cookies: {cookie_err}")

        # Navigate to TikTok Studio
        page = context.pages[0] if context.pages else await context.new_page()

        # Apply stealth: same init_script as worker browser (browser.py)
        try:
            from playwright_stealth import stealth_async
            await stealth_async(page)
        except ImportError:
            logger.warning("[REMOTE] playwright-stealth not installed")
        except Exception:
            pass

        await context.add_init_script(_build_stealth_init_script(fp))
        # Store playwright objects for cleanup (antes da navegação)
        pids["_pw"] = pw
        pids["_context"] = context

        # 5. Start x11vnc (VNC server) with per-session password + localhost-only
        vnc_password = secrets.token_urlsafe(8)

        vnc = subprocess.Popen(
            [
                "x11vnc",
                "-display", f":{DISPLAY_NUM}",
                "-passwd", vnc_password,
                "-forever",
                "-shared",
                "-rfbport", str(VNC_PORT),
                "-xkb",
                "-noxrecord",
                "-noxfixes",
                "-noxdamage",
                "-localhost",  # Only accept connections from localhost (websockify)
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        pids["vnc_pid"] = vnc.pid
        pids["_vnc_password"] = vnc_password
        await asyncio.sleep(1)
        logger.info(f"[REMOTE] x11vnc started on port {VNC_PORT} (PID {vnc.pid}) [password protected, localhost only]")

        # 6. Start noVNC websockify
        novnc = subprocess.Popen(
            [
                "websockify",
                "--web", "/usr/share/novnc",
                str(NOVNC_PORT),
                f"localhost:{VNC_PORT}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        pids["novnc_pid"] = novnc.pid
        await asyncio.sleep(1)
        logger.info(f"[REMOTE] noVNC websockify started on port {NOVNC_PORT} (PID {novnc.pid})")

        # Build noVNC URL (password auto-filled so operator doesn't need to type it)
        novnc_url = f"http://{host_url}:{NOVNC_PORT}/vnc.html?autoconnect=true&resize=scale&password={vnc_password}"

        import datetime
        _active_session = {
            "session_type": "profile",
            "profile_slug": profile_slug,
            "novnc_url": novnc_url,
            "started_at": datetime.datetime.now().isoformat(),
            **pids,
        }

        logger.info(f"[REMOTE] ✅ Session ready: {novnc_url}")

        # Navegação fire-and-forget: não bloqueia o response da API
        async def _navigate_background():
            try:
                await page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded", timeout=45000)
                logger.info("[REMOTE] Browser navigated to TikTok Studio (background)")
            except Exception as nav_err:
                logger.warning(f"[REMOTE] Navegação background falhou: {nav_err}")

        _active_session["_nav_task"] = asyncio.create_task(_navigate_background())

        return {
            "active": True,
            "novnc_url": novnc_url,
            "profile_slug": profile_slug,
            "message": "Sessão remota iniciada. Acesse o link para interagir com o browser.",
        }

    except Exception as e:
        logger.error(f"[REMOTE] Failed to start session: {e}")
        # Cleanup any started processes
        for pid in pids.values():
            _kill_pid(pid)
        return {"error": f"Falha ao iniciar sessão: {str(e)}"}


def stop_session() -> Dict[str, Any]:
    """Stops the active remote session and all associated processes."""
    global _active_session

    if not _active_session:
        return {"message": "Nenhuma sessão ativa."}

    profile = _active_session.get("profile_slug", "unknown")
    is_factory = _active_session.get("session_type") == "factory"
    logger.info(f"[REMOTE] Stopping {'factory' if is_factory else 'profile'} session for {profile}")

    pw_context = _active_session.get("_context")
    pw_browser = _active_session.get("_browser")  # Only set for factory sessions
    pw = _active_session.get("_pw")

    if pw_context:
        # Save cookies only for profile sessions with a valid slug
        if not is_factory and profile and profile != "unknown":
            try:
                from core.session_manager import get_session_path
                session_path = get_session_path(profile)
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(pw_context.storage_state(path=session_path))
                    logger.info(f"[REMOTE] Cookies salvos em {session_path}")
                else:
                    loop.run_until_complete(pw_context.storage_state(path=session_path))
                    logger.info(f"[REMOTE] Cookies salvos em {session_path}")
            except Exception as e:
                logger.warning(f"[REMOTE] Falha ao salvar cookies: {e}")

        # Close Playwright context gracefully
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(pw_context.close())
            else:
                loop.run_until_complete(pw_context.close())
        except Exception as e:
            logger.warning(f"[REMOTE] Error closing Playwright context: {e}")

    # Factory sessions use launch() + new_context() — must also close the Browser object
    if pw_browser:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(pw_browser.close())
            else:
                loop.run_until_complete(pw_browser.close())
        except Exception as e:
            logger.warning(f"[REMOTE] Error closing Browser: {e}")

    if pw:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(pw.stop())
            else:
                loop.run_until_complete(pw.stop())
        except Exception as e:
            logger.warning(f"[REMOTE] Error stopping Playwright: {e}")

    for key in ["vnc_pid", "novnc_pid", "xvfb_pid"]:
        pid = _active_session.get(key)
        if pid:
            _kill_pid(pid)
            logger.info(f"[REMOTE] Killed {key}: {pid}")

    # Kill any remaining orphan processes from this session
    for proc_name in ["chromium", "chrome", "x11vnc", "websockify"]:
        subprocess.run(["pkill", "-9", proc_name], capture_output=True)

    _active_session = None
    return {
        "message": f"Sessão remota encerrada para {profile}. Trust do browser salvo.",
        "active": False,
    }


async def start_factory_session(proxy_id: int, host_url: str = "") -> Dict[str, Any]:
    """
    Starts a fresh VNC session for creating a new TikTok profile.

    Unlike start_session(), this opens a clean ephemeral browser (no cookies,
    no persistent profile dir) navigating directly to the TikTok login page.
    The operator logs in manually via VNC, then calls capture_factory_profile().

    Proxy is REQUIRED — raises ValueError if proxy_id is invalid or inactive.
    """
    global _active_session

    if _active_session:
        return {
            "error": "Já existe uma sessão ativa. Encerre-a primeiro.",
            "novnc_url": _active_session.get("novnc_url"),
        }

    logger.info(f"[FACTORY] Starting factory session with proxy_id={proxy_id}")

    # Load proxy from DB — required
    from core.database import SessionLocal
    from core.models import Proxy as ProxyModel
    db = SessionLocal()
    try:
        proxy_obj = db.query(ProxyModel).filter(
            ProxyModel.id == proxy_id,
            ProxyModel.active == True,
        ).first()
        if not proxy_obj:
            return {"error": f"Proxy ID {proxy_id} não encontrado ou inativo."}
        proxy_config = {
            "server": proxy_obj.server,
            "username": proxy_obj.username,
            "password": proxy_obj.password,
        }
        proxy_display = proxy_obj.nickname or proxy_obj.name or proxy_obj.server
    finally:
        db.close()

    # Generate ephemeral fingerprint seed (not tied to any real profile)
    import time
    import datetime
    temp_seed = f"factory_{int(time.time())}"
    from core.browser import _generate_fingerprint, STEALTH_ARGS
    fp = _generate_fingerprint(temp_seed)

    # Kill stale processes
    for proc_name in ["Xvfb", "x11vnc", "websockify", "chromium", "chrome"]:
        subprocess.run(["pkill", "-9", proc_name], capture_output=True)
    await asyncio.sleep(1)

    x_lock = f"/tmp/.X{DISPLAY_NUM}-lock"
    if os.path.exists(x_lock):
        try:
            os.remove(x_lock)
        except OSError:
            pass

    pids = {}

    try:
        # Start Xvfb
        xvfb = subprocess.Popen(
            ["Xvfb", f":{DISPLAY_NUM}", "-screen", "0", "1920x1080x24", "-ac"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        os.environ["DISPLAY"] = f":{DISPLAY_NUM}"

        for _ in range(20):
            await asyncio.sleep(0.3)
            if os.path.exists(x_lock):
                break
            if xvfb.poll() is not None:
                stderr = xvfb.stderr.read().decode() if xvfb.stderr else ""
                raise RuntimeError(f"Xvfb crashed: {stderr}")

        if not os.path.exists(x_lock):
            raise RuntimeError("Xvfb failed to create display lock file")

        pids["xvfb_pid"] = xvfb.pid
        logger.info(f"[FACTORY] Xvfb started on :{DISPLAY_NUM} (PID {xvfb.pid})")

        # Launch ephemeral browser (no persistent profile dir)
        from playwright.async_api import async_playwright
        from core.network_utils import get_random_user_agent, DEFAULT_LOCALE, DEFAULT_TIMEZONE

        ua = get_random_user_agent()
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(
            headless=False,
            channel="chromium",
            args=STEALTH_ARGS + [
                "--window-size=1920,1080",
                "--window-position=0,0",
            ],
        )
        context = await browser.new_context(
            proxy=proxy_config,
            user_agent=ua,
            locale=DEFAULT_LOCALE,
            timezone_id=DEFAULT_TIMEZONE,
            viewport={"width": fp["viewport"]["width"], "height": fp["viewport"]["height"]},
            no_viewport=True,
        )

        page = await context.new_page()

        try:
            from playwright_stealth import stealth_async
            await stealth_async(page)
        except ImportError:
            logger.warning("[FACTORY] playwright-stealth not installed")
        except Exception:
            pass

        await context.add_init_script(_build_stealth_init_script(fp))

        pids["_pw"] = pw
        pids["_browser"] = browser
        pids["_context"] = context

        # Start x11vnc
        vnc_password = secrets.token_urlsafe(8)
        vnc = subprocess.Popen(
            [
                "x11vnc",
                "-display", f":{DISPLAY_NUM}",
                "-passwd", vnc_password,
                "-forever",
                "-shared",
                "-rfbport", str(VNC_PORT),
                "-xkb",
                "-noxrecord",
                "-noxfixes",
                "-noxdamage",
                "-localhost",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        pids["vnc_pid"] = vnc.pid
        pids["_vnc_password"] = vnc_password
        await asyncio.sleep(1)
        logger.info(f"[FACTORY] x11vnc started on port {VNC_PORT} (PID {vnc.pid})")

        # Start noVNC websockify
        novnc = subprocess.Popen(
            [
                "websockify",
                "--web", "/usr/share/novnc",
                str(NOVNC_PORT),
                f"localhost:{VNC_PORT}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        pids["novnc_pid"] = novnc.pid
        await asyncio.sleep(1)
        logger.info(f"[FACTORY] noVNC websockify started on port {NOVNC_PORT} (PID {novnc.pid})")

        novnc_url = f"http://{host_url}:{NOVNC_PORT}/vnc.html?autoconnect=true&resize=scale&password={vnc_password}"

        _active_session = {
            "session_type": "factory",
            "profile_slug": None,
            "proxy_id": proxy_id,
            "temp_seed": temp_seed,
            "factory_ua": ua,
            "novnc_url": novnc_url,
            "started_at": datetime.datetime.now().isoformat(),
            **pids,
        }

        logger.info(f"[FACTORY] ✅ Session ready for proxy '{proxy_display}': {novnc_url}")

        async def _navigate_factory():
            try:
                await page.goto("https://www.tiktok.com/login/", wait_until="domcontentloaded", timeout=45000)
                logger.info("[FACTORY] Browser navigated to TikTok login page")
            except Exception as nav_err:
                logger.warning(f"[FACTORY] Navegação background falhou: {nav_err}")

        nav_task = asyncio.create_task(_navigate_factory())
        _active_session["_nav_task"] = nav_task

        return {
            "active": True,
            "session_type": "factory",
            "novnc_url": novnc_url,
            "proxy": proxy_display,
            "message": f"Sessão fábrica iniciada com proxy '{proxy_display}'. Faça login no TikTok e clique em Capturar.",
        }

    except Exception as e:
        logger.error(f"[FACTORY] Failed to start factory session: {e}")
        for key, val in pids.items():
            if isinstance(val, int):
                _kill_pid(val)
        return {"error": f"Falha ao iniciar sessão fábrica: {str(e)}"}


async def capture_factory_profile(label: str | None = None, proxy_id: int | None = None) -> Dict[str, Any]:
    """
    Captures the TikTok session from an active factory VNC session.

    Reads cookies from the live browser context, validates login (sessionid cookie),
    fetches TikTok user info, creates a Profile in DB with the proxy bound,
    saves the session JSON, and stops the VNC.

    Raises RuntimeError if:
    - No factory session is active
    - User hasn't logged in yet (no sessionid cookie found)
    """
    global _active_session

    if not _active_session or _active_session.get("session_type") != "factory":
        raise RuntimeError("Nenhuma sessão fábrica ativa.")

    pw_context = _active_session.get("_context")
    if not pw_context:
        raise RuntimeError("Contexto Playwright não encontrado na sessão.")

    resolved_proxy_id = proxy_id or _active_session.get("proxy_id")
    ua = _active_session.get("factory_ua")

    logger.info(f"[FACTORY] Capturing profile from factory session (proxy_id={resolved_proxy_id})")

    # 1. Extract storage state (cookies) from live context
    import json as _json
    import time
    import tempfile

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".json", prefix="factory_capture_")
    os.close(tmp_fd)

    try:
        await pw_context.storage_state(path=tmp_path)
        with open(tmp_path, "r") as f:
            state = _json.load(f)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    cookies = state.get("cookies", [])

    # 2. Validate TikTok login via sessionid cookie
    has_session = any(
        c.get("name") == "sessionid" and ".tiktok.com" in c.get("domain", "")
        for c in cookies
    )
    if not has_session:
        raise RuntimeError(
            "Nenhum cookie de sessão TikTok encontrado. Complete o login antes de capturar."
        )

    logger.info(f"[FACTORY] Found {len(cookies)} cookies, sessionid present ✓")

    # 3. Build proxy URL for TikTok API calls
    proxy_url = None
    if resolved_proxy_id:
        from core.database import SessionLocal
        from core.models import Proxy as ProxyModel
        db = SessionLocal()
        try:
            p = db.query(ProxyModel).filter(ProxyModel.id == resolved_proxy_id).first()
            if p and p.server:
                server_raw = p.server.replace("http://", "").replace("https://", "")
                if p.username and p.password:
                    proxy_url = f"http://{p.username}:{p.password}@{server_raw}"
                else:
                    proxy_url = f"http://{server_raw}"
        finally:
            db.close()

    # 4. Fetch TikTok user info (best-effort, failure is non-blocking)
    user_info = None
    try:
        from core.tiktok_profile import fetch_tiktok_user_info
        cookies_dict = {c["name"]: c["value"] for c in cookies}
        user_info = fetch_tiktok_user_info(cookies_dict, proxy_url=proxy_url)
        logger.info(f"[FACTORY] TikTok user info: {user_info}")
    except Exception as e:
        logger.warning(f"[FACTORY] Could not fetch TikTok user info: {e}")

    username = user_info.get("username") if user_info else None
    display_name = user_info.get("display_name") if user_info else None
    avatar_url = user_info.get("avatar_url") if user_info else None
    final_label = label or display_name or username or f"Novo Perfil {int(time.time())}"

    # 5. Create profile in DB + save session file
    from core.session_manager import import_session
    profile_slug = import_session(
        label=final_label,
        cookies_json=_json.dumps(cookies),
        username=username,
        avatar_url=avatar_url,
        fingerprint=ua,
    )
    logger.info(f"[FACTORY] Profile created: {profile_slug}")

    # 6. Bind proxy to new profile
    if resolved_proxy_id:
        from core.database import SessionLocal
        from core.models import Profile
        db = SessionLocal()
        try:
            prof = db.query(Profile).filter(Profile.slug == profile_slug).first()
            if prof:
                prof.proxy_id = resolved_proxy_id
                db.commit()
                logger.info(f"[FACTORY] Proxy {resolved_proxy_id} bound to {profile_slug}")
        except Exception as e:
            logger.warning(f"[FACTORY] Failed to bind proxy: {e}")
            db.rollback()
        finally:
            db.close()

    # 7. Tear down VNC (stop_session handles process cleanup)
    # Patch profile_slug so stop_session guard routes correctly
    _active_session["profile_slug"] = profile_slug
    stop_session()

    return {
        "profile_id": profile_slug,
        "username": username,
        "label": final_label,
        "avatar_url": avatar_url,
        "message": f"Perfil '{final_label}' capturado com sucesso!",
    }
