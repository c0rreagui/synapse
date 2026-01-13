
from fastapi import APIRouter, HTTPException
from core.analytics.aggregator import analytics_service

router = APIRouter()

@router.get("/{profile_id}")
async def get_analytics(profile_id: str):
    """
    Returns deep analytics for a profile.
    """
    try:
        data = analytics_service.get_profile_analytics(profile_id)
        if not data:
             raise HTTPException(status_code=404, detail="Profile not found or no metadata available.")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
