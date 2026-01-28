#!/usr/bin/env python3
"""
macOS menu bar application for Paste of Shame.
Runs as a background agent with system tray icon.
"""

import sys
import threading

# macOS-specific imports
try:
    import rumps  # type: ignore[import-untyped,import-not-found]
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
            quit_button=None,  # We'll add it manually to control position
        )

        # Ensure config directory exists and load config
        config_path = Config.get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load config (creates default if doesn't exist)
        self.config = Config.load()
        
        # If config file doesn't exist, create it with defaults
        if not config_path.exists():
            self.config.save()
        
        self.daemon: Daemon | None = None
        self.daemon_thread: threading.Thread | None = None
        self.is_running = False

        # Set title to show in menu bar
        self.title = "🫥"

        # Create persistent menu items (created once, reused)
        self.start_watching_item = rumps.MenuItem("Start Watching", callback=self.start_watching)
        self.stop_watching_item = rumps.MenuItem("Stop Watching", callback=self.stop_watching)
        self.watching_status_item = rumps.MenuItem("Watching...", callback=None)
        self.statistics_item = rumps.MenuItem("Statistics", callback=self.show_stats)
        self.preferences_item = rumps.MenuItem("Preferences...", callback=self.show_preferences)
        self.reload_config_item = rumps.MenuItem("Reload Config", callback=self.reload_config)
        self.about_item = rumps.MenuItem("About", callback=self.show_about)
        self.quit_item = rumps.MenuItem("Quit", callback=rumps.quit_application)

        # Auto-start if configured (before building menu)
        if self.config.notify_enabled:
            # Start watching without calling _update_menu yet
            rule_pack = RulePack.builtin()
            self.daemon = Daemon(self.config, rule_pack)
            self.daemon_thread = threading.Thread(target=self.daemon.start, daemon=True)
            self.daemon_thread.start()
            self.is_running = True
            self.title = "🔎"

        # Build initial menu (will reflect correct state now)
        self._update_menu()

    def _update_menu(self) -> None:
        """Update the menu based on current state."""
        # Clear all menu items
        self.menu.clear()
        
        # Add status/control items based on state
        if self.is_running:
            self.menu.add(self.watching_status_item)
            self.menu.add(rumps.separator)
            self.menu.add(self.stop_watching_item)
        else:
            self.menu.add(self.start_watching_item)

        # Add separator and other items
        self.menu.add(rumps.separator)
        self.menu.add(self.statistics_item)
        self.menu.add(self.preferences_item)
        self.menu.add(self.reload_config_item)
        self.menu.add(rumps.separator)
        self.menu.add(self._create_threshold_menu())
        self.menu.add(rumps.separator)
        self.menu.add(self.about_item)
        self.menu.add(rumps.separator)
        self.menu.add(self.quit_item)

    def _create_threshold_menu(self) -> rumps.MenuItem:
        """Create threshold submenu with adjustable values."""
        threshold_menu = rumps.MenuItem(f"Threshold: {self.config.threshold}")

        # Common threshold values
        threshold_values = [1, 2, 3, 5, 8, 10, 15, 20, 30, 40, 50, 60]

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
            self.title = "🔎"  # Change title when active
            self._update_menu()  # Update menu to reflect new state

        except Exception as e:
            rumps.alert("Error", f"Failed to start watching: {e}")

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

    def stop_watching(self, _: rumps.MenuItem) -> None:
        """Stop watching the clipboard."""
        if not self.is_running:
            rumps.alert("Not Running", "Paste of Shame is not currently watching.")
            return

        if self.daemon:
            self.daemon.stop()
            self.daemon = None

        self.is_running = False
        self.title = "🫥"
        self._update_menu()  # Update menu to reflect new state

        rumps.notification(
            title="Paste of Shame",
            subtitle="Stopped",
            message="Clipboard watching stopped",
        )

    def show_stats(self, _: rumps.MenuItem) -> None:
        """Show detection statistics."""
        if not self.daemon:
            rumps.alert("Statistics", "No statistics available. Start watching first.")
            return

        warned_count = len(self.daemon._warned_hashes)
        message = f"Unique warnings issued: {warned_count}\nThreshold: {self.config.threshold}"

        rumps.alert("Statistics", message)

    def show_preferences(self, _: rumps.MenuItem) -> None:
        """Show preferences dialog and open config file in default editor."""
        config_path = Config.get_config_path()
        
        # Build message with current settings
        settings_text = (
            f"Config file: {config_path}\n\n"
            f"Current Settings:\n"
            f"• Threshold: {self.config.threshold}\n"
            f"• Poll Interval: {self.config.poll_interval}s\n"
            f"• Max Poll Interval: {self.config.max_poll_interval}s\n"
            f"• Cooldown: {self.config.cooldown_seconds}s\n"
            f"• Max Clipboard Size: {self.config.max_clipboard_size:,} chars\n"
            f"• Languages: {', '.join(self.config.enabled_languages)}\n"
            f"• Notifications: {'Enabled' if self.config.notify_enabled else 'Disabled'}\n\n"
            f"Click 'Edit Config' to open in your default editor"
        )

        # Show options
        response = rumps.alert(
            "Preferences",
            settings_text,
            ok="Edit Config",
            cancel="Close",
        )

        if response == 1:  # Edit Config
            self._open_config_file()

    def _open_config_file(self) -> None:
        """Open config file in default editor."""
        config_path = Config.get_config_path()
        import subprocess
        
        try:
            # Use open command to open with default editor
            subprocess.run(["/usr/bin/open", str(config_path)], check=True)  # noqa: S603
            
            # Show reminder to reload config after editing
            rumps.notification(
                title="Paste of Shame",
                subtitle="Config Opened",
                message="Remember to use 'Reload Config' after saving changes",
            )
        except subprocess.CalledProcessError as e:
            rumps.alert(
                "Cannot Open File",
                f"Could not open config file.\n\nLocation: {config_path}\n\nError: {e}"
            )

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
