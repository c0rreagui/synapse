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
            sound_title=request.sound_title
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
    sound_id: str = None  # 🎵 ID da música viral selecionada
    sound_title: str = None  # 🎵 Título da música para busca
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
        start_dt = datetime.fromisoformat(request.start_time)
    except:
        raise HTTPException(status_code=400, detail="Invalid start_time format. Use ISO 8601.")

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
    
    # 🧠 5. Agendar eventos (com Smart Logic para encontrar slots livres)
    events = []
    current_cursor = start_dt
    
    for video_path in request.files:
        for profile_id in request.profile_ids:
            # Smart Logic: Encontra slot disponível respeitando regras
            safe_time_iso = scheduler_service.find_next_available_slot(profile_id, current_cursor)
            
            event = scheduler_service.add_event(
                profile_id=profile_id,
                video_path=video_path,
                scheduled_time=safe_time_iso,
                viral_music_enabled=request.viral_music_enabled,
                sound_id=request.sound_id,
                sound_title=request.sound_title
            )
            events.append(event)
            
        current_cursor = current_cursor + timedelta(minutes=request.interval_minutes)
            
    await websocket.notify_schedule_update(scheduler_service.load_schedule())

    return {
        "success": True,
        "message": f"Successfully scheduled {len(events)} events.",
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

