"""Base clipboard watcher interface."""

from abc import ABC, abstractmethod
from typing import Callable


class ClipboardWatcher(ABC):
    """Abstract base class for clipboard watchers."""

    @abstractmethod
    def start(self, callback: Callable[[str], None]) -> None:
        """
        Start watching the clipboard.

        Args:
            callback: Function to call with new clipboard content
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop watching the clipboard."""
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Check if the watcher is currently running."""
        pass
