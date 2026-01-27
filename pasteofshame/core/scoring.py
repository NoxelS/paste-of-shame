"""Scoring and suppression logic."""

import re


class ScoringEngine:
    """Scoring engine with suppression logic."""

    def __init__(self, threshold: int = 20, allowlist_patterns: list[str] | None = None) -> None:
        """
        Initialize the scoring engine.

        Args:
            threshold: Score threshold for warnings
            allowlist_patterns: Regex patterns that suppress warnings when matched
        """
        self.threshold = threshold
        self.allowlist_patterns = [re.compile(p, re.IGNORECASE) for p in (allowlist_patterns or [])]

    def calculate_suppression_factor(self, text: str) -> tuple[float, str | None]:
        """
        Calculate suppression factor based on text characteristics.

        Returns:
            Tuple of (factor, reason) where factor is 0.0-1.0 (1.0 = no suppression)
        """
        if not text.strip():
            return 0.0, "empty text"

        lines = text.split("\n")
        total_lines = len(lines)
        if total_lines == 0:
            return 0.0, "no lines"

        # Check for quoted text (email-style quotes)
        quoted_lines = sum(1 for line in lines if line.strip().startswith(">"))
        quote_ratio = quoted_lines / total_lines

        # Check for code fences
        code_fence_count = text.count("```")
        has_code_fences = code_fence_count >= 2

        # Check allowlist
        for pattern in self.allowlist_patterns:
            if pattern.search(text):
                return 0.0, "matched allowlist pattern"

        # Apply suppression
        if quote_ratio > 0.7:
            return 0.3, "mostly quoted text"
        elif quote_ratio > 0.4:
            return 0.6, "partially quoted text"
        elif has_code_fences:
            return 0.5, "contains code fences"

        return 1.0, None

    def should_warn(self, score: int, has_high_severity: bool, suppression_factor: float) -> bool:
        """
        Determine if a warning should be issued.

        Args:
            score: Raw score before suppression
            has_high_severity: Whether any high severity match was found
            suppression_factor: Factor to apply (0.0-1.0)

        Returns:
            True if warning should be issued
        """
        adjusted_score = int(score * suppression_factor)
        return adjusted_score >= self.threshold or has_high_severity
