"""Core detection engine for LLM-generated text patterns."""

from pasteofshame.core.detector import Detector
from pasteofshame.core.rules import RulePack
from pasteofshame.core.types import Match, Rule, ScanResult, Severity

__all__ = ["Detector", "Match", "Rule", "RulePack", "ScanResult", "Severity"]
