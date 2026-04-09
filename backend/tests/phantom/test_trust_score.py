"""
Tests for Phantom Trust Score Calculator.

Validates all 5 scoring dimensions and the composite score logic.
Uses deterministic test data — no database or browser required.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from core.phantom.trust_score import (
    TrustScoreCalculator,
    _coefficient_of_variation,
    _cosine_similarity,
    _get_status,
    is_action_allowed,
    WEIGHTS,
    STATUS_THRESHOLDS,
    ACTION_GATES,
)
from core.phantom.models import PhantomAction


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_action(
    action_type: str = "watch",
    subtype: str = None,
    success: bool = True,
    hours_ago: float = 1,
    niche: str = None,
    error_code: str = None,
    metadata: dict = None,
    target_handle: str = None,
):
    """Create a mock PhantomAction for testing."""
    action = MagicMock(spec=PhantomAction)
    action.action_type = action_type
    action.action_subtype = subtype
    action.success = success
    action.executed_at = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    action.content_niche = niche
    action.error_code = error_code
    action.metadata_json = metadata or {}
    action.target_user_handle = target_handle
    return action


def _make_diverse_actions(count: int = 50, days: int = 7) -> list:
    """Create a realistic mix of actions across multiple days."""
    actions = []
    types = ["scroll", "watch", "like", "comment", "follow", "search", "explore"]
    handles = [f"@user_{i}" for i in range(20)]

    for i in range(count):
        hours_ago = (i / count) * days * 24
        action = _make_action(
            action_type=types[i % len(types)],
            hours_ago=hours_ago,
            niche="comedy" if i % 3 == 0 else "fashion",
            target_handle=handles[i % len(handles)],
            metadata={"text": f"unique comment {i}", "watch_pct": 0.85} if types[i % len(types)] == "comment" else {"watch_pct": 0.85},
        )
        # Vary the hour to simulate realistic temporal distribution
        action.executed_at = action.executed_at.replace(hour=(10 + i) % 24)
        actions.append(action)

    return actions


# ─── Unit Tests: Helper Functions ────────────────────────────────────────────

class TestHelperFunctions:
    def test_cv_constant_values(self):
        """Constant values should have CV = 0."""
        assert _coefficient_of_variation([5, 5, 5, 5, 5]) == 0.0

    def test_cv_empty(self):
        """Empty list should return 1.0 (maximum uncertainty)."""
        assert _coefficient_of_variation([]) == 1.0

    def test_cv_single_value(self):
        """Single value should return 1.0."""
        assert _coefficient_of_variation([5]) == 1.0

    def test_cv_moderate_variation(self):
        """Moderate variation should produce value between 0 and 1."""
        cv = _coefficient_of_variation([10, 12, 8, 11, 9])
        assert 0 < cv < 1

    def test_cosine_similarity_identical(self):
        """Identical distributions should have similarity = 1."""
        vec = {0: 1, 1: 2, 2: 3}
        assert abs(_cosine_similarity(vec, vec) - 1.0) < 0.001

    def test_cosine_similarity_orthogonal(self):
        """Non-overlapping distributions should have similarity = 0."""
        a = {0: 1, 1: 2}
        b = {3: 1, 4: 2}
        assert _cosine_similarity(a, b) == 0.0

    def test_cosine_similarity_empty(self):
        """Empty vectors should return 0."""
        assert _cosine_similarity({}, {0: 1}) == 0.0

    def test_get_status_boundaries(self):
        """Status should map correctly at boundaries."""
        assert _get_status(0) == "nascent"
        assert _get_status(10) == "nascent"
        assert _get_status(11) == "warming"
        assert _get_status(20) == "warming"
        assert _get_status(21) == "building"
        assert _get_status(40) == "building"
        assert _get_status(41) == "established"
        assert _get_status(60) == "established"
        assert _get_status(61) == "trusted"
        assert _get_status(80) == "trusted"
        assert _get_status(81) == "organic"
        assert _get_status(100) == "organic"

    def test_action_gates(self):
        """Action gates should correctly block/allow based on score."""
        assert is_action_allowed("scroll", 0) is True
        assert is_action_allowed("watch", 0) is True
        assert is_action_allowed("like", 5) is False
        assert is_action_allowed("like", 11) is True
        assert is_action_allowed("comment", 20) is False
        assert is_action_allowed("comment", 21) is True
        assert is_action_allowed("post", 40) is False
        assert is_action_allowed("post", 41) is True
        assert is_action_allowed("duet", 60) is False
        assert is_action_allowed("duet", 61) is True


# ─── Unit Tests: Dimension Calculators ───────────────────────────────────────

class TestBehavioralConsistency:
    def setup_method(self):
        self.db = MagicMock()
        self.calculator = TrustScoreCalculator(self.db)

    def test_empty_actions_returns_zero(self):
        score = self.calculator._behavioral_consistency([], 7)
        assert score == 0.0

    def test_diverse_actions_score_higher(self):
        """Actions with diverse types should score higher on diversity."""
        diverse = _make_diverse_actions(50)
        score = self.calculator._behavioral_consistency(diverse, 7)
        assert score > 30  # Should score well with 7 different action types


class TestEngagementQuality:
    def setup_method(self):
        self.db = MagicMock()
        self.calculator = TrustScoreCalculator(self.db)

    def test_empty_returns_zero(self):
        score = self.calculator._engagement_quality([], 1)
        assert score == 0.0

    def test_healthy_ratio_scores_well(self):
        """15% like-to-watch ratio should score well."""
        actions = []
        # 100 watches
        for i in range(100):
            actions.append(_make_action("watch", hours_ago=i * 0.1, metadata={"watch_pct": 0.85}))
        # 15 likes (15% ratio — within optimal range)
        for i in range(15):
            actions.append(_make_action("like", hours_ago=i * 0.2))

        score = self.calculator._engagement_quality(actions, 1)
        assert score > 50  # Should score well

    def test_spam_like_ratio_scores_poorly(self):
        """50% like ratio (spam-like) should score lower."""
        actions = []
        for i in range(20):
            actions.append(_make_action("watch", hours_ago=i * 0.1))
        for i in range(10):
            actions.append(_make_action("like", hours_ago=i * 0.2))

        score_spam = self.calculator._engagement_quality(actions, 1)

        actions2 = []
        for i in range(100):
            actions2.append(_make_action("watch", hours_ago=i * 0.1))
        for i in range(15):
            actions2.append(_make_action("like", hours_ago=i * 0.2))

        score_healthy = self.calculator._engagement_quality(actions2, 1)
        assert score_healthy >= score_spam


class TestNaturalProgression:
    def setup_method(self):
        self.db = MagicMock()
        self.calculator = TrustScoreCalculator(self.db)

    def test_correct_feature_order_scores_well(self):
        """Watch → Like → Comment progression should score high."""
        actions = [
            _make_action("watch", hours_ago=72),    # 3 days ago
            _make_action("like", hours_ago=48),      # 2 days ago
            _make_action("comment", hours_ago=24),   # 1 day ago
        ]
        score = self.calculator._natural_progression(
            actions, 1,
            account_created_at=datetime.now(timezone.utc) - timedelta(days=10),
        )
        assert score > 40  # Feature order is correct

    def test_inverted_order_scores_lower(self):
        """Comment before Watch is suspicious."""
        actions = [
            _make_action("comment", hours_ago=72),   # Comment first — wrong
            _make_action("watch", hours_ago=48),
        ]
        score = self.calculator._natural_progression(
            actions, 1,
            account_created_at=datetime.now(timezone.utc) - timedelta(days=2),
        )
        # Should still get some points (age, gaps) but lower progression
        assert score < 80


class TestPlatformAdherence:
    def setup_method(self):
        self.db = MagicMock()
        self.calculator = TrustScoreCalculator(self.db)

    def test_clean_actions_score_100(self):
        """No violations should score 100."""
        actions = [_make_action("watch", hours_ago=i) for i in range(10)]
        score = self.calculator._platform_adherence(actions)
        assert score == 100.0

    def test_captcha_reduces_score(self):
        """CAPTCHA encounters should reduce score significantly."""
        # Space actions far apart to avoid velocity penalty
        actions = [_make_action("watch", hours_ago=i * 2) for i in range(5)]
        actions.append(_make_action("watch", error_code="captcha", success=False, hours_ago=3))
        score = self.calculator._platform_adherence(actions)
        assert score < 100  # Should be penalized
        assert score <= 85  # At least -15 from captcha

    def test_rapid_fire_reduces_score(self):
        """Actions less than 1 second apart should be penalized."""
        now = datetime.now(timezone.utc)
        actions = []
        for i in range(5):
            a = _make_action("like", hours_ago=0)
            a.executed_at = now - timedelta(milliseconds=i * 500)  # 500ms apart
            actions.append(a)
        score = self.calculator._platform_adherence(actions)
        assert score < 100  # Should be penalized


class TestSessionHealth:
    def setup_method(self):
        self.db = MagicMock()
        self.calculator = TrustScoreCalculator(self.db)

    def test_no_recent_activity(self):
        """No recent activity should return a moderate score (concern but not critical)."""
        self.calculator._get_actions = MagicMock(return_value=[])
        score = self.calculator._session_health(1)
        assert score == 30.0


# ─── Integration Test: Composite Score ───────────────────────────────────────

class TestCompositeScore:
    def setup_method(self):
        self.db = MagicMock()
        self.calculator = TrustScoreCalculator(self.db)

    def test_weights_sum_to_one(self):
        """Dimension weights must sum to 1.0."""
        assert abs(sum(WEIGHTS.values()) - 1.0) < 0.001

    def test_full_compute_returns_all_fields(self):
        """compute() should return all required fields."""
        actions = _make_diverse_actions(30)
        self.calculator._get_actions = MagicMock(return_value=actions)

        result = self.calculator.compute(profile_id=1)

        assert "behavioral_consistency" in result
        assert "engagement_quality" in result
        assert "natural_progression" in result
        assert "platform_adherence" in result
        assert "session_health" in result
        assert "total_score" in result
        assert "status" in result
        assert "actions_counted" in result
        assert "window_days" in result

    def test_score_bounded_0_100(self):
        """Total score must always be between 0 and 100."""
        for _ in range(10):
            actions = _make_diverse_actions(20)
            self.calculator._get_actions = MagicMock(return_value=actions)
            result = self.calculator.compute(profile_id=1)
            assert 0 <= result["total_score"] <= 100
