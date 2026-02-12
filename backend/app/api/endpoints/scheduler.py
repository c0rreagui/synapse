from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from core.scheduler import scheduler_service
from typing import List, Dict, Optional
from .. import websocket
import os

router = APIRouter()

class ScheduleRequest(BaseModel):
    profile_id: str
    video_path: str
    scheduled_time: str
    viral_music_enabled: bool = False
    music_volume: float = 0.0
    sound_id: str = None
    sound_title: str = None
    privacy_level: str = "public"

@router.get("/list")
async def list_schedule():
    # [SYN-42] Auto-cleanup expired items before listing
    scheduler_service.cleanup_missed_schedules()
    return scheduler_service.load_schedule()

@router.get("/debug")
def debug_pending_items():
    """Inspect raw DB items to debug timezone issues."""
    from core.database import SessionLocal
    from core.models import ScheduleItem
    from datetime import datetime, timezone
    
    db = SessionLocal()
    try:
        pending = db.query(ScheduleItem).filter(ScheduleItem.status == 'pending').all()
        now_utc = datetime.now(timezone.utc)
        results = []
        for p in pending:
            try:
                # Defensive check: ensure scheduled_time is datetime
                s_time = p.scheduled_time
                tz_info = "Unknown"
                
                # Normalize for comparison
                is_due = False
                if isinstance(s_time, datetime):
                    if s_time.tzinfo is None:
                        s_time_aware = s_time.replace(tzinfo=timezone.utc)
                    else:
                        s_time_aware = s_time
                    is_due = (s_time_aware <= now_utc)
                    tz_info = str(s_time.tzinfo) if s_time.tzinfo else "Naive (Assumed UTC)"

                results.append({
                    "id": p.id,
                    "scheduled_time_raw": str(s_time),
                    "scheduled_time_type": str(type(s_time)),
                    "tzinfo": tz_info,
                    "video_path": p.video_path,
                    "is_due_utc": is_due,
                    "now_utc": str(now_utc)
                })
            except Exception as e:
                 results.append({"id": p.id, "error": str(e)})
                 
        return {"count": len(results), "items": results, "server_utc": str(now_utc)}
    except Exception as e:
        return {"fatal_error": str(e)}
    finally:
        db.close()

@router.post("/create")
async def create_event(request: ScheduleRequest):
    """
    Agenda um único evento.
    
    🧠 SMART LOGIC: Valida com regras completas (intervalo mínimo, max/dia, blocked hours)
    """
    try:
        from datetime import datetime
        from core.smart_logic import smart_logic

        # Parse incoming time
        try:
            scheduled_dt = datetime.fromisoformat(request.scheduled_time)
        except ValueError:
             raise HTTPException(status_code=400, detail="Invalid scheduled_time format. Use ISO 8601.")

        # 🧠 Smart Logic: Validação completa
        result = smart_logic.check_conflict(request.profile_id, scheduled_dt)
        
        if not result.can_proceed:
            # Conflito detectado - retornar detalhes
            raise HTTPException(
                status_code=409, 
                detail={
                    "message": result.issues[0].message if result.issues else "Conflict detected",
                    "suggested_time": result.suggested_time.isoformat() if result.suggested_time else None,
                    "issues": [i.to_dict() for i in result.issues],
                    "can_proceed": False
                }
            )

        # Criar evento
        event = scheduler_service.add_event(
            request.profile_id, 
            request.video_path, 
            request.scheduled_time,
            request.viral_music_enabled,
            request.music_volume,
            sound_id=request.sound_id,
            sound_title=request.sound_title,
            privacy_level=request.privacy_level
        )
        
        # Incluir warnings/info na resposta
        response = {**event}
        if result.issues:
            response["validation_info"] = [i.to_dict() for i in result.issues]
        
        await websocket.notify_schedule_update(scheduler_service.load_schedule())
        return response
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
    scheduled_time: Optional[str] = None
    profile_id: Optional[str] = None
    caption: Optional[str] = None
    privacy_level: Optional[str] = None
    viral_music_enabled: Optional[bool] = None
    music_volume: Optional[float] = None

@router.patch("/{event_id}")
async def update_event(event_id: str, request: UpdateEventRequest):
    # [SYN-EDIT] Build kwargs from provided fields only
    kwargs = {}
    if request.profile_id is not None:
        kwargs['profile_id'] = request.profile_id
    if request.caption is not None:
        kwargs['caption'] = request.caption
    if request.privacy_level is not None:
        kwargs['privacy_level'] = request.privacy_level
    if request.viral_music_enabled is not None:
        kwargs['viral_music_enabled'] = request.viral_music_enabled
    if request.music_volume is not None:
        kwargs['music_volume'] = request.music_volume

    updated_item = scheduler_service.update_event(
        event_id, 
        scheduled_time=request.scheduled_time,
        **kwargs
    )
    if not updated_item:
        raise HTTPException(status_code=404, detail="Event not found")
    await websocket.notify_schedule_update(scheduler_service.load_schedule())
    return updated_item




@router.get("/video-preview/{event_id}")
def video_preview(event_id: str):
    """
    Returns the video file associated with a scheduled event.
    Smart Path Resolution: searches pending/done/approved/processing/data directories.
    Note: Synchronous to avoid blocking asyncio loop with DB operations.
    """
    import os
    from core.database import SessionLocal
    from core.models import ScheduleItem
    from core.config import DATA_DIR, DONE_DIR, APPROVED_DIR, PROCESSING_DIR
    
    # Define directories
    PENDING_DIR = os.path.join(DATA_DIR, "pending")
    # Priority: Pending > Done > Approved > Processing > Data Root
    SEARCH_DIRS = [PENDING_DIR, DONE_DIR, APPROVED_DIR, PROCESSING_DIR, DATA_DIR]
    
    db = SessionLocal()
    try:
        # 1. Resolve Event
        item = None
        try:
            pk = int(event_id)
            item = db.query(ScheduleItem).filter(ScheduleItem.id == pk).first()
        except ValueError:
            item = db.query(ScheduleItem).filter(ScheduleItem.id == event_id).first()
        
        if not item:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # 2. Resolve Video Path
        video_path = item.video_path
        
        # [Fix] Handle Windows paths on Linux (Docker)
        # DB stores D:\... but we are on Linux. os.path.basename fails on backslashes.
        # Check both / and \ by replacing.
        filename = None
        if video_path:
            clean_path = video_path.replace("\\", "/")
            filename = clean_path.split("/")[-1]

        found_path = None
        if video_path and os.path.exists(video_path):
             found_path = video_path
        elif filename:
            # Smart Path Resolution
            for search_dir in SEARCH_DIRS:
                candidate = os.path.join(search_dir, filename)
                if os.path.exists(candidate):
                    found_path = candidate
                    break
        
        # 3. Final Check
        if not found_path:
             raise HTTPException(status_code=404, detail=f"Video file not found: {filename}")
        
        # 4. Serve File
        abs_path = os.path.abspath(found_path)
        return FileResponse(
            abs_path, 
            media_type="video/mp4",
            filename=os.path.basename(abs_path)
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR [video_preview]: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/items/{event_id}")
def get_schedule_item(event_id: str):
    """
    Returns a single schedule item by ID.
    Used for refreshing modal data.
    """
    from core.scheduler import scheduler_service
    # We can load the whole schedule and find it, or query DB directly.
    # Querying DB is more efficient for single item.
    from core.database import SessionLocal
    from core.models import ScheduleItem
    from zoneinfo import ZoneInfo

    db = SessionLocal()
    try:
        try:
            pk = int(event_id)
            item = db.query(ScheduleItem).filter(ScheduleItem.id == pk).first()
        except ValueError:
            item = db.query(ScheduleItem).filter(ScheduleItem.id == event_id).first()
        
        if not item:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Unpack metadata
        meta = item.metadata_info if item.metadata_info else {}
        
        # Handle Timezone
        s_time = item.scheduled_time
        if s_time and s_time.tzinfo is None:
            s_time = s_time.replace(tzinfo=ZoneInfo("America/Sao_Paulo"))

        return {
            "id": str(item.id),
            "profile_id": item.profile_slug, # Map slug to profile_id for frontend compatibility
            "video_path": item.video_path,
            "scheduled_time": s_time.isoformat() if s_time else None,
            "status": item.status,
            "error_message": item.error_message,
            
            # Unpack metadata fields expected by frontend
            "viral_music_enabled": meta.get("viral_music_enabled", False),
            "music_volume": meta.get("music_volume", 0.0),
            "sound_id": meta.get("sound_id"),
            "sound_title": meta.get("sound_title"),
            "caption": meta.get("caption", ""),
            "privacy_level": meta.get("privacy_level", "public"),
            "metadata": meta
        }
    except Exception as e:
        print(f"ERROR [get_schedule_item]: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


class RetryRequest(BaseModel):
    mode: str = "now" # "now" | "next_slot"

@router.post("/{event_id}/retry")
async def retry_event(event_id: str, request: RetryRequest):
    """
    Retries a failed event: restores file and resets status.
    mode="now": Retries immediately (keeps past time).
    mode="next_slot": Moves to next available slot (Same time, next day).
    """
    try:
        result = scheduler_service.retry_event(event_id, mode=request.mode)
        await websocket.notify_schedule_update(scheduler_service.load_schedule())
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
         raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    strategy: str # "INTERVAL" | "ORACLE" | "CUSTOM"
    start_time: str # ISO format
    interval_minutes: int = 60
    custom_times: List[str] = None # ["12:00", "18:00"] for CUSTOM strategy
    viral_music_enabled: bool = False
    mix_viral_sounds: bool = False
    sound_id: str = None
    sound_title: str = None
    smart_captions: bool = False
    privacy_level: str = "public"
    dry_run: bool = False
    force: bool = False
    file_metadata: Dict[str, Dict] = {}

@router.post("/batch")
async def batch_schedule(request: BatchScheduleRequest):
    """
    Creates multiple schedule events based on a strategy.
    
    🧠 SMART BATCH MANAGER:
    - Valida todos os slots com Smart Logic antes de agendar
    - dry_run=True: Retorna apenas validação sem agendar
    - force=True: Ignora warnings e agenda mesmo assim
    - Suporta seleção de música viral (IA ou manual)
    """
    from datetime import datetime, timedelta
    from core.smart_logic import smart_logic
    
    try:
        from zoneinfo import ZoneInfo
        # [SYN-FIX] Handle 'Z' suffix for Python < 3.11 compatibility
        clean_time = request.start_time.replace("Z", "+00:00")
        start_dt = datetime.fromisoformat(clean_time)
        
        # [SYN-TIMEZONE] Force conversion to America/Sao_Paulo for consistency
        local_tz = ZoneInfo("America/Sao_Paulo")
        if start_dt.tzinfo is None:
             start_dt = start_dt.replace(tzinfo=local_tz)
        else:
             start_dt = start_dt.astimezone(local_tz)
             
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid start_time format. Use ISO 8601. Received: {request.start_time}. Error: {e}")

    # 🧠 1. Construir lista de eventos para validação
    validation_events = []
    
    # Pre-calculate custom slots if strategy is CUSTOM
    custom_slots_sorted = []
    if request.strategy == 'CUSTOM' and request.custom_times:
        # Parse times to sort them correctly
        try:
            # Assume format "HH:MM"
            custom_slots_sorted = sorted(request.custom_times, key=lambda x: datetime.strptime(x, "%H:%M"))
        except:
            raise HTTPException(status_code=400, detail="Invalid custom_times format. Use HH:MM")
    
    current_cursor = start_dt
    
    for i, video_path in enumerate(request.files):
        # Determine Scheduled Time based on Strategy
        if request.strategy == 'CUSTOM' and custom_slots_sorted:
            # Cycle through custom slots across days
            slots_count = len(custom_slots_sorted)
            day_offset = i // slots_count
            slot_index = i % slots_count
            
            slot_time_str = custom_slots_sorted[slot_index]
            slot_hour, slot_minute = map(int, slot_time_str.split(':'))
            
            # Base date + offset
            target_date = start_dt + timedelta(days=day_offset)
            current_cursor = target_date.replace(hour=slot_hour, minute=slot_minute, second=0, microsecond=0)
            
        elif request.strategy == 'INTERVAL':
            if i > 0: # First item uses start_time, subsequent add interval
                current_cursor = current_cursor + timedelta(minutes=request.interval_minutes)
        
        # For ORACLE, we might do something else, but currently it likely relies on logic below or client?
        # Actually ORACLE usually implies "Smart Logic" finding best slots. 
        # For now, let's assume Client handles ORACLE by generic Interval or we keep current behavior.
        # Original code: current_cursor = current_cursor + timedelta(minutes=request.interval_minutes) (at end of loop)
        
        # ... logic continues ...
        
        for profile_id in request.profile_ids:
            validation_events.append({
                "id": f"batch_{i}_{profile_id}",
                "profile_id": profile_id,
                "scheduled_time": current_cursor.isoformat(),
                "video_path": video_path
            })
            
    # 🧠 2. Validar todos com Smart Logic
    validation_results = smart_logic.validate_batch(validation_events)
    
    # Converter para resposta serializável
    validation_response = {}
    errors_count = 0
    warnings_count = 0
    
    for event_id, result in validation_results.items():
        validation_response[event_id] = result.to_dict()
        if not result.is_valid:
            errors_count += 1
        elif any(issue.severity.value == "warning" for issue in result.issues):
            warnings_count += 1
    
    # 🧠 3. Se dry_run, retornar apenas validação
    if request.dry_run:
        return {
            "success": True,
            "dry_run": True,
            "can_proceed": errors_count == 0,
            "summary": {
                "total_events": len(validation_events),
                "valid": len(validation_events) - errors_count,
                "errors": errors_count,
                "warnings": warnings_count
            },
            "validation": validation_response
        }
    
    # 🧠 4. Se há erros e force=False, bloquear
    if errors_count > 0 and not request.force:
        return {
            "success": False,
            "error": "Validation failed. Use force=true to override or adjust the schedule.",
            "summary": {
                "total_events": len(validation_events),
                "errors": errors_count,
                "warnings": warnings_count
            },
            "validation": validation_response
        }
    
    # 🧠 5. Agendar eventos
    events = []
    
    # Reset cursor for actual scheduling loop
    current_cursor = start_dt
    
    # Pre-fetch trends if mixing is enabled
    trending_pool = []
    if request.mix_viral_sounds:
        from core.oracle.trend_checker import trend_checker
        trends_data = trend_checker.get_cached_trends()
        trending_pool = trends_data.get("trends", [])
        if not trending_pool:
            print("⚠️ No trends in cache for Auto-Mix. Using default sound.")
    
    # [SYN-SMART] Time Window Logic
    START_HOUR = 8
    END_HOUR = 22

    def adjust_to_window(dt: datetime) -> datetime:
        """Ensures the time is within 08:00 - 22:00. If not, jumps to next valid slot."""
        if dt.hour >= END_HOUR:
            next_day = dt + timedelta(days=1)
            return next_day.replace(hour=START_HOUR, minute=0, second=0, microsecond=0)
        elif dt.hour < START_HOUR:
            return dt.replace(hour=START_HOUR, minute=0, second=0, microsecond=0)
        return dt

    # [SYN-FIX] Define PENDING_DIR
    import os
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    PENDING_DIR = os.path.join(BASE_DIR, "data", "pending")

    for i, filename in enumerate(request.files):
        # [SYN-FIX] Ensure we store absolute path
        if not os.path.isabs(filename):
             video_path = os.path.join(PENDING_DIR, filename)
        else:
             video_path = filename

        # [SYN-CUSTOM] Calculate Time Again for Execution
        if request.strategy == 'CUSTOM' and custom_slots_sorted:
            slots_count = len(custom_slots_sorted)
            day_offset = i // slots_count
            slot_index = i % slots_count
            slot_time_str = custom_slots_sorted[slot_index]
            slot_hour, slot_minute = map(int, slot_time_str.split(':'))
            target_date = start_dt + timedelta(days=day_offset)
            current_cursor = target_date.replace(hour=slot_hour, minute=slot_minute, second=0, microsecond=0)
        elif request.strategy == 'INTERVAL' and i > 0:
             current_cursor = current_cursor + timedelta(minutes=request.interval_minutes)

        # Determine sound
        current_sound_id = request.sound_id
        current_sound_title = request.sound_title
        
        if request.mix_viral_sounds and trending_pool:
            trend = trending_pool[i % len(trending_pool)]
            current_sound_id = trend.get("id")
            current_sound_title = trend.get("title")
        
        for profile_id in request.profile_ids:
            # 1. Enforce Window Strategy (Only for INTERVAL)
            # Custom Time is explicitly chosen by user, so we trust it (unless blocked hour? maybe warn but don't move automatically)
            if request.strategy == 'INTERVAL' and not request.force:
                current_cursor = adjust_to_window(current_cursor)
            
            event = scheduler_service.add_event(
                profile_id=profile_id,
                video_path=video_path,
                scheduled_time=current_cursor.isoformat(),
                viral_music_enabled=request.viral_music_enabled,
                sound_id=current_sound_id,
                sound_title=current_sound_title,
                smart_captions=request.smart_captions,
                privacy_level=request.privacy_level,
                caption=request.file_metadata.get(filename, {}).get("caption") if request.file_metadata else None
            )
            events.append(event)
            
    await websocket.notify_schedule_update(scheduler_service.load_schedule())

    return {
        "success": True,
        "message": f"Successfully scheduled {len(events)} events" + (" (Window enforced)" if not request.force else " (Conflicts ignored)"),
        "summary": {
            "total_events": len(events),
            "warnings_ignored": warnings_count if request.force else 0
        },
        "events": events,
        "viral_music": {
            "enabled": request.viral_music_enabled,
            "sound_title": request.sound_title
        } if request.viral_music_enabled else None
    }

