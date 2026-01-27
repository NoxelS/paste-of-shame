"""Tests for the detection engine."""

import pytest

from pasteofshame.core.detector import Detector
from pasteofshame.core.rules import RulePack
from pasteofshame.core.scoring import ScoringEngine
from tests.fixtures import NEGATIVE_EXAMPLES, POSITIVE_EXAMPLES


class TestDetector:
    """Test the main detector."""

    @pytest.fixture
    def detector(self) -> Detector:
        """Create a detector with builtin rules."""
        rule_pack = RulePack.builtin()
        scoring_engine = ScoringEngine(threshold=20)
        return Detector(rule_pack=rule_pack, scoring_engine=scoring_engine)

    def test_positive_examples(self, detector: Detector) -> None:
        """Test that positive examples are detected."""
        for example in POSITIVE_EXAMPLES:
            result = detector.scan(example)
            assert len(result.matches) > 0, f"Expected matches in: {example}"
            assert result.total_score > 0, f"Expected non-zero score for: {example}"

    def test_negative_examples(self, detector: Detector) -> None:
        """Test that negative examples don't trigger false positives."""
        for example in NEGATIVE_EXAMPLES:
            result = detector.scan(example)
            # Should have no matches or very low score
            assert result.total_score < 20, f"Unexpected high score for: {example}"

    def test_high_severity_match(self, detector: Detector) -> None:
        """Test that high severity matches trigger warnings."""
        text = "As an AI language model, I must inform you..."
        result = detector.scan(text)
        assert result.has_high_severity()
        assert result.is_warning

    def test_phrase_match_case_insensitive(self, detector: Detector) -> None:
        """Test that phrase matching is case-insensitive."""
        text1 = "Certainly! Here you go."
        text2 = "CERTAINLY! Here you go."
        text3 = "certainly! Here you go."

        result1 = detector.scan(text1)
        result2 = detector.scan(text2)
        result3 = detector.scan(text3)

        assert len(result1.matches) > 0
        assert len(result2.matches) > 0
        assert len(result3.matches) > 0

    def test_multiple_matches_same_rule(self, detector: Detector) -> None:
        """Test that multiple occurrences of the same pattern are counted."""
        text = "Certainly! I will help. Certainly, here it is. Certainly!"
        result = detector.scan(text)

        # Find the "certainly" rule match
        certainly_match = next((m for m in result.matches if "certainly" in m.rule.pattern.lower()), None)
        assert certainly_match is not None
        assert len(certainly_match.spans) >= 3  # Should find 3 occurrences

    def test_excerpt_length_limit(self, detector: Detector) -> None:
        """Test that excerpts are truncated to max length."""
        long_text = "As an AI language model, " + "x" * 100
        result = detector.scan(long_text, max_excerpt_length=50)

        assert len(result.matches) > 0
        for match in result.matches:
            for excerpt in match.excerpts:
                assert len(excerpt) <= 53  # 50 + "..."

    def test_empty_text(self, detector: Detector) -> None:
        """Test scanning empty text."""
        result = detector.scan("")
        assert len(result.matches) == 0
        assert result.total_score == 0
        assert not result.is_warning
