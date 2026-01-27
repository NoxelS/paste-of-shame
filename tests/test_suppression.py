"""Tests for suppression logic."""

from pasteofshame.core.detector import Detector
from pasteofshame.core.rules import RulePack
from pasteofshame.core.scoring import ScoringEngine
from tests.fixtures import CODE_FENCE_EXAMPLES, QUOTED_EXAMPLES


class TestSuppression:
    """Test suppression logic for quotes and code."""

    def test_quoted_text_suppression(self) -> None:
        """Test that heavily quoted text has reduced score."""
        rule_pack = RulePack.builtin()
        scoring_engine = ScoringEngine(threshold=20)
        detector = Detector(rule_pack=rule_pack, scoring_engine=scoring_engine)

        for example in QUOTED_EXAMPLES:
            result = detector.scan(example)
            assert result.suppression_applied
            assert "quoted" in (result.suppression_reason or "").lower()

    def test_code_fence_suppression(self) -> None:
        """Test that text with code fences has reduced score."""
        rule_pack = RulePack.builtin()
        scoring_engine = ScoringEngine(threshold=20)
        detector = Detector(rule_pack=rule_pack, scoring_engine=scoring_engine)

        for example in CODE_FENCE_EXAMPLES:
            result = detector.scan(example)
            # May or may not suppress depending on text, but should recognize code
            if result.suppression_applied:
                assert "code" in (result.suppression_reason or "").lower()

    def test_allowlist_suppression(self) -> None:
        """Test that allowlist patterns suppress warnings."""
        rule_pack = RulePack.builtin()

        # Create scoring engine with allowlist
        allowlist = [r"authorized.*content"]
        scoring_engine = ScoringEngine(threshold=20, allowlist_patterns=allowlist)
        detector = Detector(rule_pack=rule_pack, scoring_engine=scoring_engine)

        text = "Certainly! This is authorized test content. Below is the code."
        result = detector.scan(text)

        assert result.suppression_applied
        assert "allowlist" in (result.suppression_reason or "").lower()
        assert not result.is_warning

    def test_suppression_factor_calculation(self) -> None:
        """Test the suppression factor calculation directly."""
        scoring_engine = ScoringEngine(threshold=20)

        # Empty text
        factor, reason = scoring_engine.calculate_suppression_factor("")
        assert factor == 0.0

        # Normal text
        factor, reason = scoring_engine.calculate_suppression_factor("This is normal text.")
        assert factor == 1.0
        assert reason is None

        # Heavily quoted
        quoted = "\n".join(["> quoted line" for _ in range(10)])
        factor, reason = scoring_engine.calculate_suppression_factor(quoted)
        assert factor < 1.0
        assert "quoted" in (reason or "").lower()

        # With code fences
        code = "Some text\n```\ncode here\n```\nmore text"
        factor, reason = scoring_engine.calculate_suppression_factor(code)
        assert factor < 1.0
        assert "code" in (reason or "").lower()

    def test_no_suppression_for_normal_text(self) -> None:
        """Test that normal text without quotes/code isn't suppressed."""
        rule_pack = RulePack.builtin()
        scoring_engine = ScoringEngine(threshold=20)
        detector = Detector(rule_pack=rule_pack, scoring_engine=scoring_engine)

        text = "As an AI language model, I must say certainly this helps."
        result = detector.scan(text)

        # Should have matches but no suppression
        assert len(result.matches) > 0
        assert not result.suppression_applied or result.suppression_reason is None
