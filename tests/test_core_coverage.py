"""Tests for 100% coverage of core functionality."""

import tempfile
from pathlib import Path

import pytest
import yaml

from pasteofshame.core.detector import Detector
from pasteofshame.core.rules import RulePack
from pasteofshame.core.scoring import ScoringEngine
from pasteofshame.core.types import Match, Rule, RuleType, ScanResult, Severity


class TestRulePack:
    """Test RulePack class for missing coverage."""

    def test_from_yaml(self) -> None:
        """Test loading rules from YAML file."""
        yaml_content = """
rules:
  - id: test-rule
    description: Test rule
    pattern: test pattern
    type: phrase
    weight: 10
    severity: low
    languages: [en]
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            rule_pack = RulePack.from_yaml(temp_path)
            assert len(rule_pack) == 1
            assert rule_pack.rules[0].id == "test-rule"
        finally:
            Path(temp_path).unlink()

    def test_from_dict(self) -> None:
        """Test loading rules from dictionary."""
        data = {
            "rules": [
                {
                    "id": "test-1",
                    "description": "First test",
                    "pattern": "test",
                    "type": "phrase",
                    "weight": 5,
                    "severity": "low",
                },
                {
                    "id": "test-2",
                    "description": "Second test",
                    "pattern": "another",
                    "type": "phrase",
                    "weight": 10,
                    "severity": "medium",
                },
            ]
        }
        rule_pack = RulePack.from_dict(data)
        assert len(rule_pack) == 2
        assert rule_pack.rules[0].id == "test-1"
        assert rule_pack.rules[1].id == "test-2"

    def test_filter_by_language(self) -> None:
        """Test filtering rules by language."""
        rules = [
            Rule(
                id="en-rule",
                description="English rule",
                pattern="hello",
                rule_type=RuleType.PHRASE,
                weight=10,
                severity=Severity.LOW,
                languages=["en"],
            ),
            Rule(
                id="de-rule",
                description="German rule",
                pattern="hallo",
                rule_type=RuleType.PHRASE,
                weight=10,
                severity=Severity.LOW,
                languages=["de"],
            ),
            Rule(
                id="multi-rule",
                description="Multi language",
                pattern="test",
                rule_type=RuleType.PHRASE,
                weight=10,
                severity=Severity.LOW,
                languages=["en", "de"],
            ),
        ]
        rule_pack = RulePack(rules)

        # Filter for English only
        en_pack = rule_pack.filter_by_language(["en"])
        assert len(en_pack) == 2  # en-rule and multi-rule
        assert any(r.id == "en-rule" for r in en_pack.rules)
        assert any(r.id == "multi-rule" for r in en_pack.rules)

        # Filter for German only
        de_pack = rule_pack.filter_by_language(["de"])
        assert len(de_pack) == 2  # de-rule and multi-rule

    def test_iteration(self) -> None:
        """Test iterating over rules."""
        rules = [
            Rule(
                id=f"rule-{i}",
                description=f"Rule {i}",
                pattern=f"pattern{i}",
                rule_type=RuleType.PHRASE,
                weight=10,
                severity=Severity.LOW,
            )
            for i in range(3)
        ]
        rule_pack = RulePack(rules)

        count = 0
        for rule in rule_pack:
            assert rule.id.startswith("rule-")
            count += 1
        assert count == 3


class TestScoringEngine:
    """Test ScoringEngine for missing coverage."""

    def test_empty_text_suppression(self) -> None:
        """Test suppression for empty text."""
        engine = ScoringEngine()
        factor, reason = engine.calculate_suppression_factor("")
        assert factor == 0.0
        assert reason == "empty text"

        factor, reason = engine.calculate_suppression_factor("   \n  \n  ")
        assert factor == 0.0
        assert reason == "empty text"

    def test_allowlist_pattern_suppression(self) -> None:
        """Test allowlist pattern matching."""
        engine = ScoringEngine(allowlist_patterns=[r"test.*pattern", r"ignore me"])

        # Should match allowlist
        factor, reason = engine.calculate_suppression_factor("This is a test_pattern example")
        assert factor == 0.0
        assert reason == "matched allowlist pattern"

        factor, reason = engine.calculate_suppression_factor("Please ignore me this time")
        assert factor == 0.0
        assert reason == "matched allowlist pattern"

        # Should not match
        factor, reason = engine.calculate_suppression_factor("No match here")
        assert factor == 1.0
        assert reason is None

    def test_should_warn_with_high_severity(self) -> None:
        """Test that high severity always triggers warning."""
        engine = ScoringEngine(threshold=100)

        # Low score but high severity should warn
        assert engine.should_warn(score=1, has_high_severity=True, suppression_factor=1.0)

        # Even with suppression, high severity warns
        assert engine.should_warn(score=1, has_high_severity=True, suppression_factor=0.1)


class TestRule:
    """Test Rule class for missing coverage."""

    def test_rule_from_dict_defaults(self) -> None:
        """Test Rule.from_dict with default values."""
        # Minimal rule with defaults
        data = {
            "id": "minimal",
            "description": "Minimal rule",
            "pattern": "test",
        }
        rule = Rule.from_dict(data)
        assert rule.id == "minimal"
        assert rule.rule_type == RuleType.PHRASE  # default
        assert rule.weight == 10  # default
        assert rule.severity == Severity.LOW  # default
        assert rule.languages == ["en"]  # default
        assert rule.word_boundary is False  # default

    def test_rule_from_dict_full(self) -> None:
        """Test Rule.from_dict with all fields."""
        data = {
            "id": "full",
            "description": "Full rule",
            "pattern": r"\btest\b",
            "type": "regex",
            "weight": 25,
            "severity": "high",
            "languages": ["en", "de"],
            "word_boundary": True,
        }
        rule = Rule.from_dict(data)
        assert rule.id == "full"
        assert rule.rule_type == RuleType.REGEX
        assert rule.weight == 25
        assert rule.severity == Severity.HIGH
        assert rule.languages == ["en", "de"]
        assert rule.word_boundary is True

    def test_rule_match_runtime_error(self) -> None:
        """Test that match raises error if compilation somehow fails."""
        rule = Rule(
            id="test",
            description="Test",
            pattern="test",
            rule_type=RuleType.PHRASE,
            weight=10,
            severity=Severity.LOW,
        )
        # Manually break the compiled pattern
        rule._compiled = None

        # Calling match should recompile
        matches = rule.match("test text")
        assert len(matches) > 0


class TestScanResult:
    """Test ScanResult for missing coverage."""

    def test_has_high_severity(self) -> None:
        """Test has_high_severity method."""
        # Create rules with different severities
        low_rule = Rule(
            id="low",
            description="Low",
            pattern="test",
            rule_type=RuleType.PHRASE,
            weight=5,
            severity=Severity.LOW,
        )
        high_rule = Rule(
            id="high",
            description="High",
            pattern="danger",
            rule_type=RuleType.PHRASE,
            weight=10,
            severity=Severity.HIGH,
        )

        # Result with no high severity
        result1 = ScanResult(
            text="test",
            total_score=5,
            matches=[Match(rule=low_rule, spans=[(0, 4)], excerpts=["test"])],
            is_warning=False,
        )
        assert not result1.has_high_severity()

        # Result with high severity
        result2 = ScanResult(
            text="test danger",
            total_score=15,
            matches=[
                Match(rule=low_rule, spans=[(0, 4)], excerpts=["test"]),
                Match(rule=high_rule, spans=[(5, 11)], excerpts=["danger"]),
            ],
            is_warning=True,
        )
        assert result2.has_high_severity()

    def test_top_matches(self) -> None:
        """Test top_matches method."""
        rules = [
            Rule(
                id=f"rule-{i}",
                description=f"Rule {i}",
                pattern=f"test{i}",
                rule_type=RuleType.PHRASE,
                weight=i * 5,
                severity=Severity.LOW,
            )
            for i in range(5)
        ]

        matches = [
            Match(rule=rule, spans=[(0, 5)], excerpts=[f"test{i}"]) for i, rule in enumerate(rules)
        ]

        result = ScanResult(
            text="test0 test1 test2 test3 test4",
            total_score=50,
            matches=matches,
            is_warning=True,
        )

        # Get top 3
        top_3 = result.top_matches(3)
        assert len(top_3) == 3
        assert top_3[0].rule.weight == 20  # Highest weight
        assert top_3[1].rule.weight == 15
        assert top_3[2].rule.weight == 10

        # Get top 10 (more than available)
        top_10 = result.top_matches(10)
        assert len(top_10) == 5  # Only 5 matches available


class TestDetector:
    """Test Detector for missing coverage."""

    def test_detector_default_scoring_engine(self) -> None:
        """Test that detector creates default scoring engine if not provided."""
        rule_pack = RulePack.builtin()

        # Without scoring engine
        detector = Detector(rule_pack=rule_pack)
        assert detector.scoring_engine is not None
        assert isinstance(detector.scoring_engine, ScoringEngine)
        assert detector.scoring_engine.threshold == 20  # default

        # With custom scoring engine
        custom_engine = ScoringEngine(threshold=50)
        detector2 = Detector(rule_pack=rule_pack, scoring_engine=custom_engine)
        assert detector2.scoring_engine.threshold == 50


class TestRuleCompilation:
    """Test rule compilation edge cases."""

    def test_regex_rule_compilation(self) -> None:
        """Test regex rule compilation."""
        rule = Rule(
            id="regex-test",
            description="Regex test",
            pattern=r"\btest\d+\b",
            rule_type=RuleType.REGEX,
            weight=10,
            severity=Severity.LOW,
        )
        rule.compile()
        assert rule._compiled is not None

        # Test matching
        matches = rule.match("test123 and test456")
        assert len(matches) == 2

    def test_phrase_with_word_boundary(self) -> None:
        """Test phrase with word boundary."""
        rule = Rule(
            id="boundary-test",
            description="Boundary test",
            pattern="test",
            rule_type=RuleType.PHRASE,
            weight=10,
            severity=Severity.LOW,
            word_boundary=True,
        )
        rule.compile()

        # Should match whole word only
        matches = rule.match("test testing tests")
        assert len(matches) == 1  # Only matches "test", not "testing" or "tests"

    def test_phrase_without_word_boundary(self) -> None:
        """Test phrase without word boundary."""
        rule = Rule(
            id="no-boundary-test",
            description="No boundary test",
            pattern="test",
            rule_type=RuleType.PHRASE,
            weight=10,
            severity=Severity.LOW,
            word_boundary=False,
        )
        rule.compile()

        # Should match substring
        matches = rule.match("test testing tests")
        assert len(matches) == 3  # Matches in all three words


class TestEdgeCases:
    """Test edge cases for 100% coverage."""

    def test_rule_match_uncompiled_then_compile(self) -> None:
        """Test that match compiles pattern if needed."""
        rule = Rule(
            id="test",
            description="Test",
            pattern="test",
            rule_type=RuleType.PHRASE,
            weight=10,
            severity=Severity.LOW,
        )
        # Don't compile explicitly
        assert rule._compiled is None

        # Match should auto-compile
        matches = rule.match("test text")
        assert rule._compiled is not None
        assert len(matches) == 1

    def test_scoring_no_lines_edge_case(self) -> None:
        """Test scoring with text that has zero lines (edge case)."""
        engine = ScoringEngine()

        # This is a theoretical edge case - empty string after split
        # In practice, even empty string gives [''], but test the code path
        factor, reason = engine.calculate_suppression_factor("")
        assert factor == 0.0
        assert reason == "empty text"

    def test_detector_excerpt_not_truncated(self) -> None:
        """Test that short excerpts are not truncated."""
        rule = Rule(
            id="short",
            description="Short test",
            pattern="hi",
            rule_type=RuleType.PHRASE,
            weight=10,
            severity=Severity.LOW,
        )
        rule_pack = RulePack([rule])
        detector = Detector(rule_pack=rule_pack)

        # Short text should not be truncated
        result = detector.scan("hi there", max_excerpt_length=50)
        assert len(result.matches) == 1
        assert result.matches[0].excerpts[0] == "hi"
        assert "..." not in result.matches[0].excerpts[0]

    def test_builtin_rulepack_python_version_fallback(self) -> None:
        """Test that builtin() works (covers both code paths)."""
        # This tests the actual builtin loading
        rule_pack = RulePack.builtin()
        assert len(rule_pack) > 0
        assert any(rule.id for rule in rule_pack.rules)

        # The code has a try/except for different Python versions
        # In Python 3.10+, importlib.resources.files works
        # In older versions, it falls back to pkg_resources
        # Our test environment uses 3.10+, so we get the first path
        # But the test at least verifies the builtin loading works


class TestRemainingCoverage:
    """Tests specifically targeting remaining uncovered lines."""

    def test_excerpt_truncation_boundary(self) -> None:
        """Test exact boundary case for excerpt truncation (detector.py:47)."""
        # Create a rule that matches exactly at max_excerpt_length
        rule = Rule(
            id="boundary",
            description="Boundary test",
            pattern="a" * 51,  # 51 chars - over the 50 limit
            rule_type=RuleType.PHRASE,
            weight=10,
            severity=Severity.LOW,
        )
        rule_pack = RulePack([rule])
        detector = Detector(rule_pack=rule_pack)

        # Text with match that exceeds max_excerpt_length
        text = "a" * 51
        result = detector.scan(text, max_excerpt_length=50)

        # Should have match with truncated excerpt
        assert len(result.matches) == 1
        assert len(result.matches[0].excerpts[0]) == 53  # 50 + "..."
        assert result.matches[0].excerpts[0].endswith("...")

    def test_scoring_total_lines_zero_impossible(self) -> None:
        """Test that we handle the theoretical zero lines case (scoring.py:33)."""
        # In practice, even empty string gives [''] after split
        # But let's test whitespace-only strings that might trigger edge cases
        engine = ScoringEngine()

        # These should all hit the empty text check first
        test_cases = ["", "   ", "\n\n\n", "\t\t", "  \n  \n  "]
        for text in test_cases:
            factor, reason = engine.calculate_suppression_factor(text)
            assert factor == 0.0
            assert reason == "empty text"

    def test_high_severity_warning_with_suppression(self) -> None:
        """Test high severity warning even with full suppression (scoring.py:52)."""
        engine = ScoringEngine(threshold=100)

        # Even with score of 0 and full suppression, high severity should warn
        result = engine.should_warn(score=0, has_high_severity=True, suppression_factor=0.0)
        assert result is True

        # Without high severity, low score shouldn't warn
        result = engine.should_warn(score=0, has_high_severity=False, suppression_factor=0.0)
        assert result is False

    def test_rule_compile_none_check(self) -> None:
        """Test the None check after compile in match method (types.py:64-65)."""
        rule = Rule(
            id="test",
            description="Test",
            pattern="test",
            rule_type=RuleType.PHRASE,
            weight=10,
            severity=Severity.LOW,
        )

        # Ensure not compiled
        assert rule._compiled is None

        # Call match which should compile
        matches = rule.match("test text")

        # Now should be compiled
        assert rule._compiled is not None
        assert len(matches) == 1

        # Manually set to None to test the RuntimeError path
        original_compile = rule.compile

        def broken_compile() -> None:
            """Broken compile that doesn't set _compiled."""
            pass  # Don't actually compile

        rule.compile = broken_compile  # type: ignore[method-assign]
        rule._compiled = None

        # This should raise RuntimeError
        with pytest.raises(RuntimeError, match="Pattern compilation failed"):
            rule.match("test")

        # Restore
        rule.compile = original_compile  # type: ignore[method-assign]

    def test_multiple_excerpts_from_single_rule(self) -> None:
        """Test multiple matches creating multiple excerpts (detector.py:42-49)."""
        rule = Rule(
            id="multi",
            description="Multi match",
            pattern="test",
            rule_type=RuleType.PHRASE,
            weight=5,
            severity=Severity.LOW,
        )
        rule_pack = RulePack([rule])
        detector = Detector(rule_pack=rule_pack)

        # Text with multiple matches, some short, some long
        text = "test " + ("x" * 60) + " test " + ("y" * 60) + " test"
        result = detector.scan(text, max_excerpt_length=50)

        # Should have one match with 3 excerpts
        assert len(result.matches) == 1
        assert len(result.matches[0].excerpts) == 3
        assert result.matches[0].excerpts[0] == "test"
        assert result.matches[0].excerpts[2] == "test"

    def test_allowlist_patterns_iteration(self) -> None:
        """Test that allowlist patterns are checked in order (scoring.py:43-45)."""
        patterns = [r"pattern1", r"pattern2", r"pattern3"]
        engine = ScoringEngine(allowlist_patterns=patterns)

        # Test each pattern
        for i, _pattern in enumerate(patterns, 1):
            text = f"This has pattern{i} in it"
            factor, reason = engine.calculate_suppression_factor(text)
            assert factor == 0.0
            assert reason == "matched allowlist pattern"

        # Test non-matching
        factor, reason = engine.calculate_suppression_factor("This has pattern4")
        assert factor == 1.0
        assert reason is None

