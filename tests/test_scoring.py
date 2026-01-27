"""Tests for scoring and threshold logic."""

import pytest

from pasteofshame.core.detector import Detector
from pasteofshame.core.rules import RulePack
from pasteofshame.core.scoring import ScoringEngine


class TestScoring:
    """Test scoring and threshold logic."""

    def test_threshold_warning(self) -> None:
        """Test that warnings are triggered above threshold."""
        rule_pack = RulePack.builtin()

        # Low threshold
        low_threshold = ScoringEngine(threshold=5)
        detector_low = Detector(rule_pack=rule_pack, scoring_engine=low_threshold)
        result = detector_low.scan("Certainly!")
        assert result.is_warning

        # High threshold
        high_threshold = ScoringEngine(threshold=100)
        detector_high = Detector(rule_pack=rule_pack, scoring_engine=high_threshold)
        result = detector_high.scan("Certainly!")
        assert not result.is_warning

    def test_high_severity_always_warns(self) -> None:
        """Test that high severity matches always trigger warnings."""
        rule_pack = RulePack.builtin()
        scoring_engine = ScoringEngine(threshold=1000)  # Very high threshold
        detector = Detector(rule_pack=rule_pack, scoring_engine=scoring_engine)

        text = "As an AI language model, I cannot help."
        result = detector.scan(text)

        # Even with high threshold, high severity should warn
        assert result.has_high_severity()
        assert result.is_warning

    def test_score_accumulation(self) -> None:
        """Test that scores accumulate from multiple matches."""
        rule_pack = RulePack.builtin()
        scoring_engine = ScoringEngine(threshold=20)
        detector = Detector(rule_pack=rule_pack, scoring_engine=scoring_engine)

        # Multiple low-weight patterns
        text = "Certainly! Below is the code. I hope this helps!"
        result = detector.scan(text)

        # Should accumulate score from multiple matches
        assert result.total_score >= 20
        assert len(result.matches) >= 3

    def test_top_matches(self) -> None:
        """Test retrieving top matches by weight."""
        rule_pack = RulePack.builtin()
        detector = Detector(rule_pack=rule_pack)

        text = "As an AI language model, certainly, I hope this helps."
        result = detector.scan(text)

        top_3 = result.top_matches(3)
        assert len(top_3) <= 3

        # Top matches should be sorted by weight (descending)
        if len(top_3) >= 2:
            assert top_3[0].rule.weight >= top_3[1].rule.weight
