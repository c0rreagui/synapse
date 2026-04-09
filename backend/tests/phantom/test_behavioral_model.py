"""
Tests for Phantom Behavioral Model.

Validates session planning, action selection, and timing logic.
"""

import pytest
from unittest.mock import MagicMock
from core.phantom.behavioral_model import BehavioralModel, PlannedAction, CONSUMPTION_WINDOWS
from core.phantom.personas import PERSONAS, get_persona


class TestSessionPlanning:
    def setup_method(self):
        self.model = BehavioralModel()
        self.persona = get_persona("meme_agent")

    def test_plan_returns_list(self):
        """plan_session should always return a list."""
        result = self.model.plan_session(
            persona=self.persona,
            current_score=30,
            hour=20,  # Evening — peak time
            weekday=5,  # Saturday
        )
        assert isinstance(result, list)

    def test_plan_respects_daily_cap(self):
        """Should return empty list when daily cap is reached."""
        result = self.model.plan_session(
            persona=self.persona,
            current_score=50,
            hour=20,
            weekday=1,
            daily_action_count=150,  # At the cap
        )
        assert result == []

    def test_plan_always_starts_with_consumption(self):
        """First action should be scroll/consumption (priority 0)."""
        # Force a high-probability time slot for consistency
        for _ in range(20):
            result = self.model.plan_session(
                persona=self.persona,
                current_score=50,
                hour=20,
                weekday=5,
            )
            if result:
                assert result[0].action_type == "scroll" or result[0].priority == 0
                break

    def test_plan_includes_social_for_reactors(self):
        """Reactor personas should have higher social action probability."""
        meme_persona = get_persona("meme_agent")
        assert meme_persona.engagement_style == "reactor"
        assert meme_persona.comment_probability > 0.05

    def test_plan_sorted_by_priority(self):
        """Actions should be sorted by priority (consumption first)."""
        for _ in range(10):
            result = self.model.plan_session(
                persona=self.persona,
                current_score=50,
                hour=21,
                weekday=6,
            )
            if len(result) > 1:
                priorities = [a.priority for a in result]
                assert priorities == sorted(priorities), \
                    f"Actions not sorted by priority: {priorities}"
                break


class TestActionGating:
    def setup_method(self):
        self.model = BehavioralModel()
        self.persona = get_persona("meme_agent")

    def test_low_trust_only_consumption(self):
        """Score < 11 should only produce scroll/watch actions."""
        for _ in range(10):
            result = self.model.plan_session(
                persona=self.persona,
                current_score=5,  # Very low trust
                hour=21,
                weekday=5,
            )
            for action in result:
                assert action.required_trust <= 5 or action.action_type in ("scroll", "watch"), \
                    f"Gated action {action.action_type} (gate={action.required_trust}) at score 5"


class TestGapDay:
    def setup_method(self):
        self.model = BehavioralModel()
        self.persona = get_persona("aesthetic_curator")

    def test_gap_day_probability_increases_with_streak(self):
        """Longer active streaks should have higher gap day probability."""
        # This is probabilistic — run enough iterations
        gaps_at_3 = sum(self.model.should_skip_day(self.persona, 3) for _ in range(1000))
        gaps_at_10 = sum(self.model.should_skip_day(self.persona, 10) for _ in range(1000))

        # 10 consecutive days should produce more gaps than 3
        assert gaps_at_10 > gaps_at_3


class TestTimingLogic:
    def setup_method(self):
        self.model = BehavioralModel()

    def test_evening_sessions_longer(self):
        """Evening sessions should tend to be longer than morning."""
        persona = get_persona("meme_agent")
        evening_durations = [self.model._get_session_duration(persona, 21) for _ in range(100)]
        morning_durations = [self.model._get_session_duration(persona, 7) for _ in range(100)]

        avg_evening = sum(evening_durations) / len(evening_durations)
        avg_morning = sum(morning_durations) / len(morning_durations)

        assert avg_evening > avg_morning, \
            f"Evening ({avg_evening:.1f}min) should be longer than morning ({avg_morning:.1f}min)"


class TestPersonaLibrary:
    def test_all_personas_valid(self):
        """All personas should have valid field values."""
        for key, persona in PERSONAS.items():
            assert persona.name, f"Persona {key} has no name"
            assert len(persona.primary_niches) > 0, f"Persona {key} has no niches"
            assert 0 < persona.like_probability <= 1.0
            assert 0 < persona.comment_probability <= 1.0
            assert persona.avg_daily_sessions > 0
            assert persona.avg_session_minutes > 0
            assert persona.weekend_boost > 0

    def test_content_ratios_sum_to_one(self):
        """Content ratios should approximately sum to 1.0."""
        for key, persona in PERSONAS.items():
            total = sum(persona.content_ratio.values())
            assert abs(total - 1.0) < 0.05, \
                f"Persona {key} content_ratio sums to {total}, expected ~1.0"

    def test_get_persona_returns_none_for_unknown(self):
        assert get_persona("nonexistent") is None

    def test_get_persona_returns_valid(self):
        p = get_persona("meme_agent")
        assert p is not None
        assert p.name == "Meme Chaos Agent"
