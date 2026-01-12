
from fastapi import APIRouter
from fastapi import APIRouter
from core.status_manager import status_manager

router = APIRouter()

router = APIRouter()

@router.get("/")
async def get_system_status():
    """
    Returns the real-time status of the worker/backend.
    Used by the Command Center UI.
    """
    return status_manager.get_status()
