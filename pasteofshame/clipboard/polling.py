"""Polling-based clipboard watcher implementation."""

import hashlib
from collections.abc import Callable
from threading import Event, Thread

import pyperclip  # type: ignore[import-untyped]

from pasteofshame.clipboard.base import ClipboardWatcher


class PollingClipboardWatcher(ClipboardWatcher):
    """Clipboard watcher using polling with adaptive backoff."""

    def __init__(
        self,
        initial_interval: float = 0.3,
        max_interval: float = 2.0,
        max_size: int = 200_000,
    ) -> None:
        """
        Initialize the polling watcher.

        Args:
            initial_interval: Initial polling interval in seconds
            max_interval: Maximum polling interval (backoff limit)
            max_size: Maximum clipboard content size to process (characters)
        """
        self.initial_interval = initial_interval
        self.max_interval = max_interval
        self.max_size = max_size
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._last_hash: str | None = None

    def start(self, callback: Callable[[str], None]) -> None:
        """Start watching the clipboard in a background thread."""
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = Thread(target=self._watch_loop, args=(callback,), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop watching the clipboard."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

    def is_running(self) -> bool:
        """Check if the watcher is running."""
        return self._thread is not None and self._thread.is_alive()

    def _watch_loop(self, callback: Callable[[str], None]) -> None:
        """Main watch loop running in background thread."""
        current_interval = self.initial_interval
        consecutive_unchanged = 0

        while not self._stop_event.is_set():
            try:
                # Get clipboard content
                content = pyperclip.paste()

                # Check if content is valid and not too large
                if content and len(content) <= self.max_size:
                    # Compute hash to detect changes
                    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

                    if content_hash != self._last_hash:
                        # New content detected
                        self._last_hash = content_hash
                        consecutive_unchanged = 0
                        current_interval = self.initial_interval

                        # Call the callback
                        callback(content)
                    else:
                        # Content unchanged, increase backoff
                        consecutive_unchanged += 1
                        if consecutive_unchanged > 3:
                            current_interval = min(current_interval * 1.5, self.max_interval)

            except Exception:
                # Silently ignore clipboard access errors
                pass

            # Wait before next poll
            self._stop_event.wait(current_interval)
