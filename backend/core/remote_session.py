"""
Remote Browser Session Manager
Allows operators to manually interact with a browser running on the VPS
via noVNC (web-based VNC client). Used primarily for CAPTCHA solving.
"""
import os
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


def _kill_pid(pid: int):
    """Safely kill a process tree by PID."""
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        pass
    # Also try to reap zombies
    try:
        os.waitpid(pid, os.WNOHANG)
    except OSError:
        pass


def get_session_status() -> Dict[str, Any]:
    """Returns the current remote session status."""
    global _active_session
    if not _active_session:
        return {"active": False}

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

        # 3. Launch browser via Playwright (persistent context for cookie injection)
        from playwright.async_api import async_playwright

        pw = await async_playwright().start()

        proxy_config = None
        if identity.get("proxy"):
            proxy_config = identity["proxy"]

        # Use a dedicated Playwright-compatible profile (NOT the Brave profile)
        pw_profile_dir = f"/app/data/browser_profiles/{profile_slug}_playwright"
        os.makedirs(pw_profile_dir, exist_ok=True)

        # Remove stale lock files from previous sessions
        for lock_file in ["SingletonLock", "SingletonSocket", "SingletonCookie"]:
            lock_path = os.path.join(pw_profile_dir, lock_file)
            if os.path.exists(lock_path):
                try:
                    os.remove(lock_path)
                except OSError:
                    pass

        # Use same User-Agent and stealth settings as the worker browser
        from core.network_utils import get_random_user_agent, DEFAULT_LOCALE, DEFAULT_TIMEZONE
        from core.browser import CHROME_VERSION, CHROME_MAJOR, STEALTH_ARGS

        ua = identity.get("user_agent") or get_random_user_agent()

        context = await pw.chromium.launch_persistent_context(
            user_data_dir=pw_profile_dir,
            headless=False,
            channel="chromium",
            viewport={"width": 1920, "height": 1080},
            no_viewport=True,
            proxy=proxy_config,
            user_agent=ua,
            locale=DEFAULT_LOCALE,
            timezone_id=DEFAULT_TIMEZONE,
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

        await context.add_init_script(f"""
            Object.defineProperty(navigator, 'webdriver', {{get: () => undefined}});
            Object.defineProperty(navigator, 'languages', {{get: () => ['pt-BR', 'pt', 'en-US', 'en']}});
            Object.defineProperty(navigator, 'hardwareConcurrency', {{get: () => 8}});
            Object.defineProperty(navigator, 'deviceMemory', {{get: () => 8}});
            Object.defineProperty(navigator, 'maxTouchPoints', {{get: () => 0}});
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
        """)
        await page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded", timeout=30000)
        logger.info("[REMOTE] Browser navigated to TikTok Studio")

        # Store playwright objects for cleanup
        pids["_pw"] = pw
        pids["_context"] = context

        await asyncio.sleep(2)  # Let page render

        # 5. Start x11vnc (VNC server)
        vnc = subprocess.Popen(
            [
                "x11vnc",
                "-display", f":{DISPLAY_NUM}",
                "-nopw",  # No password (internal network / SSH tunnel)
                "-forever",
                "-shared",
                "-rfbport", str(VNC_PORT),
                "-xkb",
                "-noxrecord",
                "-noxfixes",
                "-noxdamage",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        pids["vnc_pid"] = vnc.pid
        await asyncio.sleep(1)
        logger.info(f"[REMOTE] x11vnc started on port {VNC_PORT} (PID {vnc.pid})")

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

        # Build noVNC URL
        novnc_url = f"http://{host_url}:{NOVNC_PORT}/vnc.html?autoconnect=true&resize=scale"

        import datetime
        _active_session = {
            "profile_slug": profile_slug,
            "novnc_url": novnc_url,
            "started_at": datetime.datetime.now().isoformat(),
            **pids,
        }

        logger.info(f"[REMOTE] ✅ Session ready: {novnc_url}")
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
    logger.info(f"[REMOTE] Stopping session for {profile}")

    # Close Playwright context gracefully (saves cookies/state)
    pw_context = _active_session.get("_context")
    pw = _active_session.get("_pw")
    if pw_context:
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(pw_context.close())
            else:
                loop.run_until_complete(pw_context.close())
        except Exception as e:
            logger.warning(f"[REMOTE] Error closing Playwright context: {e}")
    if pw:
        try:
            import asyncio
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

    # Kill any remaining chromium processes
    subprocess.run(["pkill", "-9", "chromium"], capture_output=True)

    _active_session = None
    return {
        "message": f"Sessão remota encerrada para {profile}. Trust do browser salvo.",
        "active": False,
    }
