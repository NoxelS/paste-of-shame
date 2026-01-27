"""Rule pack loader and manager."""

import importlib.resources
from pathlib import Path
from typing import Any

import yaml

from pasteofshame.core.types import Rule


class RulePack:
    """A collection of detection rules."""

    def __init__(self, rules: list[Rule]) -> None:
        """Initialize with a list of rules."""
        self.rules = rules
        for rule in self.rules:
            rule.compile()

    @classmethod
    def from_yaml(cls, path: str | Path) -> "RulePack":
        """Load rules from a YAML file."""
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RulePack":
        """Load rules from a dictionary."""
        rules = [Rule.from_dict(rule_data) for rule_data in data.get("rules", [])]
        return cls(rules)

    @classmethod
    def builtin(cls) -> "RulePack":
        """Load the built-in rule pack."""
        # Read the builtin.yml file from the patterns directory
        try:
            # Python 3.11+ compatibility
            files = importlib.resources.files("pasteofshame.core.patterns")
            builtin_path = files / "builtin.yml"
            with builtin_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except AttributeError:
            # Fallback for older Python versions
            import pkg_resources  # type: ignore[import-not-found]

            builtin_file = pkg_resources.resource_filename("pasteofshame.core.patterns", "builtin.yml")
            with open(builtin_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

        return cls.from_dict(data)

    def filter_by_language(self, languages: list[str]) -> "RulePack":
        """Filter rules by language."""
        filtered_rules = [rule for rule in self.rules if any(lang in rule.languages for lang in languages)]
        return RulePack(filtered_rules)

    def __len__(self) -> int:
        """Return the number of rules."""
        return len(self.rules)

    def __iter__(self) -> Any:
        """Iterate over rules."""
        return iter(self.rules)
