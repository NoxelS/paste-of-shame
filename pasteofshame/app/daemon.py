"""Daemon loop for clipboard monitoring."""

import hashlib
import time

from pasteofshame.app.config import Config
from pasteofshame.clipboard.polling import PollingClipboardWatcher
from pasteofshame.core.detector import Detector
from pasteofshame.core.rules import RulePack
from pasteofshame.core.scoring import ScoringEngine
from pasteofshame.notify.notifier import Notifier


class Daemon:
    """Daemon for continuous clipboard monitoring."""

    def __init__(self, config: Config, rule_pack: RulePack | None = None) -> None:
        """
        Initialize the daemon.

        Args:
            config: Application configuration
            rule_pack: Optional custom rule pack (uses builtin if None)
        """
        self.config = config

        # Initialize components
        if rule_pack is None:
            rule_pack = RulePack.builtin()

        # Filter rules by enabled languages
        rule_pack = rule_pack.filter_by_language(config.enabled_languages)

        scoring_engine = ScoringEngine(
            threshold=config.threshold,
            allowlist_patterns=config.allowlist_patterns,
        )

        self.detector = Detector(rule_pack=rule_pack, scoring_engine=scoring_engine)
        self.notifier = Notifier(desktop_enabled=config.notify_enabled, verbose=True)

        self.watcher = PollingClipboardWatcher(
            initial_interval=config.poll_interval,
            max_interval=config.max_poll_interval,
            max_size=config.max_clipboard_size,
        )

        # Rate limiting
        self._warned_hashes: set[str] = set()
        self._last_warning_time: float = 0.0

    def start(self) -> None:
        """Start the daemon."""
        print("🔍 Paste of Shame Clipboard Guard started")
        print(f"   Threshold: {self.config.threshold}")
        print(f"   Languages: {', '.join(self.config.enabled_languages)}")
        print(f"   Desktop notifications: {'enabled' if self.config.notify_enabled else 'disabled'}")
        print("\nWatching clipboard... (Press Ctrl+C to stop)\n")

        try:
            self.watcher.start(self._on_clipboard_change)
            # Keep main thread alive
            while self.watcher.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nStopping...")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the daemon."""
        self.watcher.stop()
        print("✓ Stopped")

    def _on_clipboard_change(self, content: str) -> None:
        """
        Handle clipboard content change.

        Args:
            content: New clipboard content
        """
        # Check rate limiting
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # Skip if already warned about this exact content
        if content_hash in self._warned_hashes:
            return

        # Check global cooldown
        current_time = time.time()
        if current_time - self._last_warning_time < self.config.cooldown_seconds:
            return

        # Scan the content
        result = self.detector.scan(content)

        # Notify if warning
        if result.is_warning:
            self.notifier.notify(result)
            self._warned_hashes.add(content_hash)
            self._last_warning_time = current_time

            # Limit the size of warned_hashes set
            if len(self._warned_hashes) > 100:
                # Remove oldest (though we don't track order, just clear some)
                self._warned_hashes = set(list(self._warned_hashes)[-50:])
