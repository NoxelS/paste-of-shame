"""
Paste of Shame - Clipboard watchdog for detecting LLM-generated boilerplate.

A cross-platform tool that monitors your clipboard and warns you when
you copy text containing common LLM artifacts and boilerplate phrases.
"""

__version__ = "0.1.0"

from pasteofshame.core import (
    Detector,
    Match,
    Rule,
    RulePack,
    ScanResult,
    Severity,
)

__all__ = [
    "Detector",
    "Match",
    "Rule",
    "RulePack",
    "ScanResult",
    "Severity",
    "__version__",
    "create_detector",
    "get_best_backend",
    "list_available_backends",
]
