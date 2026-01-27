"""Type definitions for the detection engine."""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """Severity level for a rule match."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RuleType(str, Enum):
    """Type of pattern matching rule."""

    PHRASE = "phrase"
    REGEX = "regex"


@dataclass
class Rule:
    """A detection rule for LLM-generated text patterns."""

    id: str
    description: str
    pattern: str
    rule_type: RuleType
    weight: int
    severity: Severity
    languages: list[str] = field(default_factory=lambda: ["en"])
    word_boundary: bool = False
    _compiled: re.Pattern[str] | None = field(default=None, init=False, repr=False)

    def compile(self) -> None:
        """Compile the pattern for faster matching."""
        if self.rule_type == RuleType.REGEX:
            self._compiled = re.compile(self.pattern, re.IGNORECASE | re.MULTILINE)
        elif self.rule_type == RuleType.PHRASE:
            if self.word_boundary:
                # Use word boundaries for phrase matching
                escaped = re.escape(self.pattern)
                pattern = rf"\b{escaped}\b"
                self._compiled = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            else:
                # Simple case-insensitive substring search via regex
                escaped = re.escape(self.pattern)
                self._compiled = re.compile(escaped, re.IGNORECASE | re.MULTILINE)

    def match(self, text: str) -> list[tuple[int, int]]:
        """
        Find all matches in the text.

        Returns:
            List of (start, end) tuples for each match span.
        """
        if self._compiled is None:
            self.compile()
        # Compile ensures _compiled is not None
        if self._compiled is None:
            msg = "Pattern compilation failed"
            raise RuntimeError(msg)
        return [(m.start(), m.end()) for m in self._compiled.finditer(text)]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Rule":
        """Create a Rule from a dictionary."""
        return cls(
            id=data["id"],
            description=data["description"],
            pattern=data["pattern"],
            rule_type=RuleType(data.get("type", "phrase")),
            weight=data.get("weight", 10),
            severity=Severity(data.get("severity", "low")),
            languages=data.get("languages", ["en"]),
            word_boundary=data.get("word_boundary", False),
        )


@dataclass
class Match:
    """A single rule match with context."""

    rule: Rule
    spans: list[tuple[int, int]]
    excerpts: list[str]


@dataclass
class ScanResult:
    """Result of scanning text for LLM patterns."""

    text: str
    total_score: int
    matches: list[Match]
    is_warning: bool
    suppression_applied: bool = False
    suppression_reason: str | None = None

    def has_high_severity(self) -> bool:
        """Check if any match has high severity."""
        return any(m.rule.severity == Severity.HIGH for m in self.matches)

    def top_matches(self, n: int = 3) -> list[Match]:
        """Get the top N matches by weight."""
        return sorted(self.matches, key=lambda m: m.rule.weight, reverse=True)[:n]
