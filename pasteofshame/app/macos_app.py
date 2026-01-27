#!/usr/bin/env python3
"""
macOS menu bar application for Paste of Shame.
Runs as a background agent with system tray icon.
"""

import sys
import threading

# macOS-specific imports
try:
    import rumps  # type: ignore[import-untyped]
except ImportError:
    print("Error: rumps not installed. Install with: pip install rumps")
    sys.exit(1)

from pasteofshame.app.config import Config
from pasteofshame.app.daemon import Daemon
from pasteofshame.core.rules import RulePack


class PasteOfShameApp(rumps.App):
    """macOS menu bar application for Paste of Shame."""

    def __init__(self) -> None:
        """Initialize the menu bar app."""
        super().__init__(
            "Paste of Shame",
            icon=None,  # Use text-based icon initially
            quit_button="Quit",
        )

        # Load config
        self.config = Config.load()
        self.daemon: Daemon | None = None
        self.daemon_thread: threading.Thread | None = None
        self.is_running = False

        # Set title to show in menu bar
        self.title = "⚠️"

        # Create menu items that we'll update dynamically
        self.start_watching_item = rumps.MenuItem("Start Watching", callback=self.start_watching)
        self.stop_watching_item = rumps.MenuItem("Stop Watching", callback=self.stop_watching)
        self.watching_status_item = rumps.MenuItem("Watching...", callback=None)

        # Build menu
        self._update_menu()

        # Auto-start if configured
        if self.config.notify_enabled:
            self.start_watching_internal()

    def _update_menu(self) -> None:
        """Update the menu based on current state."""
        menu_items = []

        # Add status if watching
        if self.is_running:
            menu_items.append(self.watching_status_item)
            menu_items.append(None)  # Separator
            menu_items.append(self.stop_watching_item)
        else:
            menu_items.append(self.start_watching_item)

        menu_items.extend([
            None,  # Separator
            rumps.MenuItem("Statistics", callback=self.show_stats),
            rumps.MenuItem("Preferences...", callback=self.show_preferences),
            rumps.MenuItem("Reload Config", callback=self.reload_config),
            None,  # Separator
            self._create_threshold_menu(),
            None,  # Separator
            rumps.MenuItem("About", callback=self.show_about),
        ])

        self.menu.clear()
        for item in menu_items:
            if item is not None:
                self.menu.add(item)
            else:
                self.menu.add(rumps.separator)

    def _create_threshold_menu(self) -> rumps.MenuItem:
        """Create threshold submenu with adjustable values."""
        threshold_menu = rumps.MenuItem(f"Threshold: {self.config.threshold}")

        # Common threshold values
        threshold_values = [0, 5, 10, 15, 20, 40, 60]

        for value in threshold_values:
            item = rumps.MenuItem(
                f"{value}{'  ✓' if abs(self.config.threshold - value) < 0.01 else ''}",
                callback=lambda sender, val=value: self.set_threshold(val),
            )
            threshold_menu.add(item)

        return threshold_menu

    def start_watching_internal(self) -> None:
        """Start the clipboard watcher (internal)."""
        if self.is_running:
            return

        try:
            # Create daemon
            rule_pack = RulePack.builtin()
            self.daemon = Daemon(self.config, rule_pack)

            # Start in background thread
            self.daemon_thread = threading.Thread(target=self.daemon.start, daemon=True)
            self.daemon_thread.start()

            self.is_running = True
            self.title = "🔍"  # Change title when active
            self._update_menu()  # Update menu to reflect new state

        except Exception as e:
            rumps.alert("Error", f"Failed to start watching: {e}")

    @rumps.clicked("Start Watching")
    def start_watching(self, _: rumps.MenuItem) -> None:
        """Start watching the clipboard."""
        if self.is_running:
            rumps.alert("Already Running", "Paste of Shame is already watching the clipboard.")
            return

        self.start_watching_internal()
        rumps.notification(
            title="Paste of Shame",
            subtitle="Started",
            message="Now watching clipboard for LLM boilerplate",
            sound=True,
        )

    @rumps.clicked("Stop Watching")
    def stop_watching(self, _: rumps.MenuItem) -> None:
        """Stop watching the clipboard."""
        if not self.is_running:
            rumps.alert("Not Running", "Paste of Shame is not currently watching.")
            return

        if self.daemon:
            self.daemon.stop()
            self.daemon = None

        self.is_running = False
        self.title = "⚠️"
        self._update_menu()  # Update menu to reflect new state

        rumps.notification(
            title="Paste of Shame",
            subtitle="Stopped",
            message="Clipboard watching stopped",
        )

    @rumps.clicked("Statistics")
    def show_stats(self, _: rumps.MenuItem) -> None:
        """Show detection statistics."""
        if not self.daemon:
            rumps.alert("Statistics", "No statistics available. Start watching first.")
            return

        warned_count = len(self.daemon._warned_hashes)
        message = f"Unique warnings issued: {warned_count}\nThreshold: {self.config.threshold}"

        rumps.alert("Statistics", message)

    @rumps.clicked("Preferences...")
    def show_preferences(self, _: rumps.MenuItem) -> None:
        """Show preferences dialog."""
        config_path = Config.get_config_path()
        message = f"Config file: {config_path}\n\nEdit this file to change settings."

        if rumps.alert(
            "Preferences",
            message,
            ok="Open Config Folder",
            cancel="Close",
        ):
            # Open config folder in Finder
            import subprocess

            subprocess.run(["open", str(config_path.parent)], check=False)  # noqa: S603, S607

    def set_threshold(self, value: float) -> None:
        """Set the detection threshold."""
        self.config.threshold = int(value)
        self.config.save()

        # Update menu to show new threshold
        self._update_menu()

        # Show confirmation
        rumps.notification(
            title="Paste of Shame",
            subtitle="Threshold Updated",
            message=f"Detection threshold set to {value}",
        )

        # Restart daemon if running to apply new threshold
        if self.is_running:
            # Stop and restart silently
            if self.daemon:
                self.daemon.stop()
                self.daemon = None

            rule_pack = RulePack.builtin()
            self.daemon = Daemon(self.config, rule_pack)
            self.daemon_thread = threading.Thread(target=self.daemon.start, daemon=True)
            self.daemon_thread.start()

    def reload_config(self, _: rumps.MenuItem) -> None:
        """Reload configuration from disk."""
        try:
            self.config = Config.load()
            self._update_menu()

            # Restart daemon if running to apply new config
            if self.is_running:
                if self.daemon:
                    self.daemon.stop()
                    self.daemon = None

                rule_pack = RulePack.builtin()
                self.daemon = Daemon(self.config, rule_pack)
                self.daemon_thread = threading.Thread(target=self.daemon.start, daemon=True)
                self.daemon_thread.start()

            rumps.notification(
                title="Paste of Shame",
                subtitle="Config Reloaded",
                message="Configuration reloaded successfully",
            )
        except Exception as e:
            rumps.alert("Error", f"Failed to reload config: {e}")

    @rumps.clicked("About")
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
