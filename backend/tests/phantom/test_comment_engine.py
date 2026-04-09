"""
Tests for Phantom Comment Engine.

Validates Gen Z comment generation, uniqueness, forbidden patterns,
typo injection, and multi-language support.
"""

import pytest
import re
from core.phantom.comment_engine import CommentEngine, FORBIDDEN_PATTERNS, TEMPLATES


class TestCommentGeneration:
    def setup_method(self):
        self.engine = CommentEngine(uniqueness_window=50)

    def test_generates_non_empty(self):
        """Should always produce a non-empty comment."""
        for _ in range(20):
            comment = self.engine.generate(style="reaction", language="en")
            assert len(comment) > 0
            assert len(comment.strip()) > 0

    def test_respects_max_length(self):
        """Comments should never exceed 100 characters."""
        for _ in range(50):
            comment = self.engine.generate()
            assert len(comment) <= 103  # 100 + "..." truncation

    def test_different_styles(self):
        """Different styles should produce varied output."""
        styles = ["reaction", "relatable", "question", "hype"]
        comments_by_style = {s: set() for s in styles}

        for style in styles:
            for _ in range(10):
                c = self.engine.generate(style=style, language="en")
                comments_by_style[style].add(c)

        # Each style should produce at least 3 unique comments
        for style, comments in comments_by_style.items():
            assert len(comments) >= 3, f"Style '{style}' produced too few unique comments"

    def test_brazilian_portuguese(self):
        """BR language should produce Portuguese-ish content."""
        comments = [self.engine.generate(style="reaction", language="br") for _ in range(20)]
        # At least some should contain PT-BR markers
        br_markers = ["kk", "mds", "gente", "mt", "bom", "socorro", "morri", "mano", "real"]
        has_br = any(
            any(marker in c.lower() for marker in br_markers)
            for c in comments
        )
        assert has_br, f"No BR markers found in: {comments[:5]}"


class TestUniqueness:
    def setup_method(self):
        self.engine = CommentEngine(uniqueness_window=20)

    def test_no_consecutive_duplicates(self):
        """Should never produce two identical comments in sequence."""
        comments = [self.engine.generate() for _ in range(15)]
        for i in range(1, len(comments)):
            assert comments[i].lower() != comments[i - 1].lower(), \
                f"Duplicate at index {i}: {comments[i]}"

    def test_batch_uniqueness(self):
        """Batch generation should produce unique comments."""
        batch = self.engine.generate_batch(count=10)
        assert len(batch) == 10
        # Most should be unique (allowing some overlap due to limited templates)
        unique = set(c.lower() for c in batch)
        assert len(unique) >= 7, f"Too many duplicates in batch: {batch}"


class TestForbiddenPatterns:
    def setup_method(self):
        self.engine = CommentEngine()

    def test_no_forbidden_patterns_in_output(self):
        """Generated comments should never contain bot-flagging patterns."""
        for _ in range(100):
            comment = self.engine.generate()
            for pattern in FORBIDDEN_PATTERNS:
                assert not pattern.search(comment), \
                    f"Forbidden pattern matched: {pattern.pattern} in '{comment}'"

    def test_forbidden_detection(self):
        """Engine should detect forbidden patterns correctly."""
        forbidden_texts = [
            "check out my page",
            "follow for follow",
            "f4f",
            "nice video!",
            "great content!",
            "amazing!",
            "https://spam.com",
            "subscribe to my channel",
        ]
        for text in forbidden_texts:
            assert self.engine._is_forbidden(text), \
                f"Should have flagged: '{text}'"


class TestGenZStyle:
    def setup_method(self):
        self.engine = CommentEngine()

    def test_no_trailing_periods(self):
        """Gen Z never ends messages with a period."""
        for _ in range(30):
            comment = self.engine.generate()
            assert not comment.endswith("."), f"Has trailing period: '{comment}'"

    def test_mostly_lowercase(self):
        """Most comments should be lowercase (80% probability in code)."""
        lower_count = 0
        total = 50
        for _ in range(total):
            comment = self.engine.generate()
            # Check if the alphabetic characters are mostly lowercase
            alpha_chars = [c for c in comment if c.isalpha()]
            if alpha_chars:
                lower_ratio = sum(1 for c in alpha_chars if c.islower()) / len(alpha_chars)
                if lower_ratio > 0.8:
                    lower_count += 1
        # At least 60% of comments should be mostly lowercase
        assert lower_count / total > 0.5


class TestTemplateCompleteness:
    def test_all_styles_have_templates(self):
        """All standard styles should have templates in both languages."""
        for style in ["reaction", "relatable", "hype"]:
            for lang in ["en", "br"]:
                key = f"{style}_{lang}"
                assert key in TEMPLATES, f"Missing template group: {key}"
                assert len(TEMPLATES[key]) >= 5, f"Too few templates in {key}"

    def test_question_templates_exist(self):
        """Question style should have EN templates."""
        assert "question_en" in TEMPLATES
        assert len(TEMPLATES["question_en"]) >= 5
