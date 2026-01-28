"""Daemon loop for clipboard monitoring."""

import hashlib
import logging
import time
from collections.abc import Callable

from pasteofshame.app.config import Config
from pasteofshame.clipboard.base import ClipboardWatcher
from pasteofshame.clipboard.polling import PollingClipboardWatcher
from pasteofshame.core.detector import Detector
from pasteofshame.core.rules import RulePack
from pasteofshame.core.scoring import ScoringEngine
from pasteofshame.notify.notifier import Notifier

# Try to import macOS native clipboard watcher
try:
    from pasteofshame.clipboard.macos_native import MacOSNativeClipboardWatcher

    MACOS_NATIVE_AVAILABLE = True
except ImportError:
    MACOS_NATIVE_AVAILABLE = False

logger = logging.getLogger(__name__)


class Daemon:
    """Daemon for continuous clipboard monitoring."""

    def __init__(
        self,
        config: Config,
        rule_pack: RulePack | None = None,
        notification_callback: Callable[[str, str, bool], None] | None = None,
    ) -> None:
        """
        Initialize the daemon.

        Args:
            config: Application configuration
            rule_pack: Optional custom rule pack (uses builtin if None)
            notification_callback: Optional callback for sending notifications from main app
                                 Takes (title, message, sound) as arguments
        """
        self.config = config
        self.notification_callback = notification_callback

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

        # Only use desktop notifications if no callback provided (CLI mode)
        self.notifier = Notifier(desktop_enabled=config.notify_enabled and notification_callback is None, verbose=True)

        # Use native macOS clipboard watcher if available (much faster!)
        self.watcher: ClipboardWatcher
        if MACOS_NATIVE_AVAILABLE:
            logger.info("Using native macOS clipboard watcher (NSPasteboard)")
            self.watcher = MacOSNativeClipboardWatcher(
                max_size=config.max_clipboard_size,
                check_interval=0.05,  # 50ms check interval (very low overhead)
            )
        else:
            logger.info("Using polling clipboard watcher")
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
        logger.info("🔍 Paste of Shame Clipboard Guard started")
        logger.info(f"   Threshold: {self.config.threshold}")
        logger.info(f"   Languages: {', '.join(self.config.enabled_languages)}")
        logger.info(f"   Desktop notifications: {'enabled' if self.config.notify_enabled else 'disabled'}")
        logger.info(f"   Notification callback: {'provided' if self.notification_callback else 'none'}")
        logger.info("\nWatching clipboard... (Press Ctrl+C to stop)\n")

        try:
            self.watcher.start(self._on_clipboard_change)
            # Keep main thread alive
            while self.watcher.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n\nStopping...")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the daemon."""
        self.watcher.stop()
        logger.info("✓ Stopped")

    def _on_clipboard_change(self, content: str) -> None:
        """
        Handle clipboard content change.

        Args:
            content: New clipboard content
        """
        logger.debug(f"Clipboard changed, content length: {len(content)}")

        # Check rate limiting
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # Skip if already warned about this exact content
        if content_hash in self._warned_hashes:
            logger.debug("Skipping: already warned about this content")
            return

        # Check global cooldown
        current_time = time.time()
        if current_time - self._last_warning_time < self.config.cooldown_seconds:
            logger.debug("Skipping: in cooldown period")
            return

        # Scan the content
        logger.debug("Scanning content...")
        result = self.detector.scan(content)
        logger.info(f"Scan result: score={result.total_score}, is_warning={result.is_warning}")

        # Notify if warning
        if result.is_warning:
            logger.warning(f"⚠️  LLM boilerplate detected! Score: {result.total_score}")

            # Use callback if provided (for macOS app with proper icon)
            if self.notification_callback:
                title = "🫣⁉️ Shameful Paste Ahead"
                message = f"Score: {result.total_score} - Review clipboard content before sharing."
                logger.info(f"Calling notification callback: {title}, sound={self.config.notify_sound}")
                try:
                    self.notification_callback(title, message, self.config.notify_sound)
                    logger.info("Notification callback succeeded")
                except Exception as e:
                    logger.error(f"Notification callback error: {e}", exc_info=True)
            else:
                logger.debug("No notification callback, using notifier directly")

            # Always use notifier for terminal output
            self.notifier.notify(result)

            self._warned_hashes.add(content_hash)
            self._last_warning_time = current_time

            # Limit the size of warned_hashes set
            if len(self._warned_hashes) > 100:
                # Remove oldest (though we don't track order, just clear some)
                self._warned_hashes = set(list(self._warned_hashes)[-50:])
