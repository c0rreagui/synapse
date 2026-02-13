import asyncio
import logging
import signal
import sys
import psutil
from typing import List, Any, Optional

logger = logging.getLogger(__name__)

class ProcessManager:
    """
    Singleton Process Manager to track resources (processes, browsers, etc.)
    and ensure graceful cleanup on shutdown (SIGINT, SIGTERM).
    """
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(ProcessManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.resources: List[Any] = []
        self._shutting_down = False
        self._initialized = True
        
        # Register Signal Handlers
        try:
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)
            if sys.platform == "win32":
                signal.signal(signal.SIGBREAK, self._handle_signal)
        except ValueError:
            # Signal handling might fail if not main thread, usually fine
            logger.warning("[ProcessManager] Could not register signal handlers (not main thread?)")
            
    def register(self, resource: Any):
        """Registers a resource (browser, subprocess, etc.) for cleanup."""
        if resource not in self.resources:
            self.resources.append(resource)
            
    def unregister(self, resource: Any):
        """Unregisters a resource."""
        if resource in self.resources:
            self.resources.remove(resource)
            
    def _handle_signal(self, signum, frame):
        """Handles shutdown signals."""
        if self._shutting_down: return
        self._shutting_down = True
        
        sig_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        logger.info(f"[ProcessManager] Received {sig_name}. cleaning up {len(self.resources)} resources...")
        
        # We need to schedule cleanup on the running loop
        # But we modify the exit flow.
        # Ideally, we create a task.
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self.cleanup())
            # We don't exit immediately, we let cleanup finish?
            # Signal handlers interrupt.
            # We can raise SystemExit after cleanup?
        else:
            # Sync cleanup
            asyncio.run(self.cleanup())
            sys.exit(0)

    async def cleanup(self):
        """Iterates through resources and calls close()/stop()/kill()."""
        logger.info("[ProcessManager] executing cleanup...")
        for res in reversed(self.resources): # LIFO order
            try:
                # 1. Playwright / Browser objects
                if hasattr(res, 'close'):
                    if asyncio.iscoroutinefunction(res.close):
                        await res.close()
                    else:
                        res.close()
                elif hasattr(res, 'stop'):
                    if asyncio.iscoroutinefunction(res.stop):
                        await res.stop()
                    else:
                        res.stop()
                
                # 2. Subprocesses (Popen)
                elif hasattr(res, 'terminate') and hasattr(res, 'kill'):
                    res.terminate()
                    try:
                        res.wait(timeout=2)
                    except:
                        res.kill()
                        
            except Exception as e:
                logger.error(f"[ProcessManager] Error cleaning up resource {res}: {e}")
        
        self.resources.clear()
        logger.info("[ProcessManager] Cleanup complete. Exiting.")
        sys.exit(0)

# Global Instance
process_manager = ProcessManager()
