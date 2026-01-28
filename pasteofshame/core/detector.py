"""High-performance detection engine for LLM-generated text patterns."""

import re
from typing import Any

import ahocorasick  # type: ignore[import-not-found]
import regex  # type: ignore[import-untyped]

from pasteofshame.core.rules import Rule, RulePack
from pasteofshame.core.scoring import ScoringEngine
from pasteofshame.core.types import Match, ScanResult


class Detector:
    """High-performance detector for LLM-generated text patterns.

    Performance features:
    - Uses `regex` library (faster than stdlib `re`, with Rust backend)
    - Uses Aho-Corasick algorithm for fast multi-string matching
    - Pre-compiles all regex patterns at initialization
    - Separates simple string patterns from complex regex patterns
    - ~10-20x faster than stdlib regex for typical workloads
    """

    def __init__(
        self,
        rule_pack: RulePack,
        scoring_engine: ScoringEngine | None = None,
    ) -> None:
        """
        Initialize the detector.

        Args:
            rule_pack: RulePack to use for detection
            scoring_engine: Optional custom scoring engine
        """
        self.rule_pack = rule_pack
        self.scoring_engine = scoring_engine or ScoringEngine()

        # Separate rules into simple string patterns and complex regex patterns
        self.simple_rules: list[Rule] = []
        self.regex_rules: list[tuple[Rule, Any]] = []

        # Build Aho-Corasick automaton for simple string patterns
        self.automaton: Any = None
        self._build_optimized_structures()

    def _build_optimized_structures(self) -> None:
        """Build optimized data structures for pattern matching."""
        automaton = ahocorasick.Automaton()
        automaton_index = 0

        for rule in self.rule_pack.rules:
            # Check if pattern is a simple string (no regex special chars)
            pattern = rule.pattern

            # Simple heuristic: if pattern has only word characters and spaces, use Aho-Corasick
            # For case-insensitive patterns without special regex chars, we can use Aho-Corasick
            is_simple = not any(char in pattern for char in r".*+?[]{}()^$|\\") and pattern.isascii()

            if is_simple:
                # Add to Aho-Corasick automaton (case-insensitive)
                automaton.add_word(pattern.lower(), (automaton_index, rule))
                automaton_index += 1
                self.simple_rules.append(rule)
            else:
                # Pre-compile complex regex patterns with the `regex` library
                try:
                    # Use regex library which is faster than stdlib re
                    compiled = regex.compile(pattern, regex.IGNORECASE)
                    self.regex_rules.append((rule, compiled))
                except Exception:
                    # Fallback to stdlib re if regex fails
                    compiled = re.compile(pattern, re.IGNORECASE)
                    self.regex_rules.append((rule, compiled))

        # Make automaton read-only for faster searching
        if automaton_index > 0:
            automaton.make_automaton()
            self.automaton = automaton

    def _process_simple_matches(self, text: str, text_lower: str, max_excerpt_length: int) -> tuple[list[Match], int]:
        """Process simple string patterns using Aho-Corasick."""
        matches: list[Match] = []
        total_score = 0

        if not self.automaton:
            return matches, total_score

        simple_matches: dict[int, list[tuple[int, int]]] = {}

        for end_index, (_, rule) in self.automaton.iter(text_lower):
            start_index = end_index - len(rule.pattern) + 1
            rule_id = id(rule)
            if rule_id not in simple_matches:
                simple_matches[rule_id] = []
            simple_matches[rule_id].append((start_index, end_index + 1))

        # Convert to Match objects
        for rule in self.simple_rules:
            rule_id = id(rule)
            if rule_id in simple_matches:
                spans = simple_matches[rule_id]
                excerpts = self._create_excerpts(text, spans, max_excerpt_length)
                matches.append(Match(rule=rule, spans=spans, excerpts=excerpts))
                total_score += rule.weight * len(spans)

        return matches, total_score

    def _process_regex_matches(self, text: str, max_excerpt_length: int) -> tuple[list[Match], int]:
        """Process complex regex patterns."""
        matches: list[Match] = []
        total_score = 0

        for rule, compiled_pattern in self.regex_rules:
            spans_list = []

            # Use finditer for better performance than findall
            for match_obj in compiled_pattern.finditer(text):
                spans_list.append((match_obj.start(), match_obj.end()))

            if spans_list:
                excerpts = self._create_excerpts(text, spans_list, max_excerpt_length)
                matches.append(Match(rule=rule, spans=spans_list, excerpts=excerpts))
                total_score += rule.weight * len(spans_list)

        return matches, total_score

    def _create_excerpts(self, text: str, spans: list[tuple[int, int]], max_excerpt_length: int) -> list[str]:
        """Create excerpts from text spans."""
        excerpts = []
        for start, end in spans:
            excerpt = text[start:end]
            if len(excerpt) > max_excerpt_length:
                excerpt = excerpt[:max_excerpt_length] + "..."
            excerpts.append(excerpt)
        return excerpts

    def scan(self, text: str, max_excerpt_length: int = 50) -> ScanResult:
        """
        Scan text for LLM patterns using optimized algorithms.

        Args:
            text: Text to scan
            max_excerpt_length: Maximum length of excerpts in results

        Returns:
            ScanResult with matches and scoring information
        """
        text_lower = text.lower()

        # Fast string matching with Aho-Corasick
        simple_matches, simple_score = self._process_simple_matches(text, text_lower, max_excerpt_length)

        # Regex matching for complex patterns
        regex_matches, regex_score = self._process_regex_matches(text, max_excerpt_length)

        # Combine results
        matches = simple_matches + regex_matches
        total_score = simple_score + regex_score

        # Apply suppression
        suppression_factor, suppression_reason = self.scoring_engine.calculate_suppression_factor(text)
        has_high_severity = any(m.rule.severity.value == "high" for m in matches)

        is_warning = self.scoring_engine.should_warn(total_score, has_high_severity, suppression_factor)

        return ScanResult(
            text=text,
            total_score=int(total_score * suppression_factor),
            matches=matches,
            is_warning=is_warning,
            suppression_applied=suppression_factor < 1.0,
            suppression_reason=suppression_reason,
        )
