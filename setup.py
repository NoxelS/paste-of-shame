"""
Setup script for building Paste of Shame as a macOS application.

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['pasteofshame/app/macos_app.py']
DATA_FILES = [
    ("pasteofshame/core/patterns", ["pasteofshame/core/patterns/builtin.yml"]),
]
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "resources/icon.icns",
    "semi_standalone": False,  # Create fully standalone app
    "site_packages": True,  # Include site-packages
    "strip": True,  # Strip debug symbols to reduce size
    "optimize": 2,  # Optimize Python bytecode
    "plist": {
        "CFBundleName": "Paste of Shame",
        "CFBundleDisplayName": "Paste of Shame",
        "CFBundleIdentifier": "com.pasteofshame.app",
        "CFBundleVersion": "0.0.1",
        "CFBundleShortVersionString": "0.0.1",
        "LSUIElement": True,  # Run as agent (no dock icon, menu bar only)
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "10.13.0",
    },
    "packages": ["pasteofshame", "yaml", "pyperclip", "click", "rumps"],
    "includes": [
        "pasteofshame",
        "pasteofshame.core",
        "pasteofshame.core.types",
        "pasteofshame.core.rules",
        "pasteofshame.core.detector",
        "pasteofshame.core.scoring",
        "pasteofshame.clipboard",
        "pasteofshame.clipboard.base",
        "pasteofshame.clipboard.polling",
        "pasteofshame.notify",
        "pasteofshame.notify.notifier",
        "pasteofshame.app",
        "pasteofshame.app.config",
        "pasteofshame.app.daemon",
    ],
    "excludes": ["tkinter", "test", "unittest", "distutils", "setuptools"],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
