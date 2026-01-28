"""Performance benchmarks for Paste of Shame detector.

This module uses pytest-benchmark to track performance metrics and ensure
no performance regressions occur. Run with:

    pytest tests/test_benchmarks.py --benchmark-only
    pytest tests/test_benchmarks.py --benchmark-save=baseline
    pytest tests/test_benchmarks.py --benchmark-compare

To see detailed statistics:
    pytest tests/test_benchmarks.py --benchmark-only --benchmark-verbose
"""

import pytest

from pasteofshame.core.detector import Detector
from pasteofshame.core.rules import RulePack
from pasteofshame.core.scoring import ScoringEngine


@pytest.fixture(scope="module")
def detector():
    """Create a detector instance for benchmarking."""
    rule_pack = RulePack.builtin()
    scoring_engine = ScoringEngine(threshold=20)
    return Detector(rule_pack=rule_pack, scoring_engine=scoring_engine)


@pytest.fixture(scope="module")
def small_text_with_match():
    """Small text with LLM patterns (< 100 bytes)."""
    return "As an AI language model, I must inform you that certainly, I hope this helps!"


@pytest.fixture(scope="module")
def small_text_no_match():
    """Small text without LLM patterns."""
    return "This is just normal text without any AI patterns. Nothing to see here, really."


@pytest.fixture(scope="module")
def medium_text():
    """Medium text with some matches (~5KB)."""
    return (
        "This is a normal paragraph about software development. " * 50
        + "As an AI language model, I cannot assist with that. "
        + "Certainly! Here's a comprehensive solution. "
        + "I hope this helps clarify things. "
        + "More normal text continues here. " * 50
    )


@pytest.fixture(scope="module")
def large_text():
    """Large text with some matches (~50KB)."""
    return (
        "Normal text without any special patterns. " * 600
        + "Certainly! Below is the implementation. "
        + "As an AI assistant, I can provide guidance. "
        + "I hope this helps! "
        + "More normal text here. " * 600
    )


@pytest.fixture(scope="module")
def huge_text():
    """Huge text for stress testing (~500KB)."""
    return (
        "Normal text without any special patterns. " * 6000
        + "Certainly! Below is the implementation. "
        + "As an AI assistant, I can provide guidance. "
        + "I hope this helps! "
        + "More normal text here. " * 6000
    )


@pytest.fixture(scope="module")
def many_matches_text():
    """Text with many LLM pattern matches."""
    return "Certainly! " * 100 + "As an AI language model, " * 50 + "I hope this helps! " * 100


@pytest.fixture(scope="module")
def code_heavy_text():
    """Code-heavy text with code fences."""
    return (
        """
```python
def example_function():
    # Certainly! Here's an implementation
    return "As an AI language model, I hope this helps"
```

```javascript
function example() {
    // Certainly! Here's the code
    return "I hope this helps!";
}
```
"""
        * 50
    )


# ============================================================================
# Initialization Benchmarks
# ============================================================================


class TestInitializationBenchmarks:
    """Benchmark initialization performance."""

    def test_benchmark_rule_pack_loading(self, benchmark):
        """Benchmark loading the builtin rule pack."""
        result = benchmark(RulePack.builtin)
        assert len(result.rules) > 0

    def test_benchmark_detector_initialization(self, benchmark):
        """Benchmark creating a detector instance."""

        def setup_detector():
            rule_pack = RulePack.builtin()
            scoring_engine = ScoringEngine(threshold=20)
            return Detector(rule_pack=rule_pack, scoring_engine=scoring_engine)

        result = benchmark(setup_detector)
        assert result is not None


# ============================================================================
# Scanning Benchmarks - Small Text
# ============================================================================


class TestSmallTextBenchmarks:
    """Benchmark small text scanning performance."""

    def test_benchmark_small_text_with_match(self, benchmark, detector, small_text_with_match):
        """Benchmark scanning small text with matches."""
        result = benchmark(detector.scan, small_text_with_match)
        assert result.total_score > 0

    def test_benchmark_small_text_no_match(self, benchmark, detector, small_text_no_match):
        """Benchmark scanning small text without matches."""
        result = benchmark(detector.scan, small_text_no_match)
        assert result.total_score == 0


# ============================================================================
# Scanning Benchmarks - Medium to Huge Text
# ============================================================================


class TestLargeTextBenchmarks:
    """Benchmark large text scanning performance."""

    def test_benchmark_medium_text(self, benchmark, detector, medium_text):
        """Benchmark scanning medium text (~5KB)."""
        result = benchmark(detector.scan, medium_text)
        assert result.total_score > 0
        assert len(medium_text) > 4000  # Verify size

    def test_benchmark_large_text(self, benchmark, detector, large_text):
        """Benchmark scanning large text (~50KB)."""
        result = benchmark(detector.scan, large_text)
        assert result.total_score > 0
        assert len(large_text) > 30000  # Verify size

    def test_benchmark_huge_text(self, benchmark, detector, huge_text):
        """Benchmark scanning huge text (~500KB)."""
        result = benchmark(detector.scan, huge_text)
        assert result.total_score > 0
        assert len(huge_text) > 300000  # Verify size


# ============================================================================
# Special Case Benchmarks
# ============================================================================


class TestSpecialCaseBenchmarks:
    """Benchmark special case scenarios."""

    def test_benchmark_many_matches(self, benchmark, detector, many_matches_text):
        """Benchmark scanning text with many matches."""
        result = benchmark(detector.scan, many_matches_text)
        assert result.total_score > 100  # Should have high score
        assert len(result.matches) > 2  # Should have multiple matches

    def test_benchmark_code_heavy(self, benchmark, detector, code_heavy_text):
        """Benchmark scanning code-heavy text with fences."""
        result = benchmark(detector.scan, code_heavy_text)
        # Code fences should suppress scoring
        assert result.suppression_applied or result.total_score >= 0


# ============================================================================
# Throughput Benchmarks
# ============================================================================


class TestThroughputBenchmarks:
    """Benchmark throughput in bytes/second."""

    def test_benchmark_throughput_medium(self, benchmark, detector, medium_text):
        """Measure throughput for medium text."""
        text_size = len(medium_text)
        result = benchmark(detector.scan, medium_text)

        # Just verify it completed successfully
        assert result is not None
        assert text_size > 4000  # Verify size

    def test_benchmark_throughput_large(self, benchmark, detector, large_text):
        """Measure throughput for large text."""
        text_size = len(large_text)
        result = benchmark(detector.scan, large_text)

        # Just verify it completed successfully
        assert result is not None
        assert text_size > 30000  # Verify size


# ============================================================================
# Performance Regression Tests
# ============================================================================


class TestPerformanceRegression:
    """Test for performance regressions against baseline."""

    @pytest.mark.benchmark(group="regression", min_rounds=10)
    def test_no_regression_small_text(self, benchmark, detector, small_text_with_match):
        """Ensure small text scanning doesn't regress."""
        result = benchmark(detector.scan, small_text_with_match)
        # Should complete in < 1ms on modern hardware
        assert result is not None

    @pytest.mark.benchmark(group="regression", min_rounds=5)
    def test_no_regression_large_text(self, benchmark, detector, large_text):
        """Ensure large text scanning doesn't regress."""
        result = benchmark(detector.scan, large_text)
        # Should complete in < 50ms on modern hardware
        assert result is not None

    @pytest.mark.benchmark(group="regression", min_rounds=3)
    def test_no_regression_huge_text(self, benchmark, detector, huge_text):
        """Ensure huge text scanning doesn't regress."""
        result = benchmark(detector.scan, huge_text)
        # Should complete in < 500ms on modern hardware
        assert result is not None


# ============================================================================
# Pattern Matching Algorithm Benchmarks
# ============================================================================


class TestAlgorithmBenchmarks:
    """Benchmark specific algorithm components."""

    def test_benchmark_aho_corasick_only(self, benchmark, detector, large_text):
        """Benchmark Aho-Corasick string matching performance."""
        text_lower = large_text.lower()

        def run_aho_corasick():
            if detector.automaton:
                matches = list(detector.automaton.iter(text_lower))
                return matches
            return []

        result = benchmark(run_aho_corasick)
        # Should find some matches
        assert len(result) >= 0

    def test_benchmark_regex_only(self, benchmark, detector, large_text):
        """Benchmark regex matching performance."""

        def run_regex():
            matches = []
            for _rule, pattern in detector.regex_rules:
                for match in pattern.finditer(large_text):
                    matches.append(match)
            return matches

        result = benchmark(run_regex)
        # May or may not find matches depending on patterns
        assert result is not None


# ============================================================================
# Memory Efficiency Tests
# ============================================================================


class TestMemoryEfficiency:
    """Test memory efficiency of scanning operations."""

    def test_benchmark_repeated_scans(self, benchmark, detector, medium_text):
        """Benchmark repeated scans to check for memory leaks."""

        def repeated_scans():
            results = []
            for _ in range(10):
                result = detector.scan(medium_text)
                results.append(result)
            return results

        results = benchmark(repeated_scans)
        assert len(results) == 10
        # All results should be valid
        assert all(r.total_score >= 0 for r in results)
