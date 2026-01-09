"""
Logs Endpoint - Provides system logs for the frontend
"""
import os
import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

from backend.core.logger import logger

router = APIRouter()

class LogEntry(BaseModel):
    id: str
    timestamp: str
    level: str
    message: str
    source: str

class LogsResponse(BaseModel):
    logs: List[LogEntry]
    total: int

@router.get("/", response_model=LogsResponse)
async def get_logs(
    level: Optional[str] = Query(None, description="Filter by log level"),
    limit: int = Query(50, description="Number of logs to return"),
    source: Optional[str] = Query(None, description="Filter by source")
):
    """
    Get system logs with optional filtering (Persistent).
    """
    logs = logger.get_logs(limit=limit, level=level, source=source)
    
    return LogsResponse(
        logs=logs,
        total=len(logs)
    )

@router.post("/add")
async def create_log(level: str, message: str, source: str = "api"):
    """
    Add a new log entry.
    """
    entry = logger.log(level, message, source)
    return {"success": True, "log": entry}

@router.get("/stats")
async def get_log_stats():
    """
    Get log statistics by level.
    """
    return logger.get_stats()

@router.delete("/clear")
async def clear_logs():
    """
    Clear all logs (Persistent).
    """
    logger.clear()
    return {"success": True, "message": "Logs cleared"}
