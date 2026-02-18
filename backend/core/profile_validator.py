import asyncio
import logging
import os # Added import
from typing import Dict, Optional
from core.session_manager import get_session_path, update_profile_info, update_profile_metadata, update_profile_status, get_profile_metadata, get_profile_user_agent

logger = logging.getLogger(__name__)


import asyncio
import logging
import json
import os
import sys

# Use absolute imports or ensure path is set
from core.process_manager import process_manager

logger = logging.getLogger(__name__)

async def validate_profile(profile_id: str, headless: bool = True) -> dict:
    """
    Validates profile status by spawning an isolated subprocess.
    This prevents browser memory leaks or crashes from affecting the main process.
    """
    logger.info(f"🕵️ Validating profile (Isolated): {profile_id}")
    
    script_path = os.path.join(os.path.dirname(__file__), "validator_cli.py")
    if not os.path.exists(script_path):
        logger.error(f"validator_cli.py not found at {script_path}")
        return {"status": "error", "message": "Validator CLI script missing"}

    cmd = [sys.executable, script_path, profile_id]
    if not headless:
        # Note: validator_cli needs to support this flag if we pass it
        cmd.append("--headful")
        
    try:
        # Spawn process using ProcessManager
        # We process asynchronously (non-blocking IO is tricky with Popen, 
        # but ProcessManager uses Popen. We need to wait for it.)
        
        proc = process_manager.start_process(cmd)
        
        # Check if proc started
        if not proc:
             return {"status": "error", "message": "Failed to spawn validator process"}

        pid = proc.pid
        
        # Wait for completion (Thread-blocking, but wrapped in async typically requires loop.run_in_executor)
        # For simplicity in this async function, we can use asyncio.to_thread 
        # or just wait since this is an async function but Popen.wait is blocking.
        
        # Better: Communicate
        stdout, stderr = await asyncio.get_event_loop().run_in_executor(None, proc.communicate)
        
        # Process Manager cleanup (remove from tracked list)
        process_manager.stop_process(pid) 
        
        if proc.returncode != 0:
            logger.error(f"Validator CLI failed (Exit {proc.returncode}): {stderr}")
            return {"status": "error", "message": f"Process crashed: {stderr}"}
            
        # Parse JSON output
        try:
            # Clean stdout (sometimes has other prints if not silenced correctly)
            # Find the last JSON-like object
            lines = stdout.strip().splitlines()
            last_line = lines[-1] if lines else ""
            result = json.loads(last_line)
            return result
            
        except json.JSONDecodeError as je:
             logger.error(f"Invalid JSON from validator: {stdout} | Error: {je}")
             return {"status": "error", "message": "Invalid response from validator process"}
             
    except Exception as e:
        logger.error(f"Error running validator process: {e}")
        return {"status": "error", "message": str(e)}


