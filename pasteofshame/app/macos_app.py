#!/usr/bin/env python3
"""macOS menu bar application for Paste of Shame."""

import logging
import queue
import subprocess
import sys
import threading

# macOS-specific imports
try:
    import rumps  # type: ignore[import-untyped,import-not-found]
except ImportError:
    print("Error: rumps not installed. Install with: uv sync --group macos-app")
    sys.exit(1)

from pasteofshame.app.config import Config
from pasteofshame.app.daemon import Daemon
from pasteofshame.core.rules import RulePack

# Configure logging to file for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("/tmp/paste-of-shame.log"), logging.StreamHandler()],  # noqa: S108
)
logger = logging.getLogger(__name__)

# Icon states
ICON_IDLE = "🫥"
ICON_WATCHING = "🔎"


class PasteOfShameApp(rumps.App):
    """macOS menu bar application for Paste of Shame."""

    def __init__(self) -> None:
        """Initialize the menu bar app."""
        logger.info("🚀 Initializing Paste of Shame menu bar app")
        super().__init__(
            "Paste of Shame",
            icon=None,
            quit_button=None,
        )

        # Initialize state
        self.daemon: Daemon | None = None
        self.daemon_thread: threading.Thread | None = None
        self.is_running = False
        self.title = ICON_IDLE

        # Queue for notifications from daemon thread
        self.notification_queue: queue.Queue[tuple[str, str, bool]] = queue.Queue()
        logger.debug("Notification queue created")

        # Ensure config exists
        self._ensure_config_exists()
        self.config = Config.load()
        logger.info(f"Config loaded: threshold={self.config.threshold}, notify_enabled={self.config.notify_enabled}")

        # Create menu items
        self._create_menu_items()

        # Auto-start if configured
        if self.config.notify_enabled:
            logger.info("Auto-starting daemon (notify_enabled=True)")
            self._start_daemon()
            self.is_running = True
            self.title = ICON_WATCHING

        # Build initial menu
        self._update_menu()

        # Start timer to check notification queue
        logger.info("Starting notification timer (0.5s interval)")
        self.notification_timer = rumps.Timer(self._check_notifications, 0.5)
        self.notification_timer.start()
        logger.info("Menu bar app initialized successfully")

        # Request notification permissions on first launch
        self._request_notification_permissions()

    def _request_notification_permissions(self) -> None:
        """Request notification permissions by sending a welcome notification on first launch."""

        # Check if this is the first launch by looking for a marker file
        first_launch_marker = Config.get_config_path().parent / ".first_launch_done"

        if not first_launch_marker.exists():
            logger.info("First launch detected, requesting notification permissions")

            # Send a welcome notification - this triggers macOS to ask for permission
            try:
                rumps.notification(
                    title="Paste of Shame",
                    subtitle="Welcome! 👋",
                    message="Notifications are enabled. You'll be alerted when LLM boilerplate is detected in your clipboard.",
                    sound=False,
                )
                logger.info("Welcome notification sent (this triggers permission request)")

                # Mark first launch as complete
                first_launch_marker.touch()
                logger.info("First launch marker created")

            except Exception as e:
                logger.error(f"Failed to send welcome notification: {e}", exc_info=True)
        else:
            logger.debug("Not first launch, skipping welcome notification")

    def _ensure_config_exists(self) -> None:
        """Ensure config directory and file exist."""
        config_path = Config.get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        if not config_path.exists():
            # Create default config
            config = Config.load()
            config.save()

    def _create_menu_items(self) -> None:
        """Create persistent menu items."""
        self.start_item = rumps.MenuItem("Start Watching", callback=self.start_watching)
        self.stop_item = rumps.MenuItem("Stop Watching", callback=self.stop_watching)
        self.watching_item = rumps.MenuItem("● Watching...", callback=None)
        self.preferences_item = rumps.MenuItem("Preferences...", callback=self.show_preferences)
        self.reload_item = rumps.MenuItem("Reload Config", callback=self.reload_config)
        self.test_notification_item = rumps.MenuItem("Test Notification", callback=self.test_notification)
        self.toggle_sound_item = rumps.MenuItem("", callback=self.toggle_notification_sound)
        self.about_item = rumps.MenuItem("About", callback=self.show_about)
        self.quit_item = rumps.MenuItem("Quit", callback=self.quit_app)

    def quit_app(self, _: rumps.MenuItem) -> None:
        """Quit the application gracefully."""
        # Stop the notification timer
        if hasattr(self, "notification_timer"):
            self.notification_timer.stop()

        # Stop the daemon
        if self.is_running:
            self._stop_daemon()

        # Quit
        rumps.quit_application()

    def _update_menu(self) -> None:
        """Update the menu based on current state."""
        self.menu.clear()

        # Add control items based on state
        if self.is_running:
            self.menu.add(self.watching_item)
            self.menu.add(rumps.separator)
            self.menu.add(self.stop_item)
        else:
            self.menu.add(self.start_item)

        # Add configuration items
        self.menu.add(rumps.separator)
        self.menu.add(self._create_threshold_menu())

        # Update toggle sound item text based on current state
        sound_status = "🔊 On" if self.config.notify_sound else "🔇 Off"
        self.toggle_sound_item.title = f"Notification Sound: {sound_status}"

        self.menu.add(self.toggle_sound_item)
        self.menu.add(rumps.separator)
        self.menu.add(self.preferences_item)
        self.menu.add(self.reload_item)
        self.menu.add(self.test_notification_item)
        self.menu.add(rumps.separator)
        self.menu.add(self.about_item)
        self.menu.add(rumps.separator)
        self.menu.add(self.quit_item)

    def _create_threshold_menu(self) -> rumps.MenuItem:
        """Create threshold submenu with adjustable values."""
        threshold_menu = rumps.MenuItem(f"Threshold: {self.config.threshold}")

        # Common threshold values
        for value in [1, 2, 3, 5, 8, 10, 15, 20, 30, 40, 50, 60]:
            checkmark = "  ✓" if abs(self.config.threshold - value) < 0.01 else ""
            item = rumps.MenuItem(
                f"{value}{checkmark}",
                callback=lambda sender, val=value: self.set_threshold(val),
            )
            threshold_menu.add(item)

        return threshold_menu

    def _start_daemon(self) -> None:
        """Start the daemon in background thread."""
        logger.info("Starting daemon...")
        rule_pack = RulePack.builtin()

        # Provide a callback that queues notifications for the main thread
        def queue_notification(title: str, message: str, sound: bool) -> None:
            """Queue notification to be sent from main thread."""
            logger.info(f"📮 Queueing notification: {title} - {message}, sound={sound}")
            self.notification_queue.put((title, message, sound))
            logger.debug(f"Queue size after put: {self.notification_queue.qsize()}")

        self.daemon = Daemon(self.config, rule_pack, notification_callback=queue_notification)
        self.daemon_thread = threading.Thread(target=self.daemon.start, daemon=True)
        self.daemon_thread.start()
        logger.info("Daemon thread started")

    def _check_notifications(self, _: rumps.Timer) -> None:
        """Check notification queue and send any pending notifications (runs on main thread)."""
        try:
            while True:
                title, message, sound = self.notification_queue.get_nowait()
                logger.info(f"📬 Dequeued notification: {title} - {message}, sound={sound}")
                # Send notification using rumps (uses app's icon)
                try:
                    rumps.notification(
                        title="Paste of Shame",
                        subtitle=title,
                        message=message,
                        sound=sound,
                    )
                    logger.info("✅ Notification sent successfully via rumps")
                except Exception as e:
                    logger.error(f"❌ Failed to send rumps notification: {e}", exc_info=True)
        except queue.Empty:
            # No notifications pending, this is normal
            pass
        except Exception as e:
            logger.error(f"Error checking notification queue: {e}", exc_info=True)

    def _stop_daemon(self) -> None:
        """Stop the daemon if running."""
        logger.info("Stopping daemon...")
        if self.daemon:
            self.daemon.stop()
            self.daemon = None
            self.daemon_thread = None
            logger.info("Daemon stopped")

    def _restart_daemon(self) -> None:
        """Restart the daemon with current config."""
        logger.info("Restarting daemon...")
        if self.is_running:
            self._stop_daemon()
            self._start_daemon()

    def start_watching(self, _: rumps.MenuItem) -> None:
        """Start watching the clipboard."""
        logger.info("Start watching clicked")
        if self.is_running:
            logger.warning("Already running, showing alert")
            rumps.alert("Already Running", "Paste of Shame is already watching the clipboard.")
            return

        try:
            self._start_daemon()
            self.is_running = True
            self.title = ICON_WATCHING
            self._update_menu()
            logger.info("Started watching, showing notification")

            rumps.notification(
                title="Paste of Shame",
                subtitle="Started",
                message="Now watching clipboard for LLM boilerplate",
                sound=True,
            )
        except Exception as e:
            rumps.alert("Error", f"Failed to start watching: {e}")

    def stop_watching(self, _: rumps.MenuItem) -> None:
        """Stop watching the clipboard."""
        if not self.is_running:
            rumps.alert("Not Running", "Paste of Shame is not currently watching.")
            return

        self._stop_daemon()
        self.is_running = False
        self.title = ICON_IDLE
        self._update_menu()

        rumps.notification(
            title="Paste of Shame",
            subtitle="Stopped",
            message="Clipboard watching stopped",
        )

    def show_preferences(self, _: rumps.MenuItem) -> None:
        """Open config file in default editor."""
        config_path = Config.get_config_path()

        try:
            subprocess.run(["/usr/bin/open", str(config_path)], check=True)

            rumps.notification(
                title="Paste of Shame",
                subtitle="Config Opened",
                message="Remember to reload config after saving changes",
            )
        except subprocess.CalledProcessError as e:
            rumps.alert("Error Opening Config", f"Could not open config file.\n\nLocation: {config_path}\n\nError: {e}")

    def set_threshold(self, value: float) -> None:
        """Set the detection threshold."""
        self.config.threshold = int(value)
        self.config.save()
        self._update_menu()

        rumps.notification(
            title="Paste of Shame",
            subtitle="Threshold Updated",
            message=f"Detection threshold set to {value}",
        )

        # Restart daemon if running
        self._restart_daemon()

    def reload_config(self, _: rumps.MenuItem) -> None:
        """Reload configuration from disk."""
        try:
            self.config = Config.load()
            self._update_menu()
            self._restart_daemon()

            rumps.notification(
                title="Paste of Shame",
                subtitle="Config Reloaded",
                message="Configuration reloaded successfully",
            )
        except Exception as e:
            rumps.alert("Error", f"Failed to reload config: {e}")

    def show_about(self, _: rumps.MenuItem) -> None:
        """Show about dialog."""
        message = (
            "Paste of Shame v0.0.1\n\n"
            "Clipboard watchdog for detecting LLM-generated boilerplate.\n\n"
            "Uses deterministic pattern matching to detect common\n"
            "AI-generated phrases and boilerplate text.\n\n"
            "https://github.com/NoxelS/paste-of-shame"
        )
        rumps.alert("About Paste of Shame", message)

    def test_notification(self, _: rumps.MenuItem) -> None:
        """Send a test notification to verify permissions are working."""
        logger.info("Test notification requested")
        try:
            rumps.notification(
                title="Paste of Shame",
                subtitle="Test Notification ✅",
                message="If you see this, notifications are working correctly!",
                sound=True,
            )
            logger.info("Test notification sent successfully")
        except Exception as e:
            logger.error(f"Failed to send test notification: {e}", exc_info=True)
            rumps.alert(
                "Notification Error",
                f"Failed to send notification.\n\n"
                f"Please check System Settings > Notifications\n"
                f"and ensure 'Paste of Shame' has permission.\n\n"
                f"Error: {e}",
            )

    def toggle_notification_sound(self, _: rumps.MenuItem) -> None:
        """Toggle notification sound on/off."""
        self.config.notify_sound = not self.config.notify_sound
        self.config.save()
        self._update_menu()

        status = "enabled" if self.config.notify_sound else "disabled"
        logger.info(f"Notification sound {status}")

        rumps.notification(
            title="Paste of Shame",
            subtitle=f"Sound {status.capitalize()}",
            message=f"Notification sounds are now {status}",
            sound=self.config.notify_sound,  # Demonstrate the new setting
        )


def main() -> None:
    """Main entry point for the macOS app."""
    # Ensure config directory exists
    config_path = Config.get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Start the app
    app = PasteOfShameApp()
    app.run()


if __name__ == "__main__":
    main()
