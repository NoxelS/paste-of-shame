"""Cross-platform notification system."""

import os
import platform
import subprocess
import sys
from typing import Any

from pasteofshame.core.types import ScanResult


class Notifier:
    """Cross-platform desktop and terminal notifier."""

    def __init__(self, desktop_enabled: bool = True, verbose: bool = True) -> None:
        """
        Initialize the notifier.

        Args:
            desktop_enabled: Whether to attempt desktop notifications
            verbose: Whether to print to stdout
        """
        self.desktop_enabled = desktop_enabled
        self.verbose = verbose
        self.system = platform.system()

    def notify(self, result: ScanResult) -> None:
        """
        Send notification for a scan result.

        Args:
            result: ScanResult to notify about
        """
        if not result.is_warning:
            return

        # Always print to stdout in verbose mode
        if self.verbose:
            self._print_terminal(result)

        # Try desktop notification if enabled
        if self.desktop_enabled:
            self._send_desktop_notification(result)

    def _print_terminal(self, result: ScanResult) -> None:
        """Print warning to terminal."""
        print("\n" + "=" * 60)
        print("⚠️  LLM BOILERPLATE DETECTED")
        print("=" * 60)
        print(f"Score: {result.total_score}")

        if result.suppression_applied:
            print(f"Suppression: {result.suppression_reason}")

        top_matches = result.top_matches(3)
        if top_matches:
            print(f"\nTop {len(top_matches)} matches:")
            for i, match in enumerate(top_matches, 1):
                severity = match.rule.severity.value
                print(f"\n{i}. {match.rule.description} (weight: {match.rule.weight}, severity: {severity})")
                if match.excerpts:
                    excerpt = match.excerpts[0]
                    print(f'   "{excerpt}"')

        print("\n💡 Suggestion: Review and remove boilerplate before sharing.")
        print("=" * 60 + "\n")
        sys.stdout.flush()

    def _send_desktop_notification(self, result: ScanResult) -> None:
        """Send desktop notification (best-effort)."""
        title = "🫣⁉️ Shameful Paste Ahead"
        message = f"Score: {result.total_score} - Review clipboard content before sharing."

        try:
            if self.system == "Darwin":  # macOS
                self._notify_macos(title, message)
            elif self.system == "Linux":
                self._notify_linux(title, message)
            elif self.system == "Windows":
                self._notify_windows(title, message)
        except Exception as e:
            # Silently fail for desktop notifications (expected on some platforms)
            import logging

            logging.debug(f"Desktop notification error: {e}")

    def _notify_macos(self, title: str, message: str) -> None:
        """Send notification on macOS using osascript optimized for app bundles."""
        escaped_message = message.replace("\\", "\\\\").replace('"', '\\"')
        escaped_title = title.replace("\\", "\\\\").replace('"', '\\"')

        # Check if we're running from an app bundle
        app_bundle = self._get_app_bundle_path()

        if app_bundle:
            # Running from app bundle - use the bundle's executable to send notification
            # This ensures the notification uses the app's icon
            bundle_exe = os.path.join(app_bundle, "Contents", "MacOS", "Paste of Shame")

            if os.path.exists(bundle_exe):
                # Send notification through the bundle's main executable
                # This way macOS attributes it to our app
                script = f'display notification "{escaped_message}" with title "{escaped_title}" sound name "Basso"'

                # Use the bundle executable's directory as working directory
                # This helps macOS identify the notification source
                subprocess.run(
                    ["osascript", "-e", script],
                    check=False,
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(bundle_exe),
                )
                return

        # Fallback: standard osascript (for development/non-bundled)
        script = f'display notification "{escaped_message}" with title "{escaped_title}" sound name "Basso"'
        subprocess.run(["osascript", "-e", script], check=False, capture_output=True, text=True)

    def _get_app_bundle_path(self) -> str | None:
        """Get the path to the .app bundle if running from one."""
        import os

        # Get the current file's path
        current_path = os.path.abspath(__file__)

        # Walk up looking for .app directory
        parts = current_path.split(os.sep)
        for i in range(len(parts) - 1, -1, -1):
            if parts[i].endswith(".app"):
                return os.sep.join(parts[: i + 1])

        return None

    def _notify_linux(self, title: str, message: str) -> None:
        """Send notification on Linux using notify-send."""
        subprocess.run(["notify-send", title, message], check=False, capture_output=True)

    def _notify_windows(self, title: str, message: str) -> None:
        """Send notification on Windows (fallback to stdout)."""
        # Windows toast notifications require additional dependencies
        # Fall back to terminal output only
        pass

    def format_json(self, result: ScanResult) -> dict[str, Any]:
        """
        Format scan result as JSON-serializable dict.

        Args:
            result: ScanResult to format

        Returns:
            Dictionary with scan results
        """
        return {
            "total_score": result.total_score,
            "is_warning": result.is_warning,
            "suppression_applied": result.suppression_applied,
            "suppression_reason": result.suppression_reason,
            "matches": [
                {
                    "rule_id": match.rule.id,
                    "description": match.rule.description,
                    "weight": match.rule.weight,
                    "severity": match.rule.severity.value,
                    "count": len(match.spans),
                    "excerpts": match.excerpts[:3],  # Limit to 3 excerpts
                }
                for match in result.matches
            ],
        }
