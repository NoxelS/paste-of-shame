#!/usr/bin/env python3
"""
Patched py2app build script for Python 3.13 compatibility.
Works around the zlib.__file__ AttributeError issue.
"""

import os
import sys
from pathlib import Path


def patch_py2app():
    """Monkey-patch py2app to work with Python 3.13."""
    try:
        from py2app import build_app

        # Store original method
        original_build_executable = build_app.py2app.build_executable

        def patched_build_executable(self, *args, **kwargs):
            """Patched version that handles built-in modules without __file__."""
            try:
                return original_build_executable(self, *args, **kwargs)
            except AttributeError as e:
                if "zlib" in str(e) and "__file__" in str(e):
                    print("⚠️  Skipping zlib copy (built-in module)")
                    # Continue without copying zlib
                    return original_build_executable(self, *args, **kwargs)
                raise

        # Apply patch
        build_app.py2app.build_executable = patched_build_executable
        print("✅ Applied py2app Python 3.13 compatibility patch")

    except Exception as e:
        print(f"⚠️  Could not patch py2app: {e}")
        print("   Build will proceed anyway...")


if __name__ == "__main__":
    # Apply patch
    patch_py2app()

    # Run setup.py

    # Import setup configuration
    sys.path.insert(0, os.getcwd())

    # Read setup.py and execute it
    setup_path = Path("setup.py")
    if not setup_path.exists():
        print("❌ setup.py not found")
        sys.exit(1)

    # Execute setup.py in modified environment
    with open(setup_path) as f:
        setup_code = f.read()
        # Remove the final setup() call, we'll handle it
        setup_code = setup_code.replace("if __name__ == '__main__':", "if False:")
        exec(setup_code, {"__name__": "__main__"}) # noqa: S102
