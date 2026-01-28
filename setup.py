"""
Setup script for building Paste of Shame as a macOS application.

Usage:
    python setup.py py2app
"""

import os
import sys


# Monkey-patch py2app to handle built-in modules without __file__ attribute
def patch_py2app():
    """Patch py2app to skip built-in modules that don't have __file__."""
    try:
        from py2app import build_app

        original_copy_file = build_app.py2app.copy_file

        def patched_copy_file(self, src, dst):
            """Patched copy_file that handles missing __file__ attributes and files."""
            try:
                # Check if source file actually exists
                if not os.path.exists(src):
                    print(f"⚠️  Skipping non-existent file: {src}")
                    return None
                return original_copy_file(self, src, dst)
            except (AttributeError, FileNotFoundError, OSError) as e:
                if "'__file__'" in str(e) or "zlib" in str(src).lower():
                    # Skip built-in modules without __file__ or missing zlib
                    print(f"⚠️  Skipping built-in/missing module: {src}")
                    return None
                raise

        build_app.py2app.copy_file = patched_copy_file

        # Also patch build_executable to handle zlib specifically
        original_build_executable = build_app.py2app.build_executable

        def patched_build_executable(self, target, arcname, pkgexts, copyexts, script, extra_scripts):
            """Patched build_executable that skips zlib."""
            # Temporarily mock zlib.__file__ if it doesn't exist
            import zlib

            zlib_had_file = hasattr(zlib, "__file__")
            if not zlib_had_file:
                # Point to a dummy location - won't actually be used
                zlib.__file__ = os.path.join(sys.prefix, "lib", "zlib.so")

            try:
                result = original_build_executable(self, target, arcname, pkgexts, copyexts, script, extra_scripts)
            finally:
                if not zlib_had_file and hasattr(zlib, "__file__"):
                    delattr(zlib, "__file__")

            return result

        build_app.py2app.build_executable = patched_build_executable
        print("✅ Applied py2app compatibility patches")

    except ImportError:
        print("⚠️  py2app not available yet, skipping patch")
    except Exception as e:
        print(f"⚠️  Could not apply py2app patches: {e}")


# Apply patch before importing setup
patch_py2app()

from setuptools import setup

APP = ["pasteofshame/app/macos_app.py"]
DATA_FILES = [
    ("pasteofshame/core/patterns", ["pasteofshame/core/patterns/builtin.yml"]),
    ("resources", ["resources/icon.icns"]),
]
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "resources/icon.icns",
    "semi_standalone": False,  # Create fully standalone app
    "site_packages": True,  # Include site-packages
    "strip": True,  # Strip debug symbols to reduce size
    "optimize": 2,  # Optimize Python bytecode
    "compressed": False,  # Disable compression to avoid zlib issues (Python 3.10+)
    "plist": {
        "CFBundleName": "Paste of Shame",
        "CFBundleDisplayName": "Paste of Shame",
        "CFBundleIdentifier": "com.pasteofshame.app",
        "CFBundleVersion": "0.1.0",
        "CFBundleShortVersionString": "0.1.0",
        "LSUIElement": True,  # Run as agent (no dock icon, menu bar only)
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "10.15.0",  # Catalina+ for Python 3.13
        "LSApplicationCategoryType": "public.app-category.utilities",
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
    "excludes": [
        "tkinter",
        "test",
        "unittest",
        "distutils",
        "setuptools",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "PIL",
        "wx",
    ],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
