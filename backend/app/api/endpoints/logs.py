"""
Logs Endpoint - Provides system logs for the frontend
"""
import os
import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

class LogEntry(BaseModel):
    id: str
    timestamp: str
    level: str  # info, success, warning, error
    message: str
    source: str

class LogsResponse(BaseModel):
    logs: List[LogEntry]
    total: int
    
# In-memory log buffer for real-time logs
_log_buffer: List[LogEntry] = []
_log_counter = 0

def add_log(level: str, message: str, source: str = "system"):
    """Add a log entry to the buffer"""
    global _log_counter
    _log_counter += 1
    entry = LogEntry(
        id=f"log-{_log_counter}",
        timestamp=datetime.now().strftime("%H:%M:%S"),
        level=level,
        message=message,
        source=source
    )
    _log_buffer.insert(0, entry)
    # Keep only last 100 logs in memory
    if len(_log_buffer) > 100:
        _log_buffer.pop()
    return entry

# Initialize with some startup logs
add_log("info", "Sistema Synapse inicializado", "system")
add_log("success", "Conexão com banco de dados estabelecida", "database")
add_log("info", "Factory Watcher iniciado", "factory_watcher")

@router.get("/", response_model=LogsResponse)
async def get_logs(
    level: Optional[str] = Query(None, description="Filter by log level"),
    limit: int = Query(50, description="Number of logs to return"),
    source: Optional[str] = Query(None, description="Filter by source")
):
    """
    Get system logs with optional filtering.
    """
    logs = _log_buffer.copy()
    
    if level and level != "all":
        logs = [log for log in logs if log.level == level]
    
    if source:
        logs = [log for log in logs if log.source == source]
    
    return LogsResponse(
        logs=logs[:limit],
        total=len(logs)
    )

@router.post("/add")
async def create_log(level: str, message: str, source: str = "api"):
    """
    Add a new log entry (for testing or external integrations).
    """
    entry = add_log(level, message, source)
    return {"success": True, "log": entry}

@router.get("/stats")
async def get_log_stats():
    """
    Get log statistics by level.
    """
    stats = {
        "info": len([l for l in _log_buffer if l.level == "info"]),
        "success": len([l for l in _log_buffer if l.level == "success"]),
        "warning": len([l for l in _log_buffer if l.level == "warning"]),
        "error": len([l for l in _log_buffer if l.level == "error"]),
        "total": len(_log_buffer)
    }
    return stats

@router.delete("/clear")
async def clear_logs():
    """
    Clear all logs from the buffer.
    """
    global _log_buffer
    _log_buffer = []
    add_log("info", "Logs limpos pelo administrador", "system")
    return {"success": True, "message": "Logs cleared"}
