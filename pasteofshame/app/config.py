"""Configuration management."""

import os
import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Config:
    """Application configuration."""

    threshold: int = 20
    enabled_languages: list[str] = field(default_factory=lambda: ["en"])
    allowlist_patterns: list[str] = field(default_factory=list)
    notify_enabled: bool = True
    poll_interval: float = 0.3
    max_poll_interval: float = 2.0
    cooldown_seconds: float = 5.0
    max_clipboard_size: int = 200_000

    @classmethod
    def get_config_path(cls) -> Path:
        """Get the default config file path for the current platform."""
        system = platform.system()

        if system == "Darwin":  # macOS
            base = Path.home() / "Library" / "Application Support"
        elif system == "Windows":
            appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
            base = appdata
        else:  # Linux and others
            base = Path.home() / ".config"

        config_dir = base / "paste-of-shame"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.yml"

    @classmethod
    def load(cls, path: Path | str | None = None) -> "Config":
        """
        Load configuration from file.

        Args:
            path: Optional path to config file. If None, uses default location.

        Returns:
            Config instance with loaded or default values
        """
        if path is None:
            path = cls.get_config_path()
        else:
            path = Path(path)

        if not path.exists():
            # Return default config
            return cls()

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        return cls(
            threshold=data.get("threshold", 20),
            enabled_languages=data.get("enabled_languages", ["en"]),
            allowlist_patterns=data.get("allowlist_patterns", []),
            notify_enabled=data.get("notify_enabled", True),
            poll_interval=data.get("poll_interval", 0.3),
            max_poll_interval=data.get("max_poll_interval", 2.0),
            cooldown_seconds=data.get("cooldown_seconds", 5.0),
            max_clipboard_size=data.get("max_clipboard_size", 200_000),
        )

    def save(self, path: Path | str | None = None) -> None:
        """
        Save configuration to file.

        Args:
            path: Optional path to config file. If None, uses default location.
        """
        if path is None:
            path = self.get_config_path()
        else:
            path = Path(path)

        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "threshold": self.threshold,
            "enabled_languages": self.enabled_languages,
            "allowlist_patterns": self.allowlist_patterns,
            "notify_enabled": self.notify_enabled,
            "poll_interval": self.poll_interval,
            "max_poll_interval": self.max_poll_interval,
            "cooldown_seconds": self.cooldown_seconds,
            "max_clipboard_size": self.max_clipboard_size,
        }

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
