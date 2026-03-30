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
import httpx
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Singleton state for the active remote session
_active_session: Optional[Dict[str, Any]] = None

DISPLAY_NUM = 99
VNC_PORT = 5900
NOVNC_PORT = 6080
SESSION_TIMEOUT_HOURS = 4  # Auto-cleanup sessions older than this

# --- Dolphin{anty} antidetect browser ---
DOLPHIN_API_URL = "http://localhost:3001/v1.0"
DOLPHIN_API_TOKEN = os.getenv("DOLPHIN_API_TOKEN", "")
DOLPHIN_EMAIL = os.getenv("DOLPHIN_EMAIL", "")
DOLPHIN_PASSWORD = os.getenv("DOLPHIN_PASSWORD", "")
DOLPHIN_ELECTRON_PORT = 9222  # Electron DevTools port for UI automation (clicking START)
_dolphin_session_token: Optional[str] = None  # Local session token (from email/password login)

# Persistent Xvfb + Dolphin PIDs — kept alive between factory sessions so
# Dolphin doesn't need to re-contact the "choose host" server on every start.
_persistent_xvfb_pid: Optional[int] = None
_persistent_dolphin_pid: Optional[int] = None


def _pid_alive(pid: int) -> bool:
    """Returns True if the process with given PID is still running."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _xdotool_maximize_chrome():
    """Resize the Dolphin{anty} window to fill the full 1920×1080 virtual display.

    Chrome runs INSIDE Dolphin's Electron shell — it is not a standalone window.
    The top-level window has WM_CLASS='dolphin_anty'. We target it directly
    and exclude tiny utility windows (< 100px) that also carry the same class.
    """
    env = {**os.environ, "DISPLAY": f":{DISPLAY_NUM}"}
    try:
        result = subprocess.run(
            ["xdotool", "search", "--class", "dolphin_anty"],
            env=env, capture_output=True, text=True, timeout=5,
        )
        candidates = [w for w in result.stdout.strip().split() if w]

        resized = 0
        for win_id in candidates:
            # Skip tiny internal windows (clipboard managers, hidden helpers)
            geo = subprocess.run(
                ["xdotool", "getwindowgeometry", win_id],
                env=env, capture_output=True, text=True, timeout=3,
            )
            lines = geo.stdout.strip().splitlines()
            geom_line = next((l for l in lines if "Geometry:" in l), "")
            if geom_line:
                parts = geom_line.split()[-1].split("x")
                if len(parts) == 2:
                    w, h = int(parts[0]), int(parts[1])
                    if w < 100 or h < 100:
                        continue  # skip utility/hidden window

            subprocess.run(["xdotool", "windowsize", win_id, "1920", "1080"], env=env, capture_output=True)
            subprocess.run(["xdotool", "windowmove", win_id, "0", "0"], env=env, capture_output=True)
            resized += 1

        if resized:
            logger.info(f"[REMOTE] xdotool: Dolphin window maximized to 1920×1080")
        else:
            logger.warning(f"[REMOTE] xdotool: no dolphin_anty window found (candidates={candidates})")
    except Exception as e:
        logger.warning(f"[REMOTE] xdotool maximize failed: {e}")


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


def _dolphin_port_responding() -> bool:
    """Returns True if Dolphin Electron DevTools port is listening."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        result = s.connect_ex(("127.0.0.1", DOLPHIN_ELECTRON_PORT))
        s.close()
        return result == 0
    except Exception:
        return False


async def _ensure_xvfb():
    """Ensure Xvfb is running on :{DISPLAY_NUM}. Reuses existing PID if alive."""
    global _persistent_xvfb_pid
    x_lock = f"/tmp/.X{DISPLAY_NUM}-lock"
    if _persistent_xvfb_pid and _pid_alive(_persistent_xvfb_pid):
        os.environ["DISPLAY"] = f":{DISPLAY_NUM}"
        logger.info(f"[DOLPHIN] Reusing Xvfb PID {_persistent_xvfb_pid}")
        return
    # Clean up and start fresh
    if os.path.exists(x_lock):
        try:
            os.remove(x_lock)
        except OSError:
            pass
    subprocess.run(["pkill", "-9", "Xvfb"], capture_output=True)
    await asyncio.sleep(0.5)
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
            raise RuntimeError(f"Xvfb crashed on start: {stderr}")
    if not os.path.exists(x_lock):
        raise RuntimeError("Xvfb failed to create display lock file")
    _persistent_xvfb_pid = xvfb.pid
    logger.info(f"[DOLPHIN] Xvfb started on :{DISPLAY_NUM} (PID {xvfb.pid})")


def _ensure_dolphin():
    """Ensure Dolphin is running with --remote-debugging-port={DOLPHIN_ELECTRON_PORT}.
    Restarts if alive but missing the debug port (old launch without the flag).

    PORT-FIRST strategy: if port 9222 is already responding, adopt the existing
    Dolphin process (find PID via pgrep) without starting a new one. This is critical
    for upload workers that run in a fresh Python process where _persistent_dolphin_pid=None
    but Dolphin is already running from a VNC session.
    """
    global _persistent_dolphin_pid

    # PORT-FIRST: if port is already responding, adopt the existing process
    if _dolphin_port_responding():
        if _persistent_dolphin_pid and _pid_alive(_persistent_dolphin_pid):
            logger.info(f"[DOLPHIN] Reusing Dolphin PID {_persistent_dolphin_pid} (port {DOLPHIN_ELECTRON_PORT} OK)")
        else:
            # Port responding but PID not tracked — find and adopt existing process
            try:
                result = subprocess.run(
                    ["pgrep", "-f", "dolphin_anty"],
                    capture_output=True, text=True,
                )
                pids = [int(p) for p in result.stdout.strip().split() if p.isdigit()]
                if pids:
                    _persistent_dolphin_pid = pids[0]
                    logger.info(f"[DOLPHIN] Adopted existing Dolphin PID {_persistent_dolphin_pid} (port {DOLPHIN_ELECTRON_PORT} responding)")
                else:
                    logger.info(f"[DOLPHIN] Port {DOLPHIN_ELECTRON_PORT} responding, no PID found — external process")
            except Exception:
                logger.info(f"[DOLPHIN] Port {DOLPHIN_ELECTRON_PORT} responding, adopted without PID tracking")
        return

    # Port not responding — check if PID is alive without port (started without debug flag)
    if _persistent_dolphin_pid and _pid_alive(_persistent_dolphin_pid):
        logger.info(f"[DOLPHIN] Dolphin PID {_persistent_dolphin_pid} alive but port {DOLPHIN_ELECTRON_PORT} not responding — restarting with debug port")
        _kill_pid(_persistent_dolphin_pid)
        _persistent_dolphin_pid = None
        import time
        time.sleep(1)

    _patch_dolphin_chrome()
    
    # Redireciona os logs do Dolphin para arquivo para podermos debugar se ele 'crashar' silenciosamente
    dolphin_log = open("/app/data/dolphin_electron.log", "a")
    
    proc = subprocess.Popen(
        [
            "dolphin_anty", 
            "--no-sandbox", 
            "--disable-gpu", 
            "--disable-dev-shm-usage", 
            f"--remote-debugging-port={DOLPHIN_ELECTRON_PORT}"
        ],
        env={**os.environ, "DISPLAY": f":{DISPLAY_NUM}"},
        stdout=dolphin_log,
        stderr=subprocess.STDOUT,
    )
    _persistent_dolphin_pid = proc.pid
    logger.info(f"[DOLPHIN] Dolphin started (PID {proc.pid}) with debug port {DOLPHIN_ELECTRON_PORT}")


async def _dolphin_login() -> str:
    """Login to Dolphin local app with email/password. Returns session token."""
    global _dolphin_session_token
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(
            f"{DOLPHIN_API_URL}/auth/login",
            json={"username": DOLPHIN_EMAIL, "password": DOLPHIN_PASSWORD},
        )
        resp = r.json()
        logger.info(f"[FACTORY] Dolphin login response (status {r.status_code}): success={resp.get('success')}")
        if not resp.get("success"):
            raise RuntimeError(f"Dolphin login falhou: {resp}")
        _dolphin_session_token = resp["token"]
        logger.info("[FACTORY] Dolphin sessão autenticada com sucesso.")
        return _dolphin_session_token


def _patch_dolphin_chrome():
    """Wrap Dolphin's Chrome binary to force --no-sandbox (required when running as root in Docker).
    Also patches all existing Dolphin profile Preferences to redirect downloads to /app/downloads.
    Safe to call multiple times — binary patch skips if wrapper already exists.
    """
    import glob as _glob
    import shutil
    import json as _json

    # 1. Patch Chrome binary wrapper
    for chrome_bin in _glob.glob("/root/.config/dolphin_anty/browser/*/chrome"):
        real_bin = chrome_bin + ".real"
        if os.path.exists(real_bin):
            continue  # already patched
        try:
            # Check it's actually an ELF binary, not already a wrapper
            if open(chrome_bin, "rb").read(4) != b"\x7fELF":
                continue
            shutil.copy2(chrome_bin, real_bin)
            os.chmod(real_bin, 0o755)
            wrapper = '#!/bin/bash\nexec "$(dirname "$0")/chrome.real" --no-sandbox --disable-gpu --disable-dev-shm-usage --remote-debugging-port=0 --start-maximized "$@"\n'
            open(chrome_bin, "w").write(wrapper)
            os.chmod(chrome_bin, 0o755)
            logger.info(f"[FACTORY] Patched Dolphin Chrome binary: {chrome_bin}")
        except Exception as e:
            logger.warning(f"[FACTORY] Could not patch Chrome binary {chrome_bin}: {e}")

    # 2. Ensure /root/Downloads symlink → /app/downloads (Chrome default download dir)
    downloads_dir = "/app/downloads"
    os.makedirs(downloads_dir, exist_ok=True)
    root_dl = "/root/Downloads"
    # Force symlink even if a real directory already exists (Chrome creates it before symlink)
    if os.path.isdir(root_dl) and not os.path.islink(root_dl):
        try:
            shutil.rmtree(root_dl)
        except OSError:
            pass
    if not os.path.lexists(root_dl):
        try:
            os.symlink(downloads_dir, root_dl)
            logger.info(f"[FACTORY] Created /root/Downloads → {downloads_dir} symlink")
        except OSError:
            pass

    # 3. Patch all existing Dolphin profile Preferences to redirect downloads
    for prefs_path in _glob.glob("/root/.config/dolphin_anty/browser_profiles/**/Preferences", recursive=True):
        try:
            with open(prefs_path, "r") as fh:
                prefs = _json.load(fh)
            dl = prefs.setdefault("download", {})
            if dl.get("default_directory") == downloads_dir:
                continue  # already patched
            dl["default_directory"] = downloads_dir
            dl["prompt_for_download"] = False
            with open(prefs_path, "w") as fh:
                _json.dump(prefs, fh)
            logger.info(f"[FACTORY] Patched download dir in {prefs_path}")
        except Exception as e:
            logger.warning(f"[FACTORY] Could not patch Preferences {prefs_path}: {e}")


def _start_dolphin_app():
    """Launch the Dolphin{anty} Electron app in background. Returns Popen object.
    Delegates to _ensure_dolphin() which handles the persistent PID + debug port.
    Kept for backward compatibility with callers.
    """
    _ensure_dolphin()
    # Return a dummy-compatible object using the persistent PID
    import types
    obj = types.SimpleNamespace(pid=_persistent_dolphin_pid)
    return obj


async def _dolphin_create_profile(proxy_config: dict, ua: str) -> str:
    """Create an ephemeral Dolphin profile with the given proxy + UA. Returns profile_id."""
    from urllib.parse import urlparse
    import time
    server = proxy_config.get("server", "")
    parsed = urlparse(server if server.startswith("http") else f"http://{server}")
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(
            f"{DOLPHIN_API_URL}/browser_profiles",
            headers={"Authorization": f"Bearer {_dolphin_session_token}"},
            json={
                "name": f"factory_{int(time.time())}",
                "platform": "windows",
                "browser_type": "anty",
                "useragent": {"mode": "manual", "value": ua},
                "webrtc": {"mode": "altered"},
                "canvas": {"mode": "noise"},
                "webgl": {"mode": "real"},
                "timezone": {"mode": "auto"},
                "locale": {"mode": "auto"},
                "proxy": {
                    "type": parsed.scheme or "http",
                    "host": parsed.hostname or "",
                    "port": parsed.port or 80,
                    "login": proxy_config.get("username") or "",
                    "password": proxy_config.get("password") or "",
                },
            },
        )
        resp = r.json()
        if not resp.get("success"):
            raise RuntimeError(f"Dolphin create profile falhou: {resp}")
        profile_id = str(resp["data"]["id"])
        logger.info(f"[FACTORY] Dolphin profile created: {profile_id}")
        return profile_id


async def _dolphin_start_browser(profile_id: str) -> str:
    """Start the Dolphin profile browser. Returns CDP WebSocket endpoint."""
    async with httpx.AsyncClient(timeout=40) as c:
        r = await c.get(
            f"{DOLPHIN_API_URL}/browser_profiles/{profile_id}/start",
            headers={"Authorization": f"Bearer {_dolphin_session_token}"},
            params={"automation": "1"},
        )
        resp = r.json()
        if not resp.get("success"):
            raise RuntimeError(f"Dolphin start browser falhou: {resp}")
        # Handle different response shapes across API versions
        automation = resp.get("automation") or resp.get("data", {})
        ws = automation.get("wsEndpoint") or automation.get("ws")
        if ws:
            return ws
        port = automation.get("port")
        if port:
            return f"ws://localhost:{port}"
        raise RuntimeError(f"Dolphin start response sem wsEndpoint/port: {resp}")


async def _dolphin_delete_profile(profile_id: str):
    """Delete Dolphin profile (stops browser + frees free-plan slot)."""
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            await c.delete(
                f"{DOLPHIN_API_URL}/browser_profiles/{profile_id}",
                headers={"Authorization": f"Bearer {_dolphin_session_token}"},
            )
        logger.info(f"[FACTORY] Dolphin profile {profile_id} deleted.")
    except Exception as e:
        logger.warning(f"[FACTORY] Erro ao deletar perfil Dolphin {profile_id}: {e}")


def _build_stealth_init_script(fp: dict) -> str:
    """Returns the JavaScript init script for stealth browser overrides (per-profile fingerprint)."""
    from core.browser import CHROME_MAJOR
    return f"""
        // Webdriver — deletar apenas, não redefinir.
        // Com ignore_default_args=["--enable-automation"], o Chrome não seta navigator.webdriver.
        // Qualquer Object.defineProperty aqui CRIARIA um descriptor, que é exatamente o que o "WebDriver (New)" detecta.
        (function() {{
            try {{ delete Object.getPrototypeOf(navigator).webdriver; }} catch(e) {{}}
            try {{ delete navigator.webdriver; }} catch(e) {{}}
        }})();
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
        // Canvas fingerprinting noise — deterministic per-session, defeats hash-based tracking
        // Only intercepts toDataURL (not getImageData — would corrupt transparent pixels / TRANSPARENT_PIXEL test)
        (function() {{
            const NOISE = {fp["canvas_noise"]};
            const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type, ...args) {{
                const ctx = this.getContext('2d');
                if (ctx && this.width > 0 && this.height > 0) {{
                    const orig = ctx.getImageData(0, 0, 1, 1);
                    const noisy = ctx.createImageData(1, 1);
                    noisy.data[0] = (orig.data[0] + NOISE) & 255;
                    noisy.data[1] = orig.data[1];
                    noisy.data[2] = orig.data[2];
                    noisy.data[3] = orig.data[3] === 0 ? 1 : orig.data[3]; // keep non-zero alpha
                    ctx.putImageData(noisy, 0, 0);
                    const result = origToDataURL.call(this, type, ...args);
                    ctx.putImageData(orig, 0, 0); // restore original pixel
                    return result;
                }}
                return origToDataURL.call(this, type, ...args);
            }};
        }})();
        // window.chrome — guarantee it exists even if playwright-stealth fails
        if (!window.chrome || Object.keys(window.chrome).length === 0) {{
            window.chrome = {{
                app: {{ isInstalled: false, InstallState: {{}}, RunningState: {{}} }},
                runtime: {{ OnInstalledReason: {{}}, OnRestartRequiredReason: {{}}, PlatformArch: {{}}, PlatformOs: {{}} }},
                loadTimes: function() {{ return {{}}; }},
                csi: function() {{ return {{ startE: Date.now(), onloadT: Date.now(), pageT: 1.5, tran: 15 }}; }},
            }};
        }}
        // AudioContext fingerprinting noise — defeats oscillator hash
        (function() {{
            const ANOISE = {fp["audio_noise"]};
            if (typeof AudioBuffer !== 'undefined') {{
                const origGetChannelData = AudioBuffer.prototype.getChannelData;
                AudioBuffer.prototype.getChannelData = function(channel) {{
                    const arr = origGetChannelData.call(this, channel);
                    if (arr.length > 0) arr[0] = arr[0] + ANOISE;
                    return arr;
                }};
            }}
        }})();
        // navigator.connection — simulate real broadband (undefined = bot signal)
        if (!navigator.connection) {{
            Object.defineProperty(navigator, 'connection', {{
                get: () => ({{
                    downlink: 10, effectiveType: '4g', rtt: 50,
                    saveData: false, type: 'wifi', onchange: null,
                }})
            }});
        }}
        // screen dimensions — sync with Xvfb virtual display
        try {{
            Object.defineProperty(screen, 'width', {{ get: () => {fp["viewport"]["width"]} }});
            Object.defineProperty(screen, 'height', {{ get: () => {fp["viewport"]["height"]} }});
            Object.defineProperty(screen, 'availWidth', {{ get: () => {fp["viewport"]["width"]} }});
            Object.defineProperty(screen, 'availHeight', {{ get: () => {fp["viewport"]["height"]} - 40 }});
        }} catch(e) {{}}
        // navigator.plugins — empty length = immediate bot signal; Chrome has 5 plugins
        // Safety net if playwright-stealth fails to apply its own plugins spoof
        (function() {{
            if (navigator.plugins.length === 0) {{
                const makeMime = (type, suf, desc) => ({{ type, suffixes: suf, description: desc, enabledPlugin: null }});
                const makePlugin = (name, desc, filename, mimes) => {{
                    const p = {{ name, description: desc, filename, length: mimes.length }};
                    mimes.forEach((m, i) => {{ m.enabledPlugin = p; p[i] = m; }});
                    p.item = (i) => p[i] || null;
                    p.namedItem = (n) => mimes.find(m => m.type === n) || null;
                    return p;
                }};
                const plugins = [
                    makePlugin('PDF Viewer', 'Portable Document Format', 'internal-pdf-viewer',
                        [makeMime('application/pdf','pdf',''), makeMime('text/pdf','pdf','')]),
                    makePlugin('Chrome PDF Viewer', '', 'internal-pdf-viewer',
                        [makeMime('application/pdf','pdf','')]),
                    makePlugin('Chromium PDF Viewer', '', 'internal-pdf-viewer',
                        [makeMime('application/pdf','pdf','')]),
                    makePlugin('Microsoft Edge PDF Viewer', '', 'internal-pdf-viewer',
                        [makeMime('application/pdf','pdf','')]),
                    makePlugin('WebKit built-in PDF', '', 'internal-pdf-viewer',
                        [makeMime('application/pdf','pdf','')]),
                ];
                const arr = Object.assign([], plugins, {{
                    item: (i) => plugins[i] || null,
                    namedItem: (n) => plugins.find(p => p.name === n) || null,
                    refresh: () => {{}},
                    [Symbol.iterator]: function*() {{ for (const p of plugins) yield p; }}
                }});
                try {{ Object.defineProperty(navigator, 'plugins', {{ get: () => arr, configurable: true }}); }} catch(e) {{}}
                const allMimes = plugins.flatMap(p => Array.from({{length: p.length}}, (_, i) => p[i]));
                const mimeArr = Object.assign([], allMimes, {{
                    item: (i) => allMimes[i] || null,
                    namedItem: (type) => allMimes.find(m => m.type === type) || null,
                    [Symbol.iterator]: function*() {{ for (const m of allMimes) yield m; }}
                }});
                try {{ Object.defineProperty(navigator, 'mimeTypes', {{ get: () => mimeArr, configurable: true }}); }} catch(e) {{}}
            }}
        }})();
        // navigator.permissions — "denied" for notifications = bot signal; real Chrome returns "default"
        (function() {{
            if (navigator.permissions && navigator.permissions.query) {{
                const origQuery = navigator.permissions.query.bind(navigator.permissions);
                navigator.permissions.query = (desc) => {{
                    if (desc && desc.name === 'notifications') {{
                        return Promise.resolve({{ state: 'default', onchange: null }});
                    }}
                    return origQuery(desc);
                }};
            }}
        }})();
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
            viewport={"width": 1280, "height": 720},
            no_viewport=True,
            proxy=proxy_config,
            user_agent=ua,
            locale=DEFAULT_LOCALE,
            timezone_id=DEFAULT_TIMEZONE,
            downloads_path=downloads_dir,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-infobars",
                "--disable-features=UserAgentClientHint",
                "--window-size=1280,720",
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
    is_factory = _active_session.get("session_type") in ("factory", "profile_dolphin")
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

    # Dolphin{anty} — delete ephemeral profile (stops browser + frees free-plan slot)
    dolphin_profile_id = _active_session.get("dolphin_profile_id")
    if dolphin_profile_id:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(_dolphin_delete_profile(dolphin_profile_id))
            else:
                loop.run_until_complete(_dolphin_delete_profile(dolphin_profile_id))
        except Exception as e:
            logger.warning(f"[REMOTE] Failed to delete Dolphin profile {dolphin_profile_id}: {e}")

    if is_factory:
        # Factory sessions: keep Xvfb + Dolphin alive so next session doesn't need
        # to re-contact the Dolphin "choose host" server on startup.
        # Only kill x11vnc and noVNC (VNC display layers).
        for key in ["vnc_pid", "novnc_pid"]:
            pid = _active_session.get(key)
            if pid:
                _kill_pid(pid)
                logger.info(f"[REMOTE] Killed {key}: {pid}")
        # Kill Chromium browser (opened by Dolphin profile) but NOT dolphin_anty/xvfb
        subprocess.run(["pkill", "-9", "chrome"], capture_output=True)
        subprocess.run(["pkill", "-9", "x11vnc"], capture_output=True)
        subprocess.run(["pkill", "-9", "websockify"], capture_output=True)
        logger.info("[REMOTE] Factory stop: Xvfb + Dolphin kept alive for next session.")
    else:
        for key in ["vnc_pid", "novnc_pid", "xvfb_pid"]:
            pid = _active_session.get(key)
            if pid:
                _kill_pid(pid)
                logger.info(f"[REMOTE] Killed {key}: {pid}")
        # Kill any remaining orphan processes from this session
        for proc_name in ["chromium", "chrome", "x11vnc", "websockify", "dolphin_anty"]:
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

    import time
    import datetime
    temp_seed = f"factory_{int(time.time())}"
    from core.network_utils import get_random_user_agent
    ua = get_random_user_agent()

    global _persistent_xvfb_pid, _persistent_dolphin_pid

    # Kill stale VNC processes (but NOT Xvfb/Dolphin if they're already alive)
    for proc_name in ["x11vnc", "websockify", "chrome"]:
        subprocess.run(["pkill", "-9", proc_name], capture_output=True)
    await asyncio.sleep(0.5)

    pids = {}

    try:
        # 1. Ensure Xvfb running
        await _ensure_xvfb()
        pids["xvfb_pid"] = _persistent_xvfb_pid

        # 2. Ensure Dolphin running (with --remote-debugging-port)
        _ensure_dolphin()
        pids["dolphin_pid"] = _persistent_dolphin_pid

        # 3. Start x11vnc — user can see and interact with Dolphin immediately
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

        # 4. Start noVNC websockify
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

        # Set session immediately so VNC is accessible
        _active_session = {
            "session_type": "factory",
            "profile_slug": None,
            "proxy_id": proxy_id,
            "proxy_config": proxy_config,
            "temp_seed": temp_seed,
            "factory_ua": ua,
            "novnc_url": novnc_url,
            "started_at": datetime.datetime.now().isoformat(),
            **pids,
        }

        logger.info(f"[FACTORY] ✅ VNC ready for proxy '{proxy_display}'. Aguardando login no Dolphin...")

        # 5. Background task: detect Dolphin browser start via DevToolsActivePort file
        async def _dolphin_ready_and_navigate():
            import glob as _glob
            dolphin_profiles_dir = "/root/.config/dolphin_anty/browser_profiles"

            # Wait for Dolphin to fully start (profiles dir appears)
            logger.info("[FACTORY] Aguardando Dolphin iniciar...")
            for _ in range(60):
                await asyncio.sleep(1)
                if os.path.isdir(dolphin_profiles_dir):
                    break

            _patch_dolphin_chrome()  # patch any newly downloaded Chrome binary

            # Dolphin window is now visible — maximize it immediately so the user
            # sees a full-screen VNC right away (before clicking START on a profile)
            await asyncio.sleep(2)
            _xdotool_maximize_chrome()

            # Remove stale DevToolsActivePort files from previous sessions
            # (Chrome leaves these behind when killed with SIGKILL)
            import socket as _socket
            for stale_dtp in _glob.glob(f"{dolphin_profiles_dir}/**/DevToolsActivePort", recursive=True):
                try:
                    port_str = open(stale_dtp).readline().strip()
                    if port_str.isdigit():
                        sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
                        sock.settimeout(0.3)
                        result = sock.connect_ex(("127.0.0.1", int(port_str)))
                        sock.close()
                        if result != 0:  # port not listening → stale file
                            os.remove(stale_dtp)
                            logger.info(f"[FACTORY] Removed stale DevToolsActivePort: {stale_dtp}")
                except Exception:
                    pass

            logger.info("[FACTORY] Dolphin pronto! Aguardando usuário clicar START em um perfil (até 10 min)...")

            # Poll for DevToolsActivePort — Chrome creates this file when started with debugging
            # Dolphin creates it for each running browser profile
            cdp_endpoint = None
            for i in range(600):  # 10 minutes max
                await asyncio.sleep(1)
                try:
                    for dtp_file in _glob.glob(f"{dolphin_profiles_dir}/**/DevToolsActivePort", recursive=True):
                        try:
                            lines = open(dtp_file).read().strip().split("\n")
                            port = lines[0].strip()
                            ws_path = lines[1].strip() if len(lines) > 1 else ""
                            cdp_endpoint = f"ws://127.0.0.1:{port}{ws_path}"
                            logger.info(f"[FACTORY] Browser detectado: port={port} via {dtp_file}")
                            break
                        except Exception:
                            pass
                    if cdp_endpoint:
                        break
                except Exception:
                    pass

            if not cdp_endpoint:
                logger.warning("[FACTORY] Timeout ou browser sem debug port. Captura usará SQLite diretamente.")
                return

            # Chrome just opened — maximize immediately, before navigation starts
            await asyncio.sleep(2)
            _xdotool_maximize_chrome()

            # Connect via CDP and navigate to TikTok
            try:
                from playwright.async_api import async_playwright
                pw = await async_playwright().start()
                browser = await pw.chromium.connect_over_cdp(cdp_endpoint)
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
                page = context.pages[0] if context.pages else await context.new_page()

                _active_session["_pw"] = pw
                _active_session["_browser"] = browser
                _active_session["_context"] = context

                await page.goto("https://www.tiktok.com", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)
                await page.goto("https://www.tiktok.com/login/", wait_until="domcontentloaded", timeout=45000)
                logger.info("[FACTORY] ✅ TikTok carregado via CDP!")
                await asyncio.sleep(2)
                _xdotool_maximize_chrome()
            except Exception as nav_err:
                logger.error(f"[FACTORY] CDP não disponível ({nav_err}). Captura usará SQLite.")

        nav_task = asyncio.create_task(_dolphin_ready_and_navigate())
        _active_session["_nav_task"] = nav_task

        return {
            "active": True,
            "session_type": "factory",
            "novnc_url": novnc_url,
            "proxy": proxy_display,
            "message": (
                f"VNC iniciado com proxy '{proxy_display}'. "
                "1) Se ainda não fez login no Dolphin{anty}: faça login com e-mail/senha. "
                "2) Configure o proxy no perfil (⋮ → Edit → Proxy). "
                "3) Clique START no perfil → navegue para tiktok.com → faça login. "
                "4) Clique 'Capturar Perfil' quando estiver logado."
            ),
        }

    except Exception as e:
        logger.error(f"[FACTORY] Failed to start factory session: {e}")
        _active_session = None  # ensure no stale session lock
        # Only kill freshly-started processes, not persistent Xvfb/Dolphin
        for key in ["vnc_pid", "novnc_pid"]:
            pid = pids.get(key)
            if pid and isinstance(pid, int):
                _kill_pid(pid)
        subprocess.run(["pkill", "-9", "x11vnc"], capture_output=True)
        subprocess.run(["pkill", "-9", "websockify"], capture_output=True)
        return {"error": f"Falha ao iniciar sessão fábrica: {str(e)}"}


async def _dolphin_click_start(dolphin_profile_name: str):
    """Connect to Dolphin Electron UI and click START on the matching profile.

    Uses Playwright CDP connection to Dolphin's built-in DevTools port.
    NOTE: Selectors are confirmed against the Dolphin React UI DOM.
    """
    from playwright.async_api import async_playwright

    # Wait for Dolphin Electron DevTools port to respond (up to 30s)
    for _ in range(30):
        if _dolphin_port_responding():
            break
        await asyncio.sleep(1)
    else:
        raise RuntimeError(
            f"Dolphin Electron port {DOLPHIN_ELECTRON_PORT} não respondeu após 30s — "
            "Dolphin pode não ter iniciado corretamente."
        )

    # Extra wait for UI to fully render
    await asyncio.sleep(3)

    pw = await async_playwright().start()
    try:
        dolphin_browser = await pw.chromium.connect_over_cdp(
            f"http://localhost:{DOLPHIN_ELECTRON_PORT}"
        )

        # Find the main Dolphin UI page (not devtools, not chrome-extension, not empty)
        ui_page = None
        for ctx in dolphin_browser.contexts:
            for page in ctx.pages:
                url = page.url or ""
                if (
                    "devtools" not in url
                    and "chrome-extension" not in url
                    and url not in ("", "about:blank")
                ):
                    ui_page = page
                    break
            if ui_page:
                break

        # Fallback: take any non-blank page
        if not ui_page:
            for ctx in dolphin_browser.contexts:
                for page in ctx.pages:
                    if page.url not in ("", "about:blank"):
                        ui_page = page
                        break
                if ui_page:
                    break

        if not ui_page:
            raise RuntimeError(
                "Nenhuma página UI do Dolphin encontrada. "
                "Execute o script de inspeção para verificar a estrutura DOM."
            )

        logger.info(f"[DOLPHIN] Conectado à UI Electron: url={ui_page.url!r}")

        # Wait for profile list to render
        await ui_page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Strategy: find text matching profile name, then click nearest START button.
        # Dolphin uses a card/row layout — the START button is a sibling of the name text.
        try:
            await ui_page.get_by_text(dolphin_profile_name, exact=False).first.wait_for(
                state="visible", timeout=15000
            )
        except Exception:
            raise RuntimeError(
                f"Perfil '{dolphin_profile_name}' não encontrado na UI do Dolphin. "
                "Verifique se dolphin_profile_name no DB corresponde ao nome exibido no Dolphin."
            )

        profile_locator = ui_page.get_by_text(dolphin_profile_name, exact=False).first

        # Try multiple selector strategies in order of specificity
        start_btn = None
        for selector in [
            # Strategy 1: button with text START in parent container
            profile_locator.locator("xpath=ancestor::*[contains(@class,'profile') or contains(@class,'row') or contains(@class,'card')][1]//button[contains(translate(text(),'start','START'),'START') or contains(@title,'Start') or contains(@aria-label,'Start')]"),
            # Strategy 2: any button near the profile name row
            profile_locator.locator("xpath=following::button[1]"),
            # Strategy 3: generic — parent element's first button
            profile_locator.locator("..").get_by_role("button").first,
        ]:
            try:
                if await selector.is_visible(timeout=2000):
                    start_btn = selector
                    break
            except Exception:
                continue

        if start_btn is None:
            raise RuntimeError(
                f"Botão START não encontrado para o perfil '{dolphin_profile_name}'. "
                "Inspecione o DOM com o script de inspeção e ajuste os seletores."
            )

        await start_btn.click()
        logger.info(f"[DOLPHIN] ✅ Clicou START no perfil '{dolphin_profile_name}'")

    finally:
        await pw.stop()


async def launch_browser_via_dolphin(profile_slug: str) -> tuple:
    """Launch Chrome via Dolphin{anty} for automated upload.

    Does NOT use _active_session — fully independent from VNC sessions.
    Returns (pw, browser, context, page) — same signature as launch_browser().

    Requirements:
    - Profile must have dolphin_profile_name set in DB (set during factory capture).
    - Xvfb + Dolphin will be auto-started if not running.
    """
    import glob as _glob
    import socket as _socket
    import json as _json
    from core.session_manager import get_session_path

    # 1. Resolve dolphin_profile_name from DB
    from core.database import SessionLocal
    from core.models import Profile as ProfileModel
    db = SessionLocal()
    try:
        profile_obj = db.query(ProfileModel).filter(ProfileModel.slug == profile_slug).first()
        if not profile_obj:
            raise RuntimeError(f"Perfil '{profile_slug}' não encontrado no DB")
        dolphin_name = getattr(profile_obj, "dolphin_profile_name", None)
        if not dolphin_name:
            raise RuntimeError(
                f"Perfil '{profile_slug}' não tem dolphin_profile_name configurado. "
                "Abra uma sessão VNC do perfil, depois use POST /api/v1/profiles/{profile_slug}/dolphin-name "
                "para definir o nome do perfil no Dolphin."
            )
    finally:
        db.close()

    # 2. Load TikTok session cookies
    session_path = get_session_path(profile_slug)
    cookies = []
    if session_path and os.path.exists(session_path):
        try:
            with open(session_path, "r") as f:
                state = _json.load(f)
            cookies = state.get("cookies", [])
            logger.info(f"[DOLPHIN-UPLOAD] {len(cookies)} cookies carregados para '{profile_slug}'")
        except Exception as e:
            logger.warning(f"[DOLPHIN-UPLOAD] Erro ao carregar cookies: {e}")

    # 3. Ensure Xvfb + Dolphin are running
    await _ensure_xvfb()
    _ensure_dolphin()
    _patch_dolphin_chrome()

    dolphin_profiles_dir = "/root/.config/dolphin_anty/browser_profiles"

    # 4. Remove stale DevToolsActivePort files from previous sessions
    for stale_dtp in _glob.glob(f"{dolphin_profiles_dir}/**/DevToolsActivePort", recursive=True):
        try:
            port_str = open(stale_dtp).readline().strip()
            if port_str.isdigit():
                s = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
                s.settimeout(0.3)
                alive = s.connect_ex(("127.0.0.1", int(port_str)))
                s.close()
                if alive != 0:
                    os.remove(stale_dtp)
                    logger.info(f"[DOLPHIN-UPLOAD] Removido stale DevToolsActivePort: {stale_dtp}")
        except Exception:
            pass

    # 5. Click START in Dolphin UI via Electron CDP
    await _dolphin_click_start(dolphin_name)

    # 6. Maximize window immediately
    await asyncio.sleep(2)
    _xdotool_maximize_chrome()

    # 7. Poll for DevToolsActivePort — PROVEN pattern from factory/profile_dolphin
    cdp_endpoint = None
    for _ in range(120):  # 2 min max
        await asyncio.sleep(1)
        for dtp_file in _glob.glob(f"{dolphin_profiles_dir}/**/DevToolsActivePort", recursive=True):
            try:
                lines = open(dtp_file).read().strip().split("\n")
                port = lines[0].strip()
                ws_path = lines[1].strip() if len(lines) > 1 else ""
                if port.isdigit():
                    cdp_endpoint = f"ws://127.0.0.1:{port}{ws_path}"
                    logger.info(f"[DOLPHIN-UPLOAD] Chrome detectado: port={port} via {dtp_file}")
                    break
            except Exception:
                pass
        if cdp_endpoint:
            break

    if not cdp_endpoint:
        raise RuntimeError(
            "[DOLPHIN-UPLOAD] Chrome não iniciou em 2 minutos. "
            "Verifique se o botão START foi clicado corretamente e se o perfil existe no Dolphin."
        )

    # 8. Maximize after Chrome opens
    await asyncio.sleep(2)
    _xdotool_maximize_chrome()

    # 9. Connect via CDP
    from playwright.async_api import async_playwright
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp(cdp_endpoint)
    context = browser.contexts[0] if browser.contexts else await browser.new_context()
    page = context.pages[0] if context.pages else await context.new_page()

    # 9.5. Force download directory via CDP (runtime override — Preferences patch only works on next Chrome start)
    _downloads_dir = "/app/downloads"
    os.makedirs(_downloads_dir, exist_ok=True)
    try:
        _cdp_dl = await context.new_cdp_session(page)
        await _cdp_dl.send("Browser.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": _downloads_dir,
            "eventsEnabled": True,
        })
        await _cdp_dl.detach()
        logger.info(f"[DOLPHIN-UPLOAD] ✅ Download path forçado via CDP: {_downloads_dir}")
    except Exception as _e:
        logger.warning(f"[DOLPHIN-UPLOAD] Não foi possível forçar download path via CDP: {_e}")

    # 10. Inject TikTok session cookies
    if cookies:
        try:
            await context.add_cookies(cookies)
            logger.info(f"[DOLPHIN-UPLOAD] ✅ {len(cookies)} cookies injetados para '{profile_slug}'")
        except Exception as e:
            logger.warning(f"[DOLPHIN-UPLOAD] Falha ao injetar cookies: {e}")

    return pw, browser, context, page


async def _wait_dolphin_api_ready(timeout_s: int = 60) -> bool:
    """Poll Dolphin local API until it responds (API starts a few seconds after the Electron app)."""
    for _ in range(timeout_s):
        try:
            async with httpx.AsyncClient(timeout=2) as c:
                r = await c.get(f"{DOLPHIN_API_URL}/browser_profiles")
                if r.status_code in (200, 401, 403):
                    return True
        except Exception:
            pass
        await asyncio.sleep(1)
    return False


async def start_dolphin_session(profile_slug: str, host_url: str = "") -> Dict[str, Any]:
    """
    Opens an existing TikTok profile in Dolphin{anty} via VNC.

    Reuses the persistent Xvfb + Dolphin infrastructure from the factory flow,
    creates an ephemeral Dolphin browser profile (with saved proxy), starts it,
    then injects the saved TikTok cookies via CDP and navigates to TikTok Studio.

    This gives full Dolphin anti-detection (canvas, WebGL, font spoofing, etc.)
    instead of raw Playwright Chromium.
    """
    global _active_session, _persistent_xvfb_pid, _persistent_dolphin_pid

    if _active_session:
        return {
            "error": "Já existe uma sessão ativa. Encerre-a primeiro.",
            "novnc_url": _active_session.get("novnc_url"),
        }

    logger.info(f"[DOLPHIN-SESSION] Starting Dolphin profile session for: {profile_slug}")

    # Load profile + proxy from DB
    from core.database import SessionLocal
    from core.models import Profile as ProfileModel
    from core.session_manager import get_session_path
    import json as _json

    db = SessionLocal()
    try:
        profile_obj = db.query(ProfileModel).filter(ProfileModel.slug == profile_slug).first()
        if not profile_obj:
            return {"error": f"Perfil '{profile_slug}' não encontrado."}
        profile_label = profile_obj.label or profile_slug
    finally:
        db.close()

    # Load saved cookies
    session_path = get_session_path(profile_slug)
    cookies = []
    if session_path and os.path.exists(session_path):
        try:
            with open(session_path, "r") as f:
                state = _json.load(f)
            cookies = state.get("cookies", [])
            logger.info(f"[DOLPHIN-SESSION] Loaded {len(cookies)} cookies from session file")
        except Exception as e:
            logger.warning(f"[DOLPHIN-SESSION] Could not load cookies: {e}")

    # Kill stale VNC processes but keep Xvfb + Dolphin alive
    for proc_name in ["x11vnc", "websockify", "chrome"]:
        subprocess.run(["pkill", "-9", proc_name], capture_output=True)
    await asyncio.sleep(0.5)

    pids = {}

    try:
        # 1. Ensure Xvfb running
        await _ensure_xvfb()
        pids["xvfb_pid"] = _persistent_xvfb_pid

        # 2. Ensure Dolphin running (with --remote-debugging-port)
        _ensure_dolphin()
        pids["dolphin_pid"] = _persistent_dolphin_pid

        # 3. Start x11vnc
        vnc_password = secrets.token_urlsafe(8)
        vnc = subprocess.Popen(
            [
                "x11vnc",
                "-display", f":{DISPLAY_NUM}",
                "-passwd", vnc_password,
                "-forever", "-shared",
                "-rfbport", str(VNC_PORT),
                "-xkb", "-noxrecord", "-noxfixes", "-noxdamage",
                "-localhost",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        pids["vnc_pid"] = vnc.pid
        pids["_vnc_password"] = vnc_password
        await asyncio.sleep(1)
        logger.info(f"[DOLPHIN-SESSION] x11vnc started on port {VNC_PORT} (PID {vnc.pid})")

        # 4. Start noVNC
        novnc = subprocess.Popen(
            ["websockify", "--web", "/usr/share/novnc", str(NOVNC_PORT), f"localhost:{VNC_PORT}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        pids["novnc_pid"] = novnc.pid
        await asyncio.sleep(1)
        logger.info(f"[DOLPHIN-SESSION] noVNC started on port {NOVNC_PORT} (PID {novnc.pid})")

        novnc_url = f"http://{host_url}:{NOVNC_PORT}/vnc.html?autoconnect=true&resize=scale&password={vnc_password}"

        import datetime
        _active_session = {
            "session_type": "profile_dolphin",
            "profile_slug": profile_slug,
            "novnc_url": novnc_url,
            "started_at": datetime.datetime.now().isoformat(),
            **pids,
        }

        logger.info(f"[DOLPHIN-SESSION] ✅ VNC pronto para '{profile_label}'. Injetando cookies em background...")

        # 5. Background task: wait for user to click START in Dolphin → inject cookies → navigate
        #    Same polling approach as factory — no Dolphin API auth required.
        async def _dolphin_inject_and_navigate():
            import glob as _glob
            import socket as _socket
            dolphin_profiles_dir = "/root/.config/dolphin_anty/browser_profiles"

            # Wait for Dolphin to fully start (profiles dir appears)
            logger.info("[DOLPHIN-SESSION] Aguardando Dolphin iniciar...")
            for _ in range(60):
                await asyncio.sleep(1)
                if os.path.isdir(dolphin_profiles_dir):
                    break

            _patch_dolphin_chrome()

            # Dolphin window visible — maximize to 1920×1080 immediately
            await asyncio.sleep(2)
            _xdotool_maximize_chrome()

            # Remove stale DevToolsActivePort files (Chrome leaves these on SIGKILL)
            for stale_dtp in _glob.glob(f"{dolphin_profiles_dir}/**/DevToolsActivePort", recursive=True):
                try:
                    port_str = open(stale_dtp).readline().strip()
                    if port_str.isdigit():
                        sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
                        sock.settimeout(0.3)
                        alive = sock.connect_ex(("127.0.0.1", int(port_str)))
                        sock.close()
                        if alive != 0:
                            os.remove(stale_dtp)
                            logger.info(f"[DOLPHIN-SESSION] Removed stale DevToolsActivePort: {stale_dtp}")
                except Exception:
                    pass

            logger.info(f"[DOLPHIN-SESSION] Pronto! Clique START em qualquer perfil no Dolphin — cookies de '{profile_label}' serão injetados automaticamente.")

            # Poll for DevToolsActivePort — created by Chrome when started with --remote-debugging-port=0
            cdp_endpoint = None
            for _ in range(600):  # up to 10 minutes
                await asyncio.sleep(1)
                try:
                    for dtp_file in _glob.glob(f"{dolphin_profiles_dir}/**/DevToolsActivePort", recursive=True):
                        try:
                            lines = open(dtp_file).read().strip().split("\n")
                            port = lines[0].strip()
                            ws_path = lines[1].strip() if len(lines) > 1 else ""
                            cdp_endpoint = f"ws://127.0.0.1:{port}{ws_path}"
                            logger.info(f"[DOLPHIN-SESSION] Browser detectado: port={port} via {dtp_file}")
                            break
                        except Exception:
                            pass
                    if cdp_endpoint:
                        break
                except Exception:
                    pass

            if not cdp_endpoint:
                logger.warning("[DOLPHIN-SESSION] Timeout (10 min). Nenhum browser detectado.")
                return

            # Chrome just opened — maximize immediately (2s for window to render)
            await asyncio.sleep(2)
            _xdotool_maximize_chrome()

            # Connect via CDP, inject cookies, navigate to TikTok Studio
            try:
                from playwright.async_api import async_playwright
                pw = await async_playwright().start()
                browser = await pw.chromium.connect_over_cdp(cdp_endpoint)
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
                page = context.pages[0] if context.pages else await context.new_page()

                if _active_session:
                    _active_session["_pw"] = pw
                    _active_session["_browser"] = browser
                    _active_session["_context"] = context

                # Inject saved TikTok cookies so the session opens authenticated
                if cookies:
                    try:
                        await context.add_cookies(cookies)
                        logger.info(f"[DOLPHIN-SESSION] ✅ {len(cookies)} cookies de '{profile_label}' injetados via CDP")
                    except Exception as e:
                        logger.warning(f"[DOLPHIN-SESSION] Falha ao injetar cookies: {e}")

                # Navigate to TikTok Studio
                await page.goto("https://www.tiktok.com/tiktokstudio/upload",
                                wait_until="domcontentloaded", timeout=45000)
                logger.info("[DOLPHIN-SESSION] ✅ TikTok Studio carregado!")

                # Final maximize after page load
                await asyncio.sleep(2)
                _xdotool_maximize_chrome()

            except Exception as e:
                logger.error(f"[DOLPHIN-SESSION] CDP/navegação falhou: {e}")

        nav_task = asyncio.create_task(_dolphin_inject_and_navigate())
        _active_session["_nav_task"] = nav_task

        return {
            "active": True,
            "novnc_url": novnc_url,
            "profile_slug": profile_slug,
            "message": f"Sessão Dolphin iniciada para '{profile_label}'. Aguarde — injetando cookies e abrindo TikTok Studio...",
        }

    except Exception as e:
        logger.error(f"[DOLPHIN-SESSION] Falha ao iniciar: {e}")
        _active_session = None
        for key in ["vnc_pid", "novnc_pid"]:
            pid = pids.get(key)
            if pid and isinstance(pid, int):
                _kill_pid(pid)
        subprocess.run(["pkill", "-9", "x11vnc"], capture_output=True)
        subprocess.run(["pkill", "-9", "websockify"], capture_output=True)
        return {"error": f"Falha ao iniciar sessão Dolphin: {str(e)}"}


def _read_dolphin_cookies() -> list:
    """Read TikTok cookies directly from Dolphin browser profile SQLite databases.
    Fallback when CDP is not available. Uses Chrome's OSCrypt Linux decryption
    (PBKDF2 with 'peanuts' password — standard Chromium behavior without a keyring).
    """
    import glob as _glob
    import sqlite3
    import shutil
    import tempfile

    dolphin_profiles_dir = "/root/.config/dolphin_anty/browser_profiles"
    all_cookies: list = []

    for cookie_db in _glob.glob(f"{dolphin_profiles_dir}/**/Default/Cookies", recursive=True):
        try:
            tmp = tempfile.mktemp(suffix=".db")
            shutil.copy2(cookie_db, tmp)
            try:
                conn = sqlite3.connect(f"file:{tmp}?mode=ro&immutable=1", uri=True)
                cur = conn.cursor()
                cur.execute("""
                    SELECT name, CAST(value AS TEXT), encrypted_value, host_key, path,
                           expires_utc, is_secure, is_httponly, samesite
                    FROM cookies WHERE host_key LIKE '%tiktok.com%'
                """)
                rows = cur.fetchall()
                conn.close()
            finally:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

            profile_cookies = []
            for name, value, enc_value, host, path, exp_utc, secure, httponly, samesite in rows:
                if not value and enc_value:
                    value = _decrypt_chrome_cookie(enc_value)
                if not value:
                    continue
                # Chrome stores expiry as microseconds since 1601-01-01; convert to Unix seconds
                expire_unix = None
                if exp_utc and exp_utc > 0:
                    expire_unix = (exp_utc - 11644473600000000) / 1_000_000
                profile_cookies.append({
                    "name": name,
                    "value": value,
                    "domain": host,
                    "path": path,
                    "secure": bool(secure),
                    "httpOnly": bool(httponly),
                    "sameSite": "Lax" if samesite == 1 else "Strict" if samesite == 2 else "None",
                    **({"expires": expire_unix} if expire_unix else {}),
                })

            if any(c["name"] == "sessionid" for c in profile_cookies):
                logger.info(f"[FACTORY] Cookie TikTok encontrado em {cookie_db} ({len(profile_cookies)} cookies)")
                all_cookies = profile_cookies
                break
        except Exception as e:
            logger.warning(f"[FACTORY] Erro ao ler cookies de {cookie_db}: {e}")

    return all_cookies


def _decrypt_chrome_cookie(enc: bytes) -> str:
    """Decrypt a Chrome v10 cookie (Linux OSCrypt, no system keyring)."""
    try:
        if enc[:3] != b"v10":
            return enc.decode("utf-8", errors="replace") if isinstance(enc, bytes) else str(enc)
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA1(), length=16,
            salt=b"saltysalt", iterations=1, backend=default_backend(),
        )
        key = kdf.derive(b"peanuts")
        iv = b" " * 16
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        dec = cipher.decryptor()
        raw = dec.update(enc[3:]) + dec.finalize()
        pad = raw[-1]
        return raw[:-pad].decode("utf-8", errors="replace")
    except Exception:
        return ""


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
    resolved_proxy_id = proxy_id or _active_session.get("proxy_id")
    ua = _active_session.get("factory_ua")

    logger.info(f"[FACTORY] Capturing profile (proxy_id={resolved_proxy_id}, cdp={'yes' if pw_context else 'no — using SQLite'})")

    import json as _json
    import time

    # 1. Extract cookies — from live CDP context OR directly from Dolphin SQLite
    if pw_context:
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
    else:
        # CDP not connected — read cookies directly from Dolphin profile SQLite
        cookies = _read_dolphin_cookies()
        if not cookies:
            raise RuntimeError(
                "Nenhum cookie TikTok encontrado. Certifique-se de ter feito login no TikTok "
                "dentro do browser do Dolphin antes de capturar."
            )

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
