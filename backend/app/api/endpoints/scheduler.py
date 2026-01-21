from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.scheduler import scheduler_service
from typing import List
from .. import websocket

router = APIRouter()

class ScheduleRequest(BaseModel):
    profile_id: str
    video_path: str
    scheduled_time: str
    viral_music_enabled: bool = False
    music_volume: float = 0.0
    sound_id: str = None
    sound_title: str = None

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
            sound_id=request.sound_id,
            sound_title=request.sound_title
        )
        await websocket.notify_schedule_update(scheduler_service.load_schedule())
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
    await websocket.notify_schedule_update(scheduler_service.load_schedule())
    return {"status": "deleted"}

class UpdateEventRequest(BaseModel):
    scheduled_time: str

@router.patch("/{event_id}")
async def update_event(event_id: str, request: UpdateEventRequest):
    success = scheduler_service.update_event(event_id, request.scheduled_time)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    await websocket.notify_schedule_update(scheduler_service.load_schedule())
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
    sound_id: str = None  # 🎵 ID da música viral selecionada
    sound_title: str = None  # 🎵 Título da música para busca

@router.post("/batch")
async def batch_schedule(request: BatchScheduleRequest):
    """
    Creates multiple schedule events based on a strategy.
    Now with SMART LOGIC: Automatically finds free slots if target is busy.
    Supports viral music selection (IA or manual).
    """
    from datetime import datetime, timedelta
    
    events = []
    
    try:
        start_dt = datetime.fromisoformat(request.start_time)
    except:
        raise HTTPException(status_code=400, detail="Invalid start_time format. Use ISO 8601.")

    current_cursor = start_dt
    
    for video_path in request.files:
        # We attempt to schedule this video for ALL selected profiles at roughly the same time (current_cursor)
        # However, we must respect each profile's individual availability.
        
        for profile_id in request.profile_ids:
            
            # 🧠 Smart Logic: Find next available slot starting from current_cursor
            # Note: This might push the schedule forward for a busy profile, but others might stay at current_cursor.
            safe_time_iso = scheduler_service.find_next_available_slot(profile_id, current_cursor)
            
            # Create event with viral music if enabled
            event = scheduler_service.add_event(
                profile_id=profile_id,
                video_path=video_path,
                scheduled_time=safe_time_iso,
                viral_music_enabled=request.viral_music_enabled,
                sound_id=request.sound_id,
                sound_title=request.sound_title
            )
            events.append(event)
            
        # We simply add the interval to the base cursor.
        current_cursor = current_cursor + timedelta(minutes=request.interval_minutes)
            
    await websocket.notify_schedule_update(scheduler_service.load_schedule())

    return {
        "message": f"Successfully scheduled {len(events)} events.",
        "events": events,
        "viral_music": {
            "enabled": request.viral_music_enabled,
            "sound_title": request.sound_title
        } if request.viral_music_enabled else None
    }

