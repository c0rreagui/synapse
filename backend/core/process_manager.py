import subprocess
import threading
import time
import logging
import psutil
import atexit
import signal
import os
import sys
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)

class ProcessManager:
    """
    Centralized process manager to spawn, track, and kill child processes.
    Ensures that no zombie processes are left behind on shutdown.
    """
    _instance = None
    _lock = threading.Lock()
    _instance = None
    _lock = threading.Lock()
    _processes: Dict[int, psutil.Process] = {}
    _resources: set = set()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ProcessManager, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance
    
    def _initialize(self):
        """Register cleanup handlers"""
        logger.info("🛡️ ProcessManager Initialized")
        atexit.register(self.kill_all)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        logger.warning(f"🛑 Received signal {signum}. Terminating all processes...")
        self.kill_all()
        sys.exit(0)

    def start_process(self, command: List[str], cwd: str = None, env: Dict = None) -> subprocess.Popen:
        """
        Starts a new process and tracks it.
        params:
            command: List of arguments (e.g. ["python", "script.py"])
            cwd: Working directory
            env: Environment variables
        """
        try:
            # Force unbuffered output for Python scripts
            if command[0].endswith("python") or command[0].endswith("python3"):
                 if "-u" not in command:
                     command.insert(1, "-u")
            
            # Configure startup info to hide window on Windows (optional)
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, # Py3.7+
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo
            )
            
            if process.pid:
                try:
                    p = psutil.Process(process.pid)
                    with self._lock:
                        self._processes[process.pid] = p
                    logger.info(f"🚀 Started subprocess {process.pid}: {' '.join(command)}")
                except psutil.NoSuchProcess:
                    logger.warning(f"⚠️ Process {process.pid} died immediately after spawn.")
            
            return process
            
        except Exception as e:
            logger.error(f"❌ Failed to start process {' '.join(command)}: {e}")
            raise e

    def stop_process(self, pid: int):
        """Stop a specific process by PID"""
        with self._lock:
            proc = self._processes.get(pid)
            if proc:
                try:
                    logger.info(f"🛑 Stopping process {pid}...")
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except psutil.TimeoutExpired:
                         logger.warning(f"⚠️ Process {pid} did not terminate gracefully. Killing force...")
                         proc.kill()
                    
                    if pid in self._processes:
                        del self._processes[pid]
                        
                except psutil.NoSuchProcess:
                    # Already dead
                    if pid in self._processes:
                        del self._processes[pid]
                except Exception as e:
                    logger.error(f"❌ Error stopping process {pid}: {e}")

    def kill_all(self):
        """Kill all tracked processes. Safe to call multiple times."""
        with self._lock:
            if not self._processes:
                return
                
            logger.warning(f"🧹 Cleaning up {len(self._processes)} child processes...")
            
            for pid, proc in list(self._processes.items()):
                try:
                    if proc.is_running():
                        proc.terminate()
                except psutil.NoSuchProcess:
                    pass
                except Exception as e:
                    logger.error(f"Error terminating {pid}: {e}")
            
            # Wait for termination
            gone, alive = psutil.wait_procs(self._processes.values(), timeout=3)
            
            # Force kill alive
            for p in alive:
                try:
                    logger.warning(f"💀 Force killing zombie {p.pid}")
                    p.kill()
                except: pass
            
            self._processes.clear()
            
            # Cleanup registered resources (Best Effort)
            if self._resources:
                logger.info(f"🧹 Use Best-Effort cleanup for {len(self._resources)} resources...")
                for res in list(self._resources):
                    try:
                        if hasattr(res, "close"):
                             # If async, this might warn/fail in atexit, but we allow it for now
                             # For sync resources it works.
                            res.close()
                        elif hasattr(res, "stop"):
                            res.stop()
                    except Exception as e:
                        logger.warning(f"Error closing resource {res}: {e}")
                self._resources.clear()

            logger.info("✨ Process cleanup complete.")

    def register(self, resource):
        """Register a non-process resource for cleanup (e.g. Playwright)"""
        with self._lock:
            self._resources.add(resource)

    def unregister(self, resource):
        """Unregister a resource"""
        with self._lock:
            if resource in self._resources:
                self._resources.remove(resource)

# Singleton export
process_manager = ProcessManager()
