"""Performance tests to ensure the tool is responsive and not lagging."""

import time

import pytest

from pasteofshame.core.detector import Detector
from pasteofshame.core.rules import RulePack
from pasteofshame.core.scoring import ScoringEngine


class TestPerformance:
    """Test performance characteristics of the detection system."""

    @pytest.fixture
    def detector(self) -> Detector:
        """Create a detector with builtin rules."""
        rule_pack = RulePack.builtin()
        scoring_engine = ScoringEngine(threshold=20)
        return Detector(rule_pack=rule_pack, scoring_engine=scoring_engine)

    def test_small_text_scan_speed(self, detector: Detector) -> None:
        """Test that small text (< 1KB) scans in under 50ms."""
        text = "As an AI language model, I must inform you that certainly, I hope this helps!"

        start = time.perf_counter()
        result = detector.scan(text)
        elapsed = time.perf_counter() - start

        assert result.is_warning
        assert elapsed < 0.050, f"Small text scan took {elapsed * 1000:.2f}ms (expected < 50ms)"

    def test_medium_text_scan_speed(self, detector: Detector) -> None:
        """Test that medium text (~10KB) scans in under 100ms."""
        # Create a 10KB text block
        text = (
            "This is a normal paragraph. " * 100
            + "As an AI language model, I cannot assist. "
            + "Normal text continues here. " * 100
        )

        start = time.perf_counter()
        result = detector.scan(text)
        elapsed = time.perf_counter() - start

        assert len(text) > 5000  # Ensure we have substantial text
        assert elapsed < 0.100, f"Medium text scan took {elapsed * 1000:.2f}ms (expected < 100ms)"

    def test_large_text_scan_speed(self, detector: Detector) -> None:
        """Test that large text (~100KB) scans in under 500ms."""
        # Create a 100KB text block with some LLM patterns
        text = (
            "Normal text without any special patterns. " * 1000
            + "Certainly! Below is the implementation. "
            + "More normal text here. " * 1000
        )

        start = time.perf_counter()
        detector.scan(text)
        elapsed = time.perf_counter() - start

        assert len(text) > 50000  # Ensure we have large text
        assert elapsed < 0.500, f"Large text scan took {elapsed * 1000:.2f}ms (expected < 500ms)"

    def test_rule_compilation_speed(self) -> None:
        """Test that rule pack loading is fast."""
        start = time.perf_counter()
        rule_pack = RulePack.builtin()
        elapsed = time.perf_counter() - start

        assert len(rule_pack.rules) > 0
        assert elapsed < 0.150, f"Rule compilation took {elapsed * 1000:.2f}ms (expected < 150ms)"

    def test_detector_initialization_speed(self) -> None:
        """Test that detector initialization is fast."""
        rule_pack = RulePack.builtin()

        start = time.perf_counter()
        detector = Detector(rule_pack=rule_pack)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.010, f"Detector init took {elapsed * 1000:.2f}ms (expected < 10ms)"

    def test_multiple_scans_no_slowdown(self, detector: Detector) -> None:
        """Test that repeated scans don't slow down over time."""
        text = "Certainly! As an AI language model, I hope this helps!"

        timings = []
        for _ in range(100):
            start = time.perf_counter()
            detector.scan(text)
            elapsed = time.perf_counter() - start
            timings.append(elapsed)

        # Check that last 10 scans aren't significantly slower than first 10
        avg_first = sum(timings[:10]) / 10
        avg_last = sum(timings[-10:]) / 10

        # Allow 50% variance but no significant degradation
        assert avg_last < avg_first * 1.5, (
            f"Performance degraded: first avg {avg_first * 1000:.2f}ms, last avg {avg_last * 1000:.2f}ms"
        )

    def test_empty_text_scan_speed(self, detector: Detector) -> None:
        """Test that empty text is handled efficiently."""
        start = time.perf_counter()
        result = detector.scan("")
        elapsed = time.perf_counter() - start

        assert not result.is_warning
        assert elapsed < 0.001, f"Empty text scan took {elapsed * 1000:.2f}ms (expected < 1ms)"

    def test_no_match_text_scan_speed(self, detector: Detector) -> None:
        """Test that text with no matches is still fast."""
        text = "This is completely normal text without any LLM patterns whatsoever. " * 50

        start = time.perf_counter()
        result = detector.scan(text)
        elapsed = time.perf_counter() - start

        assert not result.is_warning
        assert elapsed < 0.050, f"No-match text scan took {elapsed * 1000:.2f}ms (expected < 50ms)"

    def test_suppression_calculation_speed(self, detector: Detector) -> None:
        """Test that suppression logic doesn't significantly slow down scans."""
        # Text with code fences (triggers suppression)
        text_with_code = """```python
def test():
    return "As an AI language model"
```
Certainly! Below is the code."""

        start = time.perf_counter()
        result = detector.scan(text_with_code)
        elapsed = time.perf_counter() - start

        assert result.suppression_applied or len(result.matches) > 0
        assert elapsed < 0.050, f"Suppression scan took {elapsed * 1000:.2f}ms (expected < 50ms)"

    def test_quoted_text_suppression_speed(self, detector: Detector) -> None:
        """Test that quoted text suppression is efficient."""
        # Heavily quoted text
        quoted_text = "\n".join([f"> Certainly! Line {i}" for i in range(100)])

        start = time.perf_counter()
        result = detector.scan(quoted_text)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.100, f"Quoted text scan took {elapsed * 1000:.2f}ms (expected < 100ms)"

    def test_scoring_engine_performance(self) -> None:
        """Test that scoring engine calculations are fast."""
        scoring_engine = ScoringEngine(threshold=20, allowlist_patterns=[r"test.*pattern"])

        text = "Normal text with some content that might match patterns. " * 10

        start = time.perf_counter()
        factor, reason = scoring_engine.calculate_suppression_factor(text)
        elapsed = time.perf_counter() - start

        assert 0.0 <= factor <= 1.0
        assert elapsed < 0.010, f"Suppression calc took {elapsed * 1000:.2f}ms (expected < 10ms)"

    def test_rule_filtering_speed(self) -> None:
        """Test that language filtering is fast."""
        rule_pack = RulePack.builtin()

        start = time.perf_counter()
        filtered = rule_pack.filter_by_language(["en"])
        elapsed = time.perf_counter() - start

        assert len(filtered.rules) > 0
        assert elapsed < 0.005, f"Rule filtering took {elapsed * 1000:.2f}ms (expected < 5ms)"

    def test_memory_efficiency(self, detector: Detector) -> None:
        """Test that scanning doesn't create excessive objects."""
        import gc

        text = "Certainly! As an AI language model, I hope this helps!"

        # Force garbage collection before test
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Run multiple scans
        for _ in range(50):
            detector.scan(text)

        # Force garbage collection after test
        gc.collect()
        final_objects = len(gc.get_objects())

        # Allow some object growth but not excessive (< 50% increase)
        object_growth = (final_objects - initial_objects) / initial_objects
        assert object_growth < 0.5, (
            f"Excessive object growth: {object_growth * 100:.1f}% ({initial_objects} -> {final_objects})"
        )
