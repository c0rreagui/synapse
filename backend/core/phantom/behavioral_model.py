"""
Phantom Behavioral Model — Session planning engine.

Decides WHAT actions to execute and WHEN based on:
    - Current persona traits (interests, timing, engagement style)
    - Current trust score (action gates)
    - Time of day and day of week
    - Recent action history (avoid repetition, enforce cooldowns)

This module is the "brain" of Phantom — it connects the persona model
to the action executors, producing a sequenced action plan for each session.
"""

import random
import math
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional

from core.phantom.personas import GenZPersona
from core.phantom.trust_score import is_action_allowed
from core.phantom.safety import SAFETY

logger = logging.getLogger("PhantomBehavioralModel")


# ─── Action Plan ─────────────────────────────────────────────────────────────

@dataclass
class PlannedAction:
    """A single action to execute in a session."""
    action_type: str        # "scroll", "watch", "like", "comment", "follow", "search", "explore"
    subtype: Optional[str] = None   # "fyp_scroll", "niche_search", etc.
    required_trust: float = 0.0
    params: Dict = field(default_factory=dict)
    priority: int = 0       # Lower = execute first

    def __repr__(self):
        return f"<Action {self.action_type}:{self.subtype or 'default'} gate={self.required_trust}>"


# ─── Consumption Windows ─────────────────────────────────────────────────────

CONSUMPTION_WINDOWS = {
    "morning_scroll":   {"hours": (7, 9),   "prob": 0.25, "duration_range": (5, 15)},
    "lunch_break":      {"hours": (12, 14), "prob": 0.40, "duration_range": (10, 30)},
    "afternoon_fill":   {"hours": (15, 17), "prob": 0.15, "duration_range": (5, 20)},
    "evening_deep":     {"hours": (19, 23), "prob": 0.70, "duration_range": (20, 60)},
    "late_night":       {"hours": (23, 1),  "prob": 0.30, "duration_range": (10, 40)},
}


# ─── Session Planner ─────────────────────────────────────────────────────────

class BehavioralModel:
    """
    Plans action sequences for a single Phantom session.

    Each session simulates a realistic "pick up phone, scroll TikTok, put down" cycle.
    The model adapts based on persona traits, current trust level, and context.
    """

    def plan_session(
        self,
        persona: GenZPersona,
        current_score: float,
        hour: int,
        weekday: int,  # 0=Monday, 6=Sunday
        daily_action_count: int = 0,
    ) -> List[PlannedAction]:
        """
        Plan a full session of actions.

        Args:
            persona: The profile's assigned persona.
            current_score: Current trust score (determines action gates).
            hour: Current hour (0-23).
            weekday: Day of week (0=Mon, 6=Sun).
            daily_action_count: Actions already executed today (for cap enforcement).

        Returns:
            Ordered list of PlannedActions to execute sequentially.
        """
        # Check daily cap
        remaining_cap = SAFETY.max_actions_per_day - daily_action_count
        if remaining_cap <= 0:
            logger.info("[BEHAVIORAL] Daily action cap reached, skipping session")
            return []

        # Determine session viability
        if not self._should_have_session(persona, hour, weekday):
            logger.debug(f"[BEHAVIORAL] Low probability for session at hour={hour}, weekday={weekday}")
            return []

        # Determine session duration
        session_minutes = self._get_session_duration(persona, hour)
        logger.info(f"[BEHAVIORAL] Planning {session_minutes:.0f}min session at hour={hour}")

        # Build action sequence
        actions: List[PlannedAction] = []

        # Always start with consumption (scroll + watch) — this is the core
        scroll_actions = self._plan_consumption(persona, session_minutes, current_score)
        actions.extend(scroll_actions)

        # Social actions (interspersed based on engagement style)
        if random.random() < persona.content_ratio.get("social", 0.15):
            social_actions = self._plan_social(persona, current_score, len(scroll_actions))
            actions.extend(social_actions)

        # Exploration actions
        if random.random() < persona.content_ratio.get("explore", 0.10):
            explore_actions = self._plan_exploration(persona, current_score)
            actions.extend(explore_actions)

        # Enforce remaining cap
        if len(actions) > remaining_cap:
            actions = actions[:remaining_cap]

        # Sort by priority (consumption first, then social, then explore)
        actions.sort(key=lambda a: a.priority)

        logger.info(f"[BEHAVIORAL] Session planned: {len(actions)} actions "
                     f"({', '.join(a.action_type for a in actions[:5])}...)")
        return actions

    # ─── Session Viability ───────────────────────────────────────────────

    def _should_have_session(self, persona: GenZPersona, hour: int, weekday: int) -> bool:
        """
        Determine if a session should happen now based on persona traits.

        Uses peak_hours and weekend_boost to calculate probability.
        """
        # Base probability from time window
        base_prob = 0.10  # Default low
        for window_name, window in CONSUMPTION_WINDOWS.items():
            h_start, h_end = window["hours"]
            if h_start <= h_end:
                in_window = h_start <= hour < h_end
            else:
                in_window = hour >= h_start or hour < h_end  # Wraps past midnight
            if in_window:
                base_prob = max(base_prob, window["prob"])

        # Boost if current hour is in persona's peak hours
        if hour in persona.peak_hours:
            base_prob = min(1.0, base_prob * 1.5)

        # Weekend boost
        is_weekend = weekday >= 5
        if is_weekend:
            base_prob = min(1.0, base_prob * persona.weekend_boost)

        return random.random() < base_prob

    def _get_session_duration(self, persona: GenZPersona, hour: int) -> float:
        """
        Calculate session duration in minutes.

        Uses Gaussian distribution centered on persona's avg with time-of-day modulation.
        Evening sessions tend to be longer.
        """
        base = persona.avg_session_minutes

        # Evening sessions are 20-50% longer
        if 19 <= hour <= 23:
            base *= random.uniform(1.2, 1.5)
        # Morning sessions are shorter
        elif 6 <= hour <= 9:
            base *= random.uniform(0.6, 0.9)

        # Gaussian jitter (±30%)
        duration = max(3, random.gauss(base, base * 0.3))
        return duration

    # ─── Action Planners ─────────────────────────────────────────────────

    def _plan_consumption(
        self,
        persona: GenZPersona,
        session_minutes: float,
        current_score: float,
    ) -> List[PlannedAction]:
        """
        Plan consumption actions for the session.

        A typical session: scroll FYP → watch videos → occasionally interact.
        """
        actions = []

        # FYP scroll session
        actions.append(PlannedAction(
            action_type="scroll",
            subtype="fyp_scroll",
            required_trust=0,
            params={
                "duration_minutes": session_minutes * persona.content_ratio.get("consume", 0.75),
                "like_probability": persona.like_probability,
                "save_probability": persona.save_probability,
            },
            priority=0,
        ))

        # Estimated video count (avg TikTok video is ~15-30 seconds)
        estimated_videos = int(session_minutes * 60 / random.uniform(12, 25))

        # Individual watch actions (tracked separately for metrics)
        for i in range(min(estimated_videos, 30)):  # Cap at 30 per session
            niche = random.choice(
                persona.primary_niches if random.random() < 0.7
                else persona.secondary_niches or persona.primary_niches
            )
            actions.append(PlannedAction(
                action_type="watch",
                subtype=f"{'niche' if random.random() < 0.6 else 'fyp'}_watch",
                required_trust=0,
                params={
                    "niche": niche,
                    "skip_probability": 0.38,  # 38% quick skip (bimodal distribution)
                },
                priority=1,
            ))

        # Saves (based on save probability)
        num_saves = sum(1 for _ in range(estimated_videos) if random.random() < persona.save_probability)
        for _ in range(num_saves):
            if is_action_allowed("save", current_score):
                actions.append(PlannedAction(
                    action_type="save",
                    subtype="bookmark",
                    required_trust=11,
                    priority=2,
                ))

        return actions

    def _plan_social(
        self,
        persona: GenZPersona,
        current_score: float,
        watch_count: int,
    ) -> List[PlannedAction]:
        """Plan social interaction actions based on persona engagement style."""
        actions = []

        # Comments (based on comment probability relative to watches)
        if is_action_allowed("comment", current_score):
            num_comments = sum(
                1 for _ in range(watch_count)
                if random.random() < persona.comment_probability
            )
            num_comments = min(num_comments, SAFETY.max_comments_per_day)

            for _ in range(num_comments):
                actions.append(PlannedAction(
                    action_type="comment",
                    subtype=persona.comment_style,
                    required_trust=21,
                    params={"style": persona.comment_style},
                    priority=3,
                ))

        # Follows
        if is_action_allowed("follow", current_score):
            num_follows = random.randint(0, min(3, persona.max_follows_per_day))
            for _ in range(num_follows):
                actions.append(PlannedAction(
                    action_type="follow",
                    subtype="organic_follow",
                    required_trust=21,
                    priority=4,
                ))

        return actions

    def _plan_exploration(
        self,
        persona: GenZPersona,
        current_score: float,
    ) -> List[PlannedAction]:
        """Plan exploration actions (search, browse sounds, profile visits)."""
        actions = []

        # Search (always allowed but low priority)
        if is_action_allowed("search", current_score) and random.random() < 0.5:
            search_niche = random.choice(persona.primary_niches + persona.secondary_niches)
            actions.append(PlannedAction(
                action_type="search",
                subtype="niche_search",
                required_trust=11,
                params={"query_type": "hashtag", "niche": search_niche},
                priority=5,
            ))

        # Explore page
        if is_action_allowed("explore", current_score) and random.random() < 0.4:
            actions.append(PlannedAction(
                action_type="explore",
                subtype="discover_page",
                required_trust=11,
                priority=5,
            ))

        # Tab navigation (neutral but absence is a red flag)
        if random.random() < 0.6:
            actions.append(PlannedAction(
                action_type="explore",
                subtype="tab_navigation",
                required_trust=0,
                params={"tabs": random.choice([
                    ["fyp", "following"],
                    ["following", "fyp"],
                    ["fyp", "discover"],
                ])},
                priority=6,
            ))

        # Notification check
        if random.random() < 0.5:
            actions.append(PlannedAction(
                action_type="explore",
                subtype="notification_check",
                required_trust=0,
                priority=6,
            ))

        return actions

    def should_skip_day(self, persona: GenZPersona, consecutive_active_days: int) -> bool:
        """
        Determine if today should be a "gap day" (no activity).

        Real users don't use the app every single day. Having some natural gaps
        actually improves the trust score's Natural Progression dimension.
        """
        # After 10+ consecutive days, 35% chance of a gap
        if consecutive_active_days >= 10:
            return random.random() < 0.35
        # After 5-9 consecutive days, 20% chance
        if consecutive_active_days >= 5:
            return random.random() < 0.20
        # Default: 5% chance (rare but possible)
        return random.random() < 0.05


# ─── Singleton ───────────────────────────────────────────────────────────────

behavioral_model = BehavioralModel()
