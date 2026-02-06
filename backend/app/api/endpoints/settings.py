
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
from pydantic import BaseModel
from core.settings_manager import settings_manager

router = APIRouter()

class SettingsUpdate(BaseModel):
    settings: Dict[str, Any]

@router.get("/settings")
async def get_settings():
    """Get all global settings (secrets masked)."""
    return settings_manager.get_all(mask_secrets=True)

@router.post("/settings")
async def update_settings(payload: SettingsUpdate):
    """Update global settings."""
    updated = settings_manager.update(payload.settings)
    return updated

@router.get("/system/health")
async def system_health():
    """Quick system health check."""
    from core.scheduler import Scheduler
    
    # Check DB using Scheduler as proxy
    db_status = "ok"
    try:
        scheduler = Scheduler()
        # Just instantiate check
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    return {
        "status": "online",
        "database": db_status,
        "version": "1.0.0-beta"
    }
