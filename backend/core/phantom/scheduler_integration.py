"""
Phantom Scheduler Integration — Periodic Phantom session dispatch.

Hooks into the existing Scheduler loop to trigger Phantom sessions
for profiles that have personas assigned and are due for engagement.

This module handles:
- Determining which profiles need Phantom sessions
- Throttling session frequency per profile
- Dispatching sessions with proper browser context
"""

import asyncio
import logging
import os
import random
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from core.database import SessionLocal
from core.phantom.safety import SAFETY, check_kill_switch
from core.phantom.models import PhantomAction, PhantomPersonaAssignment

logger = logging.getLogger("PhantomScheduler")

# ─── Config ──────────────────────────────────────────────────────────────────

# How often to check for phantom-eligible profiles (in scheduler ticks)
# Scheduler runs every 30s → 60 ticks = 30 minutes
PHANTOM_CHECK_INTERVAL_TICKS = 60

# Minimum hours between sessions for the same profile
MIN_SESSION_GAP_HOURS = float(os.getenv("PHANTOM_MIN_SESSION_GAP_HOURS", "2"))

# Counter for tick-based scheduling
_phantom_tick_counter = 0


async def phantom_tick() -> Optional[Dict[str, Any]]:
    """
    Called by the scheduler loop on every iteration.

    Uses a tick counter to only run the real check every PHANTOM_CHECK_INTERVAL_TICKS.
    Returns session info if a session was dispatched, None otherwise.
    """
    global _phantom_tick_counter
    _phantom_tick_counter += 1

    if _phantom_tick_counter < PHANTOM_CHECK_INTERVAL_TICKS:
        return None

    _phantom_tick_counter = 0

    if not check_kill_switch():
        return None

    return await _check_and_dispatch()


async def _check_and_dispatch() -> Optional[Dict[str, Any]]:
    """
    Check all profiles with personas assigned and dispatch sessions
    for those that are due for Phantom engagement.
    """
    db = SessionLocal()
    try:
        # Get all profiles with persona assignments
        assignments = db.query(PhantomPersonaAssignment).all()
        if not assignments:
            return None

        now = datetime.now(timezone.utc)
        dispatched = []
        # Holds strong references to tasks so the GC doesn't collect them early.
        _task_refs: set = set()

        for assignment in assignments:
            profile_id = assignment.profile_id

            # Check if profile had a recent session
            last_action = (
                db.query(PhantomAction)
                .filter(PhantomAction.profile_id == profile_id)
                .order_by(PhantomAction.executed_at.desc())
                .first()
            )

            if last_action:
                hours_since = (now - last_action.executed_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
                if hours_since < MIN_SESSION_GAP_HOURS:
                    continue  # Too soon

            # Jitter: Randomize execution order + small delay to avoid burst patterns
            dispatched.append(profile_id)

        if not dispatched:
            return None

        # Shuffle to avoid predictable ordering
        random.shuffle(dispatched)

        # Limit to max simultaneous sessions
        batch = dispatched[:SAFETY.max_profiles_simultaneous]

        logger.info(f"[PHANTOM] Scheduler dispatching {len(batch)} sessions: {batch}")

        # Dispatch each session as an independent background task.
        # Stagger task STARTS (not completions) so sessions run concurrently
        # without blocking the scheduler loop.
        for i, profile_id in enumerate(batch):
            if i > 0:
                await asyncio.sleep(random.uniform(10, 30))
            task = asyncio.create_task(
                _dispatch_session(profile_id),
                name=f"phantom_session_{profile_id}",
            )
            _task_refs.add(task)
            task.add_done_callback(_task_refs.discard)

        logger.info(f"[PHANTOM] {len(batch)} sessions dispatched as background tasks.")
        return {"dispatched": len(batch), "status": "tasks_created"}

    except Exception as e:
        logger.error(f"[PHANTOM] Scheduler check error: {e}")
        return None
    finally:
        db.close()


async def _dispatch_session(profile_id: int) -> Dict[str, Any]:
    """
    Dispatch a Phantom session for a single profile.

    Resolves the profile slug from the integer ID, launches a dedicated
    browser context via the standard Synapse browser stack (proxy, UA,
    geolocation all resolved from the profile identity), runs the full
    Phantom session, then closes the browser.
    """
    from core.phantom.service import phantom_service
    from core.browser import launch_browser_for_profile, close_browser
    from core.models import Profile

    logger.info(f"[PHANTOM] Dispatching session for profile {profile_id}")

    # ── 1. Resolve profile slug ───────────────────────────────────────────────
    db_resolve = SessionLocal()
    try:
        profile = db_resolve.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            return {
                "profile_id": profile_id,
                "status": "error",
                "message": f"Profile {profile_id} not found in database",
            }
        profile_slug = profile.slug
    finally:
        db_resolve.close()

    # ── 2. Launch browser + run session ──────────────────────────────────────
    p = browser = None
    try:
        p, browser, _context, page = await launch_browser_for_profile(profile_slug)

        db = SessionLocal()
        try:
            return await phantom_service.run_session(
                db=db,
                profile_id=profile_id,
                page=page,
            )
        finally:
            db.close()

    except Exception as e:
        logger.error(f"[PHANTOM] Session error for profile {profile_id} ({profile_slug}): {e}")
        return {"profile_id": profile_id, "status": "error", "message": str(e)}

    finally:
        if p and browser:
            try:
                await close_browser(p, browser)
            except Exception:
                pass

