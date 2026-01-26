import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import psutil
import asyncio

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATUS_FILE = os.path.join(DATA_DIR, "status.json")

class StatusManager:
    def __init__(self):
        self.file_path = STATUS_FILE
        self._ensure_dir()
        self.async_callback = None
        # In-memory storage for bots status (to avoid full file dependency for high freq updates)
        self.bots_status = {
            "uploader": {"id": "1", "name": "ATLAS-01", "role": "UPLOADER", "status": "online", "current_task": "Idle", "uptime": "0s"},
            "factory": {"id": "2", "name": "FORGE-X", "role": "FACTORY", "status": "online", "current_task": "Watching inputs...", "uptime": "0s"},
            "monitor": {"id": "3", "name": "WATCHER-V2", "role": "MONITOR", "status": "online", "current_task": "System Check", "uptime": "0s"}
        }
        self.start_times = {
            "uploader": time.time(),
            "factory": time.time(),
            "monitor": time.time()
        }
        from threading import Lock
        self._lock = Lock()

    def set_async_callback(self, callback):
        self.async_callback = callback

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def _get_system_stats(self):
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "ram_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage(BASE_DIR).percent
            }
        except:
            return {}

    def _update_uptimes(self):
        now = time.time()
        for key in self.bots_status:
            diff = int(now - self.start_times.get(key, now))
            # Format timedelta
            hours, remainder = divmod(diff, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.bots_status[key]["uptime"] = f"{hours}h {minutes}m"

    def update_bot_status(self, bot_key: str, status: str, task: str):
        if bot_key in self.bots_status:
            self.bots_status[bot_key]["status"] = status
            self.bots_status[bot_key]["current_task"] = task
            # Trigger full update broadcast logic if needed, or just persist
            # For now, we will piggyback on the main update or next polling/broadcast

    def update_status(self, 
                      state: str, # 'idle', 'busy', 'error', 'paused'
                      current_task: Optional[str] = None, 
                      progress: int = 0, 
                      step: Optional[str] = None,
                      logs: Optional[List[str]] = None):
        """
        Updates the global system status.
        """
        self._update_uptimes()

        data = {
            "state": state,
            "last_updated": datetime.now().isoformat(),
            "timestamp": time.time(),
            "job": {
                "name": current_task or "None",
                "progress": progress,
                "step": step or "Waiting...",
                "logs": logs or []
            },
            "bots": list(self.bots_status.values())
        }
        
        try:
            with self._lock:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to write status: {e}")

        if self.async_callback:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    data_to_send = {
                        "state": state,
                        "job": data["job"],
                        "system": self._get_system_stats(),
                        "bots": data["bots"]
                    }
                    asyncio.run_coroutine_threadsafe(self.async_callback(data_to_send), loop)
            except Exception as e:
                print(f"WS Broadcast Error: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Reads the current status and appends REAL system stats."""
        # Base status from file
        status = {}
        if not os.path.exists(self.file_path):
            self._update_uptimes()
            status = {
                "state": "idle",
                "last_updated": datetime.now().isoformat(),
                "job": {"name": None, "progress": 0, "step": "Ready", "logs": []},
                "bots": list(self.bots_status.values())
            }
        else:
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    status = json.load(f)
            except:
                status = {"state": "unknown", "job": {}, "bots": []}

        # Append Real Hardware Stats (On-the-fly)
        status["system"] = self._get_system_stats()
        # Merge latest memory bot stats if file is stale
        self._update_uptimes()
        status["bots"] = list(self.bots_status.values())
            
        return status

    def set_idle(self):
        self.update_status("idle", progress=0, step="Aguardando tarefas...")

# Singleton
status_manager = StatusManager()
