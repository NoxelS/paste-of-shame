#!/usr/bin/env python3
"""
Generate a simple icon for Paste of Shame macOS app.
Creates an icns file from the warning emoji.
"""

import subprocess
from pathlib import Path


def create_icon() -> None:
    """Create an icon for the macOS app."""
    resources_dir = Path(__file__).parent
    iconset_dir = resources_dir / "icon.iconset"
    icon_file = resources_dir / "icon.icns"

    # Create iconset directory
    iconset_dir.mkdir(exist_ok=True)

    # For a simple approach, we'll create a text-based icon using ImageMagick
    # If ImageMagick is not available, we'll create a minimal icon
    try:
        # Create base image with emoji/text
        sizes = [16, 32, 64, 128, 256, 512, 1024]

        for size in sizes:
            output_file = iconset_dir / f"icon_{size}x{size}.png"
            output_file_2x = iconset_dir / f"icon_{size}x{size}@2x.png"

            # Create with ImageMagick
            cmd = [
                "convert",
                "-size",
                f"{size}x{size}",
                "xc:white",
                "-font",
                "AppleColorEmoji",
                "-pointsize",
                str(int(size * 0.8)),
                "-fill",
                "red",
                "-gravity",
                "center",
                "-annotate",
                "+0+0",
                "⚠️",
                str(output_file),
            ]

            try:
                subprocess.run(cmd, check=True, capture_output=True)
                print(f"Created {output_file.name}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback: create with sips (macOS built-in)
                create_simple_icon(output_file, size)

            # Create 2x version
            if size < 512:
                size_2x = size * 2
                cmd_2x = [
                    "convert",
                    "-size",
                    f"{size_2x}x{size_2x}",
                    "xc:white",
                    "-font",
                    "AppleColorEmoji",
                    "-pointsize",
                    str(int(size_2x * 0.8)),
                    "-fill",
                    "red",
                    "-gravity",
                    "center",
                    "-annotate",
                    "+0+0",
                    "⚠️",
                    str(output_file_2x),
                ]
                try:
                    subprocess.run(cmd_2x, check=True, capture_output=True)
                    print(f"Created {output_file_2x.name}")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    create_simple_icon(output_file_2x, size_2x)

        # Convert iconset to icns
        subprocess.run(["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icon_file)], check=True)
        print(f"\n✓ Created {icon_file}")

        # Clean up iconset
        subprocess.run(["rm", "-rf", str(iconset_dir)], check=False)

    except Exception as e:
        print(f"Warning: Could not create icon: {e}")
        print("A default icon will be used.")


def create_simple_icon(output_file: Path, size: int) -> None:
    """Create a simple colored square icon as fallback."""
    try:
        # Create a simple red square with sips
        cmd = [
            "sips",
            "-z",
            str(size),
            str(size),
            "--setProperty",
            "format",
            "png",
            "/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/AlertCautionIcon.icns",
            "--out",
            str(output_file),
        ]
        subprocess.run(cmd, check=False, capture_output=True)
        print(f"Created fallback icon: {output_file.name}")
    except Exception:
        pass


if __name__ == "__main__":
    create_icon()
