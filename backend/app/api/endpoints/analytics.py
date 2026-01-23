
from fastapi import APIRouter, HTTPException, Body
from core.analytics.aggregator import analytics_service
from core.oracle.deep_analytics import deep_analytics

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

@router.post("/video/analyze")
async def analyze_video(video_data: dict = Body(...)):
    """
    [Oracle V2] Analisa performance profunda de um vídeo.
    Requer payload com dados do vídeo (stats, duration).
    """
    try:
        result = deep_analytics.analyze_video_performance(video_data)
        if "error" in result:
             raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
