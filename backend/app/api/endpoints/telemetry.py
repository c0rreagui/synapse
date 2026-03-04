import os
import psutil
import time
import json
import asyncio
from typing import Dict, Any, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Time anchor at module load
START_TIME = time.time()

# Path to the JSONL log file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LOG_FILE = os.path.join(BASE_DIR, "logs", "app.jsonl")


def get_uptime_str(seconds: float) -> str:
    """Format seconds into a short string like '1d 2h 3m' ou '4h 15m'"""
    mins, _ = divmod(seconds, 60)
    hour, mins = divmod(mins, 60)
    day, hour = divmod(hour, 24)

    parts = []
    if day > 0:
        parts.append(f"{int(day)}d")
    if hour > 0 or day > 0:
        parts.append(f"{int(hour)}h")
    parts.append(f"{int(mins)}m")

    return " ".join(parts)


@router.get("/vitals")
async def get_vitals() -> Dict[str, Any]:
    """
    Returns system vitals:
    - cpu_percent: Current CPU usage percentage
    - mem_used_gb: RAM used in GB
    - mem_total_gb: Total RAM in GB
    - mem_percent: RAM usage percentage
    - uptime: Formatted string of service uptime
    """
    cpu_percent = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    mem_used_gb = round(mem.used / (1024**3), 1)
    mem_total_gb = round(mem.total / (1024**3), 1)
    uptime_seconds = time.time() - START_TIME
    uptime_str = get_uptime_str(uptime_seconds)

    return {
        "cpu_percent": cpu_percent,
        "mem_used_gb": mem_used_gb,
        "mem_total_gb": mem_total_gb,
        "mem_percent": mem.percent,
        "uptime": uptime_str,
    }


def read_last_lines(filepath: str, n: int = 50) -> List[str]:
    """Read last N lines from a file efficiently."""
    try:
        with open(filepath, "rb") as f:
            f.seek(0, 2)
            end = f.tell()
            lines: List[bytes] = []
            pos = end
            while pos > 0 and len(lines) < n + 1:
                pos = max(pos - 4096, 0)
                f.seek(pos)
                chunk = f.read(min(4096, end - pos))
                chunk_lines = chunk.split(b"\n")
                if lines:
                    chunk_lines[-1] += lines[0]
                    lines = chunk_lines + lines[1:]
                else:
                    lines = chunk_lines
            return [line.decode("utf-8", errors="replace") for line in lines[-n:] if line.strip()]
    except FileNotFoundError:
        return []


@router.websocket("/stream")
async def log_stream(websocket: WebSocket):
    """
    WebSocket endpoint that tails logs/app.jsonl in real-time.
    On connect: sends last 30 log lines as backfill.
    Then polls the file for new lines every 1s and pushes them.
    """
    await websocket.accept()

    # Backfill: send last 30 lines
    initial_lines = read_last_lines(LOG_FILE, 30)
    for line in initial_lines:
        try:
            entry = json.loads(line)
            await websocket.send_json({"type": "log_entry", "data": entry})
        except (json.JSONDecodeError, Exception):
            await websocket.send_json({
                "type": "log_entry",
                "data": {"level": "INFO", "message": line.strip(), "module": "System"}
            })

    # Seek to end of file for tailing
    try:
        f = open(LOG_FILE, "r", encoding="utf-8", errors="replace")
        f.seek(0, 2)  # seek to end
    except FileNotFoundError:
        f = None

    try:
        while True:
            try:
                # Check for client messages (ping/pong keepalive)
                try:
                    msg = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                    if msg == "ping":
                        await websocket.send_json({"type": "pong"})
                except asyncio.TimeoutError:
                    pass

                # Read new lines from file
                if f:
                    new_lines = f.readlines()
                    for line in new_lines:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                            await websocket.send_json({"type": "log_entry", "data": entry})
                        except json.JSONDecodeError:
                            await websocket.send_json({
                                "type": "log_entry",
                                "data": {"level": "INFO", "message": line, "module": "System"}
                            })

            except WebSocketDisconnect:
                break
            except Exception:
                break
    finally:
        if f:
            f.close()
