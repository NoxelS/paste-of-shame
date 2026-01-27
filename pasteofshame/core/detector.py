"""Main detection engine."""

from pasteofshame.core.rules import RulePack
from pasteofshame.core.scoring import ScoringEngine
from pasteofshame.core.types import Match, ScanResult


class Detector:
    """Main detector for LLM-generated text patterns."""

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

    def scan(self, text: str, max_excerpt_length: int = 50) -> ScanResult:
        """
        Scan text for LLM patterns.

        Args:
            text: Text to scan
            max_excerpt_length: Maximum length of excerpts in results

        Returns:
            ScanResult with matches and scoring information
        """
        matches: list[Match] = []
        total_score = 0

        for rule in self.rule_pack.rules:
            spans = rule.match(text)
            if spans:
                excerpts = []
                for start, end in spans:
                    excerpt = text[start:end]
                    if len(excerpt) > max_excerpt_length:
                        excerpt = excerpt[:max_excerpt_length] + "..."
                    excerpts.append(excerpt)

                matches.append(Match(rule=rule, spans=spans, excerpts=excerpts))
                total_score += rule.weight * len(spans)

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
