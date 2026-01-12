from fastapi import APIRouter, HTTPException
from core.analytics.aggregator import analytics_engine

router = APIRouter()

@router.get("/{profile_id}")
async def get_analytics(profile_id: str):
    try:
        data = analytics_engine.get_profile_analytics(profile_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
