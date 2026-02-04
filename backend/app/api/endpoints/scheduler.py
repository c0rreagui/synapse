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
    mix_viral_sounds: bool = False  # 🔀 [SYN-39] Unique trend per video
    sound_id: str = None  # 🎵 ID da música viral selecionada (se mix_viral_sounds for False)
    sound_title: str = None  # 🎵 Título da música para busca
    smart_captions: bool = False  # ✍️ [SYN-40] Generate AI descriptions
    privacy_level: str = "public"  # 🔒 [SYN-NEW] Visibility (public/private)
    dry_run: bool = False  # 🧠 Se True, apenas valida sem agendar
    force: bool = False  # 🧠 Se True, ignora warnings e agenda mesmo assim

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
        # [SYN-FIX] Handle 'Z' suffix for Python < 3.11 compatibility
        clean_time = request.start_time.replace("Z", "+00:00")
        start_dt = datetime.fromisoformat(clean_time)
    except:
        raise HTTPException(status_code=400, detail=f"Invalid start_time format. Use ISO 8601. Received: {request.start_time}")

    # 🧠 1. Construir lista de eventos para validação
    validation_events = []
    current_cursor = start_dt
    
    for i, video_path in enumerate(request.files):
        for profile_id in request.profile_ids:
            validation_events.append({
                "id": f"batch_{i}_{profile_id}",
                "profile_id": profile_id,
                "scheduled_time": current_cursor.isoformat(),
                "video_path": video_path
            })
        current_cursor = current_cursor + timedelta(minutes=request.interval_minutes)
    
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
    current_cursor = start_dt
    
    # Pre-fetch trends if mixing is enabled
    trending_pool = []
    if request.mix_viral_sounds:
        from core.oracle.trend_checker import trend_checker
        trends_data = trend_checker.get_cached_trends()
        trending_pool = trends_data.get("trends", [])
        if not trending_pool:
            # Fallback/Error? For now, if pool is empty, we just skip mixing
            print("⚠️ No trends in cache for Auto-Mix. Using default sound.")
    
    # [SYN-SMART] Time Window Logic
    START_HOUR = 8
    END_HOUR = 22

    def adjust_to_window(dt: datetime) -> datetime:
        """Ensures the time is within 08:00 - 22:00. If not, jumps to next valid slot."""
        if dt.hour >= END_HOUR:
            # Move to next day 08:00
            next_day = dt + timedelta(days=1)
            return next_day.replace(hour=START_HOUR, minute=0, second=0, microsecond=0)
        elif dt.hour < START_HOUR:
            # Move to today 08:00
            return dt.replace(hour=START_HOUR, minute=0, second=0, microsecond=0)
        return dt

    # [SYN-FIX] Define PENDING_DIR to resolve absolute paths
    import os
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    PENDING_DIR = os.path.join(BASE_DIR, "data", "pending")

    for i, filename in enumerate(request.files):
        # [SYN-FIX] Ensure we store absolute path in DB so Scheduler can find it
        if not os.path.isabs(filename):
             video_path = os.path.join(PENDING_DIR, filename)
        else:
             video_path = filename

        # Determine sound for this video index
        current_sound_id = request.sound_id
        current_sound_title = request.sound_title
        
        if request.mix_viral_sounds and trending_pool:
            # Round-robin distribution
            trend = trending_pool[i % len(trending_pool)]
            current_sound_id = trend.get("id")
            current_sound_title = trend.get("title")
        
        for profile_id in request.profile_ids:
            # 1. Enforce Window Strategy FIRST
            if not request.force:
                current_cursor = adjust_to_window(current_cursor)
            
            # 2. Smart Logic: Find next available slot if conflicted (but staying in window?)
            # safe_time_iso = scheduler_service.find_next_available_slot(profile_id, current_cursor)
            # NOTE: scheduler_service might push it out of window if conflicted.
            # Ideally we check conflict manually and push forward if needed.
            
            # For now, let's use the cursor directly and let Validation warn us, or just schedule.
            # User wants "re-fitted".
            
            event = scheduler_service.add_event(
                profile_id=profile_id,
                video_path=video_path,
                scheduled_time=current_cursor.isoformat(),
                viral_music_enabled=request.viral_music_enabled,
                sound_id=current_sound_id,
                sound_title=current_sound_title,
                smart_captions=request.smart_captions,
                privacy_level=request.privacy_level
            )
            events.append(event)
            
        # Increment for next video
        current_cursor = current_cursor + timedelta(minutes=request.interval_minutes)
        # Check window again for next loop? (Will be checked at start of loop)
        if not request.force:
            current_cursor = adjust_to_window(current_cursor)
            
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

