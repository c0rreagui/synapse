from fastapi import APIRouter, HTTPException
from typing import List, Dict
from app.core import session_manager

router = APIRouter()

@router.get("/list", response_model=List[Dict[str, str]])
async def get_profiles():
    """
    Returns the list of active TikTok sessions.
    Scans the backend/data/sessions directory dynamically.
    """
    try:
        return session_manager.list_available_sessions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[Dict[str, str]])
async def get_profiles_root():
    """Alias for /list for backward compatibility"""
    return session_manager.list_available_sessions()
