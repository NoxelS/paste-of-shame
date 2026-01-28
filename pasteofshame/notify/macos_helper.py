"""macOS notification helper that uses the app bundle's icon."""

import subprocess
from pathlib import Path


def send_notification_with_app_icon(title: str, message: str) -> bool:
    """
    Send a macOS notification using the app's icon.

    This works by finding the app bundle and using its identifier
    to ensure notifications show with the correct icon.

    Args:
        title: Notification title
        message: Notification message

    Returns:
        True if notification was sent successfully, False otherwise
    """
    # Find the app bundle if running from one
    app_bundle = _find_app_bundle()

    if not app_bundle:
        # Not running from bundle, use standard osascript
        return _send_osascript_notification(title, message)

    # Use the executable inside the bundle to send notification
    # This ensures the notification is attributed to our app
    python_exe = _find_python_in_bundle(app_bundle)

    if python_exe:
        # Run osascript through the bundle's Python
        return _send_notification_from_bundle(python_exe, title, message)
    else:
        # Fallback to standard osascript
        return _send_osascript_notification(title, message)


def _find_app_bundle() -> Path | None:
    """Find the .app bundle we're running from, if any."""
    current = Path(__file__).resolve()

    # Walk up looking for .app directory
    for parent in current.parents:
        if parent.suffix == ".app":
            return parent

    return None


def _find_python_in_bundle(bundle: Path) -> Path | None:
    """Find the Python executable inside the app bundle."""
    # py2app puts the Python executable here
    python_exe = bundle / "Contents" / "MacOS" / "python"

    if python_exe.exists():
        return python_exe

    # Try alternative location
    python_exe = bundle / "Contents" / "MacOS" / "Paste of Shame"
    if python_exe.exists():
        return python_exe

    return None


def _send_notification_from_bundle(python_exe: Path, title: str, message: str) -> bool:
    """Send notification using the bundle's executable."""
    escaped_message = message.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")
    escaped_title = title.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")

    # Create a small Python script that sends the notification
    # This way it runs as part of the app bundle process
    script = f"""
import subprocess
script = 'display notification "{escaped_message}" with title "{escaped_title}" sound name "Basso"'
subprocess.run(["osascript", "-e", script], check=False)
"""

    try:
        result = subprocess.run(
            [str(python_exe), "-c", script],
            check=False,
            capture_output=True,
            timeout=5,
        )
    except Exception:
        return False

    return result.returncode == 0


def _send_osascript_notification(title: str, message: str) -> bool:
    """Send notification using plain osascript (fallback)."""
    escaped_message = message.replace("\\", "\\\\").replace('"', '\\"')
    escaped_title = title.replace("\\", "\\\\").replace('"', '\\"')

    script = f'display notification "{escaped_message}" with title "{escaped_title}" sound name "Basso"'

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            check=False,
            capture_output=True,
            timeout=5,
        )
    except Exception:
        return False

    return result.returncode == 0
