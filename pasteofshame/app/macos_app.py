#!/usr/bin/env python3
"""macOS menu bar application for Paste of Shame."""

import subprocess
import sys
import threading
from pathlib import Path

# macOS-specific imports
try:
    import rumps  # type: ignore[import-untyped,import-not-found]
except ImportError:
    print("Error: rumps not installed. Install with: uv sync --group macos-app")
    sys.exit(1)

from pasteofshame.app.config import Config
from pasteofshame.app.daemon import Daemon
from pasteofshame.core.rules import RulePack


# Icon states
ICON_IDLE = "🫥"
ICON_WATCHING = "🔎"


class PasteOfShameApp(rumps.App):
    """macOS menu bar application for Paste of Shame."""

    def __init__(self) -> None:
        """Initialize the menu bar app."""
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

        # Ensure config exists
        self._ensure_config_exists()
        self.config = Config.load()

        # Create menu items
        self._create_menu_items()

        # Auto-start if configured
        if self.config.notify_enabled:
            self._start_daemon()
            self.is_running = True
            self.title = ICON_WATCHING

        # Build initial menu
        self._update_menu()

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
        self.about_item = rumps.MenuItem("About", callback=self.show_about)
        self.quit_item = rumps.MenuItem("Quit", callback=rumps.quit_application)

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
        self.menu.add(rumps.separator)
        self.menu.add(self.preferences_item)
        self.menu.add(self.reload_item)
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
        rule_pack = RulePack.builtin()
        self.daemon = Daemon(self.config, rule_pack)
        self.daemon_thread = threading.Thread(target=self.daemon.start, daemon=True)
        self.daemon_thread.start()

    def _stop_daemon(self) -> None:
        """Stop the daemon if running."""
        if self.daemon:
            self.daemon.stop()
            self.daemon = None
            self.daemon_thread = None

    def _restart_daemon(self) -> None:
        """Restart the daemon with current config."""
        if self.is_running:
            self._stop_daemon()
            self._start_daemon()

    def start_watching(self, _: rumps.MenuItem) -> None:
        """Start watching the clipboard."""
        if self.is_running:
            rumps.alert("Already Running", "Paste of Shame is already watching the clipboard.")
            return

        try:
            self._start_daemon()
            self.is_running = True
            self.title = ICON_WATCHING
            self._update_menu()

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
            subprocess.run(["/usr/bin/open", str(config_path)], check=True)  # noqa: S603
            
            rumps.notification(
                title="Paste of Shame",
                subtitle="Config Opened",
                message="Remember to reload config after saving changes",
            )
        except subprocess.CalledProcessError as e:
            rumps.alert(
                "Error Opening Config",
                f"Could not open config file.\n\nLocation: {config_path}\n\nError: {e}"
            )

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
