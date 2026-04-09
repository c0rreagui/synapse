"""
Phantom API — Trust Score & Behavioral Simulation endpoints.

All endpoints are prefixed with /api/v1/phantom/ via main.py router registration.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from core.database import get_db

router = APIRouter()


# ─── Request Models ──────────────────────────────────────────────────────────

class AssignPersonaRequest(BaseModel):
    profile_id: int
    persona_key: str
    custom_overrides: Optional[Dict[str, Any]] = None


class SimulateRequest(BaseModel):
    profile_id: int


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/status")
async def phantom_status():
    """Global Phantom engine status — active sessions, kill switch state."""
    from core.phantom.service import phantom_service
    return phantom_service.get_status()


@router.get("/personas")
async def list_personas():
    """List all available Gen Z personas."""
    from core.phantom.personas import PERSONAS
    return {
        "personas": [
            {
                "key": key,
                "name": p.name,
                "description": p.description,
                "engagement_style": p.engagement_style,
                "primary_niches": p.primary_niches,
                "avg_daily_sessions": p.avg_daily_sessions,
                "avg_session_minutes": p.avg_session_minutes,
            }
            for key, p in PERSONAS.items()
        ]
    }


@router.post("/assign-persona")
async def assign_persona(request: AssignPersonaRequest, db: Session = Depends(get_db)):
    """Assign a persona to a profile — activates Phantom for that profile."""
    from core.phantom.service import phantom_service

    result = phantom_service.assign_persona(
        db=db,
        profile_id=request.profile_id,
        persona_key=request.persona_key,
        custom_overrides=request.custom_overrides,
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.delete("/persona/{profile_id}")
async def remove_persona(profile_id: int, db: Session = Depends(get_db)):
    """Remove persona assignment — deactivates Phantom for that profile."""
    from core.phantom.models import PhantomPersonaAssignment

    assignment = (
        db.query(PhantomPersonaAssignment)
        .filter(PhantomPersonaAssignment.profile_id == profile_id)
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=404, detail=f"No persona assigned to profile {profile_id}")

    db.delete(assignment)
    db.commit()
    return {"status": "removed", "profile_id": profile_id}


@router.get("/all-status")
async def get_all_phantom_status(db: Session = Depends(get_db)):
    """
    Bulk status for all profiles with Phantom enabled.
    Returns a map of profile_id → status in a fixed number of queries regardless of N.
    """
    from core.phantom.models import PhantomPersonaAssignment, PhantomTrustSnapshot, PhantomAction

    assignments = db.query(PhantomPersonaAssignment).all()
    if not assignments:
        return {}

    profile_ids = [a.profile_id for a in assignments]
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # ── Latest trust snapshot per profile (1 query) ───────────────────────────
    # Subquery: max computed_at per profile_id
    latest_snapshot_sq = (
        db.query(
            PhantomTrustSnapshot.profile_id,
            func.max(PhantomTrustSnapshot.computed_at).label("max_at"),
        )
        .filter(PhantomTrustSnapshot.profile_id.in_(profile_ids))
        .group_by(PhantomTrustSnapshot.profile_id)
        .subquery()
    )
    snapshots = {
        s.profile_id: s
        for s in db.query(PhantomTrustSnapshot).join(
            latest_snapshot_sq,
            (PhantomTrustSnapshot.profile_id == latest_snapshot_sq.c.profile_id)
            & (PhantomTrustSnapshot.computed_at == latest_snapshot_sq.c.max_at),
        ).all()
    }

    # ── Actions today per profile (1 query) ───────────────────────────────────
    actions_today_rows = (
        db.query(
            PhantomAction.profile_id,
            func.count(PhantomAction.id).label("cnt"),
        )
        .filter(
            PhantomAction.profile_id.in_(profile_ids),
            PhantomAction.executed_at >= today_start,
        )
        .group_by(PhantomAction.profile_id)
        .all()
    )
    actions_today_map = {row.profile_id: row.cnt for row in actions_today_rows}

    # ── Last action timestamp per profile (1 query) ───────────────────────────
    last_action_sq = (
        db.query(
            PhantomAction.profile_id,
            func.max(PhantomAction.executed_at).label("last_at"),
        )
        .filter(PhantomAction.profile_id.in_(profile_ids))
        .group_by(PhantomAction.profile_id)
        .subquery()
    )
    last_action_map = {row.profile_id: row.last_at for row in db.query(last_action_sq).all()}

    # ── Assemble ──────────────────────────────────────────────────────────────
    result: Dict[int, Any] = {}
    for assignment in assignments:
        pid = assignment.profile_id
        snapshot = snapshots.get(pid)
        last_at = last_action_map.get(pid)
        result[pid] = {
            "enabled": True,
            "persona_key": assignment.persona_key,
            "trust_score": round(snapshot.total_score, 1) if snapshot else 0.0,
            "trust_status": snapshot.status if snapshot else "nascent",
            "actions_today": actions_today_map.get(pid, 0),
            "last_session": last_at.isoformat() if last_at else None,
        }

    return result


@router.get("/trust-score/{profile_id}")
async def get_trust_score(profile_id: int, db: Session = Depends(get_db)):
    """Get current trust score breakdown for a profile."""
    from core.phantom.service import phantom_service
    return phantom_service.get_trust_score(db, profile_id)


@router.get("/trust-score/{profile_id}/history")
async def get_trust_history(
    profile_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get trust score history for time-series chart data."""
    from core.phantom.service import phantom_service
    return phantom_service.get_trust_history(db, profile_id, limit=limit)


@router.get("/actions/{profile_id}")
async def get_action_log(
    profile_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get paginated action log for a profile."""
    from core.phantom.service import phantom_service
    return phantom_service.get_action_log(db, profile_id, limit=limit, offset=offset)


@router.post("/simulate")
async def start_simulation(
    request: SimulateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Trigger a Phantom session immediately for a profile.
    Runs in the background — returns instantly, session executes async.
    """
    from core.phantom.safety import check_kill_switch
    from core.models import Profile
    from core.phantom.scheduler_integration import _dispatch_session

    if not check_kill_switch():
        raise HTTPException(
            status_code=403,
            detail="Phantom is disabled. Set PHANTOM_ENABLED=true to enable.",
        )

    profile = db.query(Profile).filter(Profile.id == request.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile {request.profile_id} not found")

    background_tasks.add_task(_dispatch_session, request.profile_id)

    return {
        "status": "dispatched",
        "profile_id": request.profile_id,
        "profile_slug": profile.slug,
        "message": "Session dispatched in background. Use GET /status to monitor.",
    }


@router.post("/simulate/stop")
async def stop_simulation(request: SimulateRequest):
    """Stop an active Phantom session for a profile."""
    from core.phantom.service import phantom_service
    return await phantom_service.stop_session(request.profile_id)
