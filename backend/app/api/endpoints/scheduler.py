from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.scheduler import scheduler_service
from typing import List

router = APIRouter()

class ScheduleRequest(BaseModel):
    profile_id: str
    video_path: str
    scheduled_time: str
    viral_music_enabled: bool = False
    music_volume: float = 0.0
    trend_category: str = "General"

@router.get("/list")
async def list_schedule():
    return scheduler_service.load_schedule()

@router.post("/create")
async def create_event(request: ScheduleRequest):
    try:
        from datetime import datetime

        # 🧠 SMART SCHEDULER: Conflict Avoidance
        # Parse incoming time
        try:
            scheduled_dt = datetime.fromisoformat(request.scheduled_time)
        except ValueError:
             raise HTTPException(status_code=400, detail="Invalid scheduled_time format. Use ISO 8601.")

        # Check availability
        if not scheduler_service.is_slot_available(request.profile_id, scheduled_dt):
            # Conflict detected! Calculate suggestion
            suggestion_iso = scheduler_service.find_next_available_slot(request.profile_id, scheduled_dt)
            
            raise HTTPException(
                status_code=409, 
                detail={
                    "message": "Conflict detected: Slot is busy.",
                    "suggested_time": suggestion_iso
                }
            )

        event = scheduler_service.add_event(
            request.profile_id, 
            request.video_path, 
            request.scheduled_time,
            request.viral_music_enabled,
            request.music_volume,
            request.trend_category
        )
        return event
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{event_id}")
async def delete_schedule(event_id: str):
    success = scheduler_service.delete_event(event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"status": "deleted"}

class UpdateEventRequest(BaseModel):
    scheduled_time: str

@router.patch("/{event_id}")
async def update_event(event_id: str, request: UpdateEventRequest):
    success = scheduler_service.update_event(event_id, request.scheduled_time)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"status": "updated"}

@router.get("/suggestion/{profile_id}")
async def get_schedule_suggestion(profile_id: str):
    """
    Returns the best posting times cached from the last Oracle analysis.
    """
    from core import session_manager
    meta = session_manager.get_profile_metadata(profile_id)
    best_times = meta.get("oracle_best_times", [])
    
    if not best_times:
        # Fallback if no analysis exists
        return {"best_times": [], "message": "No Oracle analysis found. Run Oracle first."}
        
    return {"best_times": best_times}

class BatchScheduleRequest(BaseModel):
    files: List[str]
    profile_ids: List[str]
    strategy: str # "INTERVAL" | "ORACLE"
    start_time: str # ISO format
    interval_minutes: int = 60
    viral_music_enabled: bool = False

@router.post("/batch")
async def batch_schedule(request: BatchScheduleRequest):
    """
    Creates multiple schedule events based on a strategy.
    Now with SMART LOGIC: Automatically finds free slots if target is busy.
    """
    from datetime import datetime, timedelta
    
    events = []
    
    try:
        start_dt = datetime.fromisoformat(request.start_time)
    except:
        raise HTTPException(status_code=400, detail="Invalid start_time format. Use ISO 8601.")

    current_cursor = start_dt
    
    for video_path in request.files:
        # If multiple profiles, we process them in parallel for this 'time block'
        # But we need to check availability for EACH profile individually.
        
        # NOTE: For simplicity in Batch, if user Selected 5 profiles,
        # we try to schedule all 5 at 'current_cursor'. 
        # If Profile A is busy at 'current_cursor', we find next slot for A.
        # If Profile B is free at 'current_cursor', we schedule B there.
        # This creates a "best effort" parallel schedule.
        
        for profile_id in request.profile_ids:
            
            # 🧠 Smart Logic: Find next available slot starting from current_cursor
            safe_time_iso = scheduler_service.find_next_available_slot(profile_id, current_cursor)
            
            # Create event
            event = scheduler_service.add_event(
                profile_id=profile_id,
                video_path=video_path,
                scheduled_time=safe_time_iso,
                viral_music_enabled=request.viral_music_enabled
            )
            events.append(event)
            
            # We base the next video's time on the ACTUAL scheduled time + Interval
            # This maintains the rhythm/cadence even after dodging a bullet.
            current_time = safe_dt + timedelta(minutes=request.interval_minutes)
            
    return {
        "message": f"Successfully scheduled {len(events)} events.",
        "events": events
    }
