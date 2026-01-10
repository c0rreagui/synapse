from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.core.scheduler import scheduler_service
from typing import List

router = APIRouter()

class ScheduleRequest(BaseModel):
    profile_id: str
    video_path: str
    scheduled_time: str
    viral_music_enabled: bool = False 

@router.get("/list")
async def list_schedule():
    return scheduler_service.load_schedule()

@router.post("/create")
async def create_event(request: ScheduleRequest):
    try:
        event = scheduler_service.add_event(
            request.profile_id, 
            request.video_path, 
            request.scheduled_time,
            request.viral_music_enabled
        )
        return event
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{event_id}")
async def delete_schedule(event_id: str):
    success = scheduler_service.delete_event(event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"status": "deleted"}
