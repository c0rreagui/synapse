"""
Phantom Trust Score Calculator — 5-dimension composite scoring engine.

Computes a 0-100 trust score from:
    1. Behavioral Consistency (w=0.30) — Usage pattern regularity
    2. Engagement Quality (w=0.25) — Comment diversity, like ratios
    3. Natural Progression (w=0.20) — Organic growth over time
    4. Platform Adherence (w=0.15) — Rate limit / CAPTCHA compliance
    5. Session Health (w=0.10) — Cookie, proxy, keepalive status

The score determines which actions are unlocked (action gates).
Snapshots are persisted for time-series visualization.
"""

import math
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from collections import Counter

from sqlalchemy.orm import Session

from core.phantom.models import PhantomAction, PhantomTrustSnapshot

logger = logging.getLogger("PhantomTrustScore")


# ─── Constants ───────────────────────────────────────────────────────────────

WEIGHTS = {
    "behavioral_consistency": 0.30,
    "engagement_quality": 0.25,
    "natural_progression": 0.20,
    "platform_adherence": 0.15,
    "session_health": 0.10,
}

# Expected Gen Z hourly distribution (24h, normalized weights)
# Higher weight = higher expected activity
GEN_Z_HOUR_DISTRIBUTION = {
    0: 0.03, 1: 0.01, 2: 0.005, 3: 0.002, 4: 0.001, 5: 0.005,
    6: 0.01, 7: 0.03, 8: 0.04, 9: 0.04, 10: 0.03, 11: 0.04,
    12: 0.06, 13: 0.06, 14: 0.04, 15: 0.03, 16: 0.03, 17: 0.04,
    18: 0.05, 19: 0.08, 20: 0.10, 21: 0.10, 22: 0.09, 23: 0.06,
}

STATUS_THRESHOLDS = [
    (0, 10, "nascent"),
    (11, 20, "warming"),
    (21, 40, "building"),
    (41, 60, "established"),
    (61, 80, "trusted"),
    (81, 100, "organic"),
]

ACTION_GATES = {
    "scroll": 0,
    "watch": 0,
    "like": 11,
    "save": 11,
    "explore": 11,
    "search": 11,
    "comment": 21,
    "follow": 21,
    "unfollow": 21,
    "post": 41,
    "edit_profile": 41,
    "duet": 61,
    "stitch": 61,
    "share_external": 61,
}


# ─── Helper Functions ────────────────────────────────────────────────────────

def _coefficient_of_variation(values: List[float]) -> float:
    """CV = std_dev / mean. Lower = more consistent."""
    if not values or len(values) < 2:
        return 1.0
    mean = sum(values) / len(values)
    if mean == 0:
        return 1.0
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return (variance ** 0.5) / mean


def _cosine_similarity(vec_a: Dict[int, float], vec_b: Dict[int, float]) -> float:
    """Cosine similarity between two sparse vectors keyed by hour (0-23)."""
    keys = set(vec_a.keys()) | set(vec_b.keys())
    dot = sum(vec_a.get(k, 0) * vec_b.get(k, 0) for k in keys)
    mag_a = sum(v ** 2 for v in vec_a.values()) ** 0.5
    mag_b = sum(v ** 2 for v in vec_b.values()) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _get_status(score: float) -> str:
    """Map numeric score to status label."""
    for low, high, label in STATUS_THRESHOLDS:
        if low <= score <= high:
            return label
    return "organic"


def is_action_allowed(action_type: str, current_score: float) -> bool:
    """Check if action is unlocked at the current trust level."""
    required = ACTION_GATES.get(action_type, 0)
    return current_score >= required


# ─── Core Calculator ─────────────────────────────────────────────────────────

class TrustScoreCalculator:
    """
    Computes trust score for a profile based on its action history.

    Usage:
        calculator = TrustScoreCalculator(db_session)
        score = calculator.compute(profile_id)
        calculator.persist_snapshot(profile_id, score)
    """

    def __init__(self, db: Session):
        self.db = db

    def compute(
        self,
        profile_id: int,
        window_days: int = 7,
        account_created_at: Optional[datetime] = None,
    ) -> Dict:
        """
        Compute full trust score breakdown.

        Returns dict with dimension scores, total, status, and gate info.
        """
        actions = self._get_actions(profile_id, window_days)

        bc = self._behavioral_consistency(actions, window_days)
        eq = self._engagement_quality(actions, profile_id)
        np_ = self._natural_progression(actions, profile_id, account_created_at)
        pa = self._platform_adherence(actions)
        sh = self._session_health(profile_id)

        total = (
            WEIGHTS["behavioral_consistency"] * bc
            + WEIGHTS["engagement_quality"] * eq
            + WEIGHTS["natural_progression"] * np_
            + WEIGHTS["platform_adherence"] * pa
            + WEIGHTS["session_health"] * sh
        )

        total = round(min(100, max(0, total)), 1)

        return {
            "behavioral_consistency": round(bc, 1),
            "engagement_quality": round(eq, 1),
            "natural_progression": round(np_, 1),
            "platform_adherence": round(pa, 1),
            "session_health": round(sh, 1),
            "total_score": total,
            "status": _get_status(total),
            "actions_counted": len(actions),
            "window_days": window_days,
        }

    def persist_snapshot(self, profile_id: int, score_data: Dict) -> PhantomTrustSnapshot:
        """Save a trust score snapshot to the database."""
        snapshot = PhantomTrustSnapshot(
            profile_id=profile_id,
            behavioral_consistency=score_data["behavioral_consistency"],
            engagement_quality=score_data["engagement_quality"],
            natural_progression=score_data["natural_progression"],
            platform_adherence=score_data["platform_adherence"],
            session_health=score_data["session_health"],
            total_score=score_data["total_score"],
            status=score_data["status"],
            actions_counted=score_data["actions_counted"],
            window_days=score_data["window_days"],
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        logger.info(
            f"[TRUST_SCORE] Profile {profile_id}: {score_data['total_score']} "
            f"({score_data['status']}) — {score_data['actions_counted']} actions"
        )
        return snapshot

    # ─── Dimension Calculators ───────────────────────────────────────────

    def _behavioral_consistency(self, actions: List[PhantomAction], window_days: int) -> float:
        """
        Measures how consistent the daily usage pattern is.

        Sub-scores:
            - Session regularity (low CV of daily action counts)
            - Temporal alignment (activity matches Gen Z hour distribution)
            - Weekend boost (Gen Z uses ~40% more on weekends)
            - Action type diversity
        """
        if not actions:
            return 0.0

        now = datetime.now(timezone.utc)

        # 1. Session regularity (0-30 pts)
        daily_counts = Counter()
        for a in actions:
            day_key = a.executed_at.date()
            daily_counts[day_key] += 1

        # Fill missing days with 0
        all_days = [(now - timedelta(days=i)).date() for i in range(window_days)]
        daily_values = [daily_counts.get(d, 0) for d in all_days]

        cv = _coefficient_of_variation(daily_values)
        regularity = max(0, 30 * (1 - min(cv, 1.0)))

        # 2. Temporal alignment (0-30 pts)
        hour_counts: Dict[int, float] = Counter()
        for a in actions:
            hour_counts[a.executed_at.hour] += 1
        total_actions = sum(hour_counts.values()) or 1
        hour_distribution = {h: c / total_actions for h, c in hour_counts.items()}

        alignment = _cosine_similarity(hour_distribution, GEN_Z_HOUR_DISTRIBUTION)
        temporal = alignment * 30

        # 3. Weekend boost (0-20 pts)
        weekday_actions = sum(1 for a in actions if a.executed_at.weekday() < 5)
        weekend_actions = sum(1 for a in actions if a.executed_at.weekday() >= 5)

        # Normalize to per-day
        weekday_avg = weekday_actions / max(min(window_days, 5), 1)
        weekend_avg = weekend_actions / max(min(window_days - 5, 2) if window_days > 5 else 1, 1)

        if weekday_avg > 0:
            ratio = weekend_avg / weekday_avg
        else:
            ratio = 0

        expected_ratio = 1.4
        weekend_score = max(0, 20 - abs(ratio - expected_ratio) * 12)

        # 4. Action diversity (0-20 pts)
        action_types = set(a.action_type for a in actions)
        expected_types = {"scroll", "watch", "like", "comment", "follow", "search", "explore"}
        diversity = (len(action_types & expected_types) / len(expected_types)) * 20

        return regularity + temporal + weekend_score + diversity

    def _engagement_quality(self, actions: List[PhantomAction], profile_id: int) -> float:
        """
        Measures quality over quantity of interactions.

        Sub-scores:
            - Comment diversity (unique comments vs. total)
            - Like-to-watch ratio (healthy range: 10-25%)
            - Creator distribution (engaging with diverse creators)
            - Watch completion rate
        """
        if not actions:
            return 0.0

        # Classify actions
        comments = [a for a in actions if a.action_type == "comment"]
        watches = [a for a in actions if a.action_type == "watch"]
        likes = [a for a in actions if a.action_type == "like"]

        # 1. Comment diversity (0-30 pts)
        if comments:
            comment_texts = [a.metadata_json.get("text", "") for a in comments if a.metadata_json]
            unique_ratio = len(set(comment_texts)) / len(comment_texts) if comment_texts else 0
            comment_score = unique_ratio * 30
        else:
            comment_score = 15  # No comments yet is OK (just started)

        # 2. Like ratio (0-25 pts)
        watch_count = len(watches)
        like_count = len(likes)
        if watch_count > 0:
            ratio = like_count / watch_count
            if 0.10 <= ratio <= 0.25:
                ratio_score = 25
            elif ratio < 0.10:
                ratio_score = (ratio / 0.10) * 25
            else:
                ratio_score = max(0, 25 - (ratio - 0.25) * 50)
        else:
            ratio_score = 10  # Not enough data

        # 3. Creator distribution (0-25 pts)
        unique_creators = set()
        for a in actions:
            if a.target_user_handle:
                unique_creators.add(a.target_user_handle)

        if len(unique_creators) >= 20:
            dist_score = 25
        elif len(unique_creators) >= 10:
            dist_score = 18
        else:
            dist_score = min(len(unique_creators) * 2.5, 25)

        # 4. Watch completion (0-20 pts)
        if watches:
            completions = [
                a.metadata_json.get("watch_pct", 0.5)
                for a in watches
                if a.metadata_json
            ]
            avg_completion = sum(completions) / len(completions) if completions else 0.5
            completion_score = min(20, avg_completion * 25)
        else:
            completion_score = 10

        return comment_score + ratio_score + dist_score + completion_score

    def _natural_progression(
        self,
        actions: List[PhantomAction],
        profile_id: int,
        account_created_at: Optional[datetime] = None,
    ) -> float:
        """
        Measures organic growth — burst behavior = red flag.

        Sub-scores:
            - Account age factor (logarithmic, caps at 30 days)
            - Action volume ramp (monotonically increasing-ish)
            - Feature progression (watch → like → comment → post)
            - Natural gaps (some zero-activity days are expected)
        """
        now = datetime.now(timezone.utc)

        # 1. Age factor (0-25 pts) — logarithmic, maxes at ~30 days
        if account_created_at:
            age_days = max((now - account_created_at).days, 1)
        else:
            age_days = 1
        age_score = min(25, math.log(age_days + 1) / math.log(31) * 25)

        # 2. Action volume ramp (0-25 pts)
        if actions:
            weekly_volumes = self._get_weekly_volumes(actions)
            if len(weekly_volumes) >= 2:
                regressions = sum(
                    1 for i in range(1, len(weekly_volumes))
                    if weekly_volumes[i] < weekly_volumes[i - 1] * 0.5
                )
                ramp_score = max(0, 25 - regressions * 8)
            else:
                ramp_score = 15  # Not enough data
        else:
            ramp_score = 5

        # 3. Feature progression (0-25 pts)
        first_dates = {}
        for a in sorted(actions, key=lambda x: x.executed_at):
            if a.action_type not in first_dates:
                first_dates[a.action_type] = a.executed_at

        expected_order = ["watch", "like", "comment", "follow"]
        progression_valid = True
        for i in range(1, len(expected_order)):
            curr = first_dates.get(expected_order[i])
            prev = first_dates.get(expected_order[i - 1])
            if curr and prev and curr < prev:
                progression_valid = False
                break

        progression_score = 25 if progression_valid else 10

        # 4. Natural gaps (0-25 pts) — some zero days are healthy
        if actions:
            last_14_days = [(now - timedelta(days=i)).date() for i in range(14)]
            active_days = set(a.executed_at.date() for a in actions)
            gap_days = sum(1 for d in last_14_days if d not in active_days)

            if 1 <= gap_days <= 4:
                gap_score = 25  # Natural
            elif gap_days == 0:
                gap_score = 15  # Too perfect = suspicious
            else:
                gap_score = max(0, 25 - (gap_days - 4) * 4)
        else:
            gap_score = 5

        return age_score + ramp_score + progression_score + gap_score

    def _platform_adherence(self, actions: List[PhantomAction]) -> float:
        """
        Measures compliance with platform limits.

        Starts at 100, subtracts for:
            - Rate limit violations
            - CAPTCHA encounters
            - Content flags
            - Superhuman action velocity
        """
        score = 100.0

        violations = sum(1 for a in actions if a.error_code == "rate_limit")
        captchas = sum(1 for a in actions if a.error_code == "captcha")
        flags = sum(1 for a in actions if a.error_code == "content_flag")

        score -= violations * 10
        score -= captchas * 15
        score -= flags * 20

        # Action velocity check — look for rapid-fire sequences
        if len(actions) >= 2:
            sorted_actions = sorted(actions, key=lambda a: a.executed_at)
            min_gap_ms = float("inf")
            for i in range(1, len(sorted_actions)):
                gap = (sorted_actions[i].executed_at - sorted_actions[i - 1].executed_at).total_seconds() * 1000
                if gap > 0:
                    min_gap_ms = min(min_gap_ms, gap)

            if min_gap_ms < 1000:  # Less than 1 second between actions
                score -= 25
            elif min_gap_ms < 2000:
                score -= 10

        return max(0, score)

    def _session_health(self, profile_id: int) -> float:
        """
        Technical health of the session.

        This is a lightweight check — full validation happens in session_manager.
        Here we check:
            - Recent successful actions (proxy and browser working)
            - Error rate in last 24h
            - Overall success rate
        """
        recent_actions = self._get_actions(profile_id, window_days=1)

        if not recent_actions:
            return 30.0  # No activity in 24h — some concern but not critical

        # 1. Recent activity exists (0-40 pts)
        activity_score = 40.0 if len(recent_actions) >= 5 else len(recent_actions) * 8

        # 2. Error rate (0-30 pts)
        errors = sum(1 for a in recent_actions if not a.success)
        error_rate = errors / len(recent_actions)
        error_score = max(0, 30 * (1 - error_rate * 3))  # 33% error rate = 0 pts

        # 3. Success streak (0-30 pts)
        sorted_recent = sorted(recent_actions, key=lambda a: a.executed_at, reverse=True)
        streak = 0
        for a in sorted_recent:
            if a.success:
                streak += 1
            else:
                break
        streak_score = min(30, streak * 3)

        return activity_score + error_score + streak_score

    # ─── Data Access ─────────────────────────────────────────────────────

    def _get_actions(self, profile_id: int, window_days: int) -> List[PhantomAction]:
        """Fetch actions for profile within the time window."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        return (
            self.db.query(PhantomAction)
            .filter(
                PhantomAction.profile_id == profile_id,
                PhantomAction.executed_at >= cutoff,
            )
            .order_by(PhantomAction.executed_at.asc())
            .all()
        )

    def _get_weekly_volumes(self, actions: List[PhantomAction]) -> List[int]:
        """Group action counts by ISO week."""
        weekly: Dict[Tuple[int, int], int] = Counter()
        for a in actions:
            iso = a.executed_at.isocalendar()
            weekly[(iso[0], iso[1])] += 1
        return [count for _, count in sorted(weekly.items())]
