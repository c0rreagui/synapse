"""
Phantom Service — Top-level orchestrator for Phantom sessions.

This is the main entry point for running Phantom sessions.
It coordinates the behavioral model, action runners, trust scorer,
and action logging into a coherent execution pipeline.
"""

import asyncio
import random
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func

from core.phantom.safety import SAFETY, check_kill_switch, check_proxy_requirement
from core.phantom.behavioral_model import behavioral_model, PlannedAction
from core.phantom.trust_score import TrustScoreCalculator
from core.phantom.personas import get_persona, apply_overrides, list_persona_keys
from core.phantom.models import PhantomAction, PhantomPersonaAssignment
from core.phantom.actions.consumption import consumption_runner
from core.phantom.actions.social import social_runner
from core.phantom.actions.exploration import exploration_runner

logger = logging.getLogger("PhantomService")

# Track active sessions for concurrency control
_active_sessions: Dict[int, datetime] = {}
_session_lock = asyncio.Lock()


class PhantomService:
    """
    Orchestrates Phantom sessions — the main public API.

    Usage:
        service = PhantomService()
        await service.run_session(db, profile_id, page)
        score = service.get_trust_score(db, profile_id)
    """

    async def run_session(
        self,
        db: Session,
        profile_id: int,
        page,  # playwright.async_api.Page
        proxy_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute a full Phantom session for a profile.

        1. Validates kill switch, proxy, and concurrency
        2. Resolves persona and current trust score
        3. Plans session via behavioral model
        4. Executes each action sequentially with human-like delays
        5. Logs every action (batch commit at end)
        6. Recomputes trust score

        Returns:
            Session metrics and updated trust score.
        """
        # ─── Pre-flight checks ──────────────────────────────
        if not check_kill_switch():
            return {"status": "disabled", "message": "Phantom is disabled. Set PHANTOM_ENABLED=true"}

        if not check_proxy_requirement(proxy_id):
            return {"status": "error", "message": "Proxy required for Phantom sessions"}

        # Atomic concurrency check under lock
        async with _session_lock:
            if len(_active_sessions) >= SAFETY.max_profiles_simultaneous:
                return {"status": "busy", "message": f"Max concurrent sessions ({SAFETY.max_profiles_simultaneous}) reached"}

            if profile_id in _active_sessions:
                return {"status": "already_running", "message": f"Session already active for profile {profile_id}"}

            _active_sessions[profile_id] = datetime.now(timezone.utc)

        # ─── Session start ──────────────────────────────────
        session_start = time.time()

        result = {
            "profile_id": profile_id,
            "status": "completed",
            "actions_executed": 0,
            "actions_failed": 0,
            "session_duration_s": 0,
            "trust_score": None,
        }

        try:
            # Resolve persona
            persona_assignment = (
                db.query(PhantomPersonaAssignment)
                .filter(PhantomPersonaAssignment.profile_id == profile_id)
                .first()
            )
            if not persona_assignment:
                logger.warning(f"[PHANTOM] No persona assigned for profile {profile_id}")
                result["status"] = "error"
                result["message"] = "No persona assigned. Use assign_persona() first."
                return result

            persona = get_persona(persona_assignment.persona_key)
            if not persona:
                result["status"] = "error"
                result["message"] = f"Unknown persona: {persona_assignment.persona_key}"
                return result

            if persona_assignment.custom_overrides:
                persona = apply_overrides(persona, persona_assignment.custom_overrides)

            # Get current trust score
            calculator = TrustScoreCalculator(db)
            current_score_data = calculator.compute(profile_id)
            current_score = current_score_data["total_score"]

            # Count today's actions
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            daily_count = (
                db.query(PhantomAction)
                .filter(
                    PhantomAction.profile_id == profile_id,
                    PhantomAction.executed_at >= today_start,
                )
                .count()
            )

            # Check for gap day
            consecutive_days = self._count_consecutive_active_days(db, profile_id)
            if behavioral_model.should_skip_day(persona, consecutive_days):
                logger.info(f"[PHANTOM] Gap day for profile {profile_id} (active {consecutive_days} consecutive days)")
                result["status"] = "gap_day"
                result["message"] = f"Natural gap day after {consecutive_days} consecutive active days"
                return result

            # Plan session
            now = datetime.now(timezone.utc)
            planned_actions = behavioral_model.plan_session(
                persona=persona,
                current_score=current_score,
                hour=now.hour,
                weekday=now.weekday(),
                daily_action_count=daily_count,
            )

            if not planned_actions:
                result["status"] = "skipped"
                result["message"] = "No actions planned for this time window"
                return result

            logger.info(f"[PHANTOM] Starting session: {len(planned_actions)} actions for profile {profile_id}")

            # Execute actions — accumulate log entries, commit once at end
            for action in planned_actions:
                try:
                    action_result = await self._execute_action(page, action)
                    self._log_action(db, profile_id, action, action_result)
                    result["actions_executed"] += 1
                except Exception as e:
                    logger.error(f"[PHANTOM] Action {action.action_type} failed: {e}")
                    self._log_action(db, profile_id, action, {
                        "success": False,
                        "error": str(e),
                    })
                    result["actions_failed"] += 1

                    # Check for captcha — trigger cooldown
                    if "captcha" in str(e).lower():
                        logger.warning(f"[PHANTOM] CAPTCHA detected for profile {profile_id}! Cooling down.")
                        result["status"] = "captcha_cooldown"
                        break

                # Human-like delay between actions
                delay = max(
                    SAFETY.min_action_interval_seconds,
                    random.gauss(3.5, 1.2),
                )
                await asyncio.sleep(delay)

            # Batch commit all logged actions at once
            try:
                db.commit()
            except Exception as e:
                logger.error(f"[PHANTOM] Failed to commit action log: {e}")
                db.rollback()
                result["status"] = "error"
                result["message"] = f"DB commit failed: {e}"
                return result

            # Recompute trust score after session
            new_score_data = calculator.compute(profile_id)
            calculator.persist_snapshot(profile_id, new_score_data)
            result["trust_score"] = new_score_data

        except Exception as e:
            logger.error(f"[PHANTOM] Session error for profile {profile_id}: {e}")
            db.rollback()
            result["status"] = "error"
            result["message"] = str(e)
        finally:
            async with _session_lock:
                _active_sessions.pop(profile_id, None)
            result["session_duration_s"] = round(time.time() - session_start, 1)

        return result

    async def stop_session(self, profile_id: int) -> Dict[str, Any]:
        """Stop an active Phantom session for a profile."""
        async with _session_lock:
            if profile_id in _active_sessions:
                _active_sessions.pop(profile_id)
                return {"status": "stopped", "profile_id": profile_id}
            return {"status": "not_running", "profile_id": profile_id}

    async def _execute_action(self, page, action: PlannedAction) -> Dict[str, Any]:
        """Route a planned action to its appropriate runner."""
        params = action.params or {}

        if action.action_type == "scroll":
            return await consumption_runner.scroll_fyp(
                page,
                duration_minutes=params.get("duration_minutes", 10),
                like_probability=params.get("like_probability", 0.15),
                save_probability=params.get("save_probability", 0.03),
            )

        elif action.action_type == "watch":
            # Individual watch tracking is handled within scroll_fyp
            return {"success": True, "action": "watch", "niche": params.get("niche")}

        elif action.action_type in ("like", "save"):
            # These are handled within consumption scroll
            return {"success": True, "action": action.action_type}

        elif action.action_type == "comment":
            return await social_runner.comment_on_video(
                page,
                style=params.get("style", "reaction"),
                language=params.get("language", "en"),
            )

        elif action.action_type == "follow":
            return await social_runner.follow_creator(page)

        elif action.action_type == "search":
            return await exploration_runner.search(
                page,
                niche=params.get("niche", "trending"),
                query_type=params.get("query_type", "hashtag"),
            )

        elif action.action_type == "explore":
            if action.subtype == "tab_navigation":
                return await exploration_runner.navigate_tab(
                    page, tabs=params.get("tabs", ["fyp", "following"]),
                )
            elif action.subtype == "notification_check":
                return await exploration_runner.check_notifications(page)
            elif action.subtype == "discover_page":
                return await exploration_runner.browse_discover(page)
            else:
                return await exploration_runner.visit_own_profile(page)

        else:
            logger.warning(f"[PHANTOM] Unknown action type: {action.action_type}")
            return {"success": False, "error": f"Unknown action: {action.action_type}"}

    def _log_action(
        self,
        db: Session,
        profile_id: int,
        action: PlannedAction,
        result: Dict[str, Any],
    ):
        """
        Add action to the session's pending writes (no commit).

        Actions are batch-committed at the end of the session for atomicity.
        """
        log_entry = PhantomAction(
            profile_id=profile_id,
            action_type=action.action_type,
            action_subtype=action.subtype,
            success=result.get("success", False),
            duration_ms=result.get("duration_ms"),
            error_code=result.get("error_code") or (result.get("error", "")[:50] if not result.get("success") else None),
            trust_impact=self._calc_trust_impact(action, result),
            content_niche=action.params.get("niche") if action.params else None,
            target_user_handle=result.get("creator_handle"),
            metadata_json={
                k: v for k, v in result.items()
                if k not in ("success", "error", "error_code", "creator_handle")
            },
        )
        db.add(log_entry)

    def _calc_trust_impact(self, action: PlannedAction, result: Dict[str, Any]) -> int:
        """Calculate trust impact points for an action."""
        if not result.get("success", False):
            return 0

        impact_map = {
            "scroll": 3,
            "watch": 1,
            "like": 1,
            "save": 2,
            "comment": 4,
            "follow": 2,
            "search": 1,
            "explore": 1,
        }
        return impact_map.get(action.action_type, 0)

    def _count_consecutive_active_days(self, db: Session, profile_id: int) -> int:
        """Count consecutive days with at least one action (single query)."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        active_dates = (
            db.query(func.date(PhantomAction.executed_at))
            .filter(
                PhantomAction.profile_id == profile_id,
                PhantomAction.executed_at >= cutoff,
            )
            .group_by(func.date(PhantomAction.executed_at))
            .all()
        )

        active_set = {d[0] for d in active_dates}
        today = datetime.now(timezone.utc).date()
        count = 0
        for i in range(1, 31):
            if (today - timedelta(days=i)) in active_set:
                count += 1
            else:
                break
        return count

    def assign_persona(
        self,
        db: Session,
        profile_id: int,
        persona_key: str,
        custom_overrides: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Assign a persona to a profile."""
        persona = get_persona(persona_key)
        if not persona:
            return {"status": "error", "message": f"Unknown persona: {persona_key}. Available: {list_persona_keys()}"}

        existing = (
            db.query(PhantomPersonaAssignment)
            .filter(PhantomPersonaAssignment.profile_id == profile_id)
            .first()
        )
        if existing:
            existing.persona_key = persona_key
            existing.custom_overrides = custom_overrides or {}
            existing.assigned_at = datetime.now(timezone.utc)
        else:
            assignment = PhantomPersonaAssignment(
                profile_id=profile_id,
                persona_key=persona_key,
                custom_overrides=custom_overrides or {},
            )
            db.add(assignment)

        db.commit()
        return {
            "status": "assigned",
            "profile_id": profile_id,
            "persona": persona_key,
            "persona_name": persona.name,
        }

    def get_trust_score(self, db: Session, profile_id: int) -> Dict[str, Any]:
        """Get current trust score for a profile."""
        calculator = TrustScoreCalculator(db)
        return calculator.compute(profile_id)

    def get_trust_history(
        self,
        db: Session,
        profile_id: int,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get trust score history for time-series visualization."""
        from core.phantom.models import PhantomTrustSnapshot
        snapshots = (
            db.query(PhantomTrustSnapshot)
            .filter(PhantomTrustSnapshot.profile_id == profile_id)
            .order_by(PhantomTrustSnapshot.computed_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "total_score": s.total_score,
                "behavioral_consistency": s.behavioral_consistency,
                "engagement_quality": s.engagement_quality,
                "natural_progression": s.natural_progression,
                "platform_adherence": s.platform_adherence,
                "session_health": s.session_health,
                "status": s.status,
                "actions_counted": s.actions_counted,
                "computed_at": s.computed_at.isoformat(),
            }
            for s in reversed(snapshots)
        ]

    def get_action_log(
        self,
        db: Session,
        profile_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get paginated action log for a profile."""
        total = (
            db.query(PhantomAction)
            .filter(PhantomAction.profile_id == profile_id)
            .count()
        )
        actions = (
            db.query(PhantomAction)
            .filter(PhantomAction.profile_id == profile_id)
            .order_by(PhantomAction.executed_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "actions": [
                {
                    "id": a.id,
                    "action_type": a.action_type,
                    "action_subtype": a.action_subtype,
                    "success": a.success,
                    "trust_impact": a.trust_impact,
                    "content_niche": a.content_niche,
                    "target_user_handle": a.target_user_handle,
                    "error_code": a.error_code,
                    "duration_ms": a.duration_ms,
                    "executed_at": a.executed_at.isoformat(),
                }
                for a in actions
            ],
        }

    def get_status(self) -> Dict[str, Any]:
        """Get global Phantom status."""
        return {
            "enabled": SAFETY.enabled,
            "active_sessions": len(_active_sessions),
            "max_sessions": SAFETY.max_profiles_simultaneous,
            "active_profiles": list(_active_sessions.keys()),
        }


# ─── Singleton ───────────────────────────────────────────────────────────────

phantom_service = PhantomService()
