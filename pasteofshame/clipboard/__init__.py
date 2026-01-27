"""Clipboard monitoring functionality."""

from pasteofshame.clipboard.base import ClipboardWatcher
from pasteofshame.clipboard.polling import PollingClipboardWatcher

__all__ = ["ClipboardWatcher", "PollingClipboardWatcher"]
