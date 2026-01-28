"""Native macOS clipboard watcher using NSPasteboard change count."""

import hashlib
import logging
from collections.abc import Callable
from threading import Event, Thread

from pasteofshame.clipboard.base import ClipboardWatcher

logger = logging.getLogger(__name__)

# Try to import macOS native clipboard API
try:
    from AppKit import NSPasteboard  # type: ignore[import-not-found,import-untyped]

    NATIVE_AVAILABLE = True
except ImportError:
    NATIVE_AVAILABLE = False
    logger.warning("AppKit not available, falling back to polling")


class MacOSNativeClipboardWatcher(ClipboardWatcher):
    """Native macOS clipboard watcher using NSPasteboard change count.

    This is much more efficient than polling because it uses the native
    macOS clipboard change counter (changeCount) to detect changes instantly.
    """

    def __init__(self, max_size: int = 200_000, check_interval: float = 0.05) -> None:
        """
        Initialize the native macOS watcher.

        Args:
            max_size: Maximum clipboard content size to process (characters)
            check_interval: How often to check the change count (seconds)
                           Very low overhead since we only check an integer
        """
        self.max_size = max_size
        self.check_interval = check_interval
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._last_hash: str | None = None
        self._last_change_count: int = -1

        if not NATIVE_AVAILABLE:
            msg = "AppKit not available. Install with: pip install pyobjc-framework-Cocoa"
            raise ImportError(msg)

    def start(self, callback: Callable[[str], None]) -> None:
        """Start watching the clipboard in a background thread."""
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = Thread(target=self._watch_loop, args=(callback,), daemon=True)
        self._thread.start()
        logger.info("Native macOS clipboard watcher started")

    def stop(self) -> None:
        """Stop watching the clipboard."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info("Native macOS clipboard watcher stopped")

    def is_running(self) -> bool:
        """Check if the watcher is running."""
        return self._thread is not None and self._thread.is_alive()

    def _watch_loop(self, callback: Callable[[str], None]) -> None:
        """Main watch loop using native change count detection."""
        pasteboard = NSPasteboard.generalPasteboard()

        # Initialize with current change count
        self._last_change_count = pasteboard.changeCount()
        logger.debug(f"Initial change count: {self._last_change_count}")

        while not self._stop_event.is_set():
            try:
                # Check if clipboard has changed (very fast operation)
                current_change_count = pasteboard.changeCount()

                if current_change_count != self._last_change_count:
                    logger.debug(f"Clipboard change detected: {self._last_change_count} -> {current_change_count}")
                    self._last_change_count = current_change_count

                    # Get clipboard content
                    content = pasteboard.stringForType_("public.utf8-plain-text")

                    if content and len(content) <= self.max_size:
                        # Compute hash to avoid duplicate processing
                        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

                        if content_hash != self._last_hash:
                            self._last_hash = content_hash
                            logger.debug(f"New clipboard content ({len(content)} chars)")

                            # Call the callback
                            callback(content)
                        else:
                            logger.debug("Content hash unchanged, skipping")
                    elif content and len(content) > self.max_size:
                        logger.debug(f"Clipboard content too large ({len(content)} > {self.max_size}), skipping")

            except Exception as e:
                logger.error(f"Error in native clipboard watcher: {e}", exc_info=True)

            # Very short sleep since we're only checking an integer
            self._stop_event.wait(self.check_interval)
