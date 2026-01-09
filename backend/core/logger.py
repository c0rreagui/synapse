
import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOGS_DIR, "app.jsonl")

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

class JsonLogger:
    def __init__(self, file_path: str = LOG_FILE):
        self.file_path = file_path
        # Mem cache for read performance (last 200 logs)
        self._mem_buffer: List[Dict] = []
        self._load_from_file()

    def _load_from_file(self):
        """Loads last N logs from file into memory."""
        if not os.path.exists(self.file_path):
            self._mem_buffer = []
            return

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Tail 200
                last_lines = lines[-200:]
                self._mem_buffer = [json.loads(line) for line in last_lines if line.strip()]
                # Reverse to show newest first? Logic usually expects newest first.
                # If file is appended, newest is at bottom.
                # So we reverse buffer for frontend display (descending)
                self._mem_buffer.reverse() 
        except Exception as e:
            print(f"Error loading logs: {e}")
            self._mem_buffer = []

    def log(self, level: str, message: str, source: str = "system") -> Dict:
        """Adds a log entry."""
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "full_timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message.strip(),
            "source": source
        }
        
        # Write to file (Append)
        try:
            with open(self.file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"Failed to write log: {e}")

        # Update Buffer
        self._mem_buffer.insert(0, entry) # Newest first
        if len(self._mem_buffer) > 200:
            self._mem_buffer.pop()
            
        return entry

    def get_logs(self, limit: int = 50, level: Optional[str] = None, source: Optional[str] = None) -> List[Dict]:
        """Get logs from buffer."""
        filtered = self._mem_buffer
        
        if level and level != "all":
            filtered = [l for l in filtered if l['level'] == level]
        
        if source:
            filtered = [l for l in filtered if l['source'] == source]
            
        return filtered[:limit]

    def clear(self):
        """Clears the log file and buffer."""
        self._mem_buffer = []
        try:
            open(self.file_path, 'w').close()
            self.log("info", "Logs limpos pelo administrador", "system")
        except:
            pass

    def get_stats(self) -> Dict:
        return {
            "info": len([l for l in self._mem_buffer if l['level'] == "info"]),
            "success": len([l for l in self._mem_buffer if l['level'] == "success"]),
            "warning": len([l for l in self._mem_buffer if l['level'] == "warning"]),
            "error": len([l for l in self._mem_buffer if l['level'] == "error"]),
            "total": len(self._mem_buffer)
        }

# Singleton instance
logger = JsonLogger()
