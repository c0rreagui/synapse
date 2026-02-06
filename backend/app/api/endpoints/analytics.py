
from fastapi import APIRouter, HTTPException, Body
from core.oracle.analytics_aggregator import analytics_aggregator
from core.oracle.deep_analytics import deep_analytics

router = APIRouter()

@router.get("/{profile_id}")
async def get_analytics(profile_id: str):
    """
    Returns deep analytics for a profile.
    """
    from fastapi.concurrency import run_in_threadpool
    try:
        # Use the new Oracle-powered Aggregator
        data = await run_in_threadpool(analytics_aggregator.get_dashboard_data, profile_id)
        
        if "error" in data:
             # Return as is (might be empty state)
             return data
             
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
