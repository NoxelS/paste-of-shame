#!/bin/bash
# Create a minimal icon using macOS tools

ICONSET="resources/icon.iconset"
mkdir -p "$ICONSET"

# Create simple PNG files with colored squares
for size in 16 32 128 256 512; do
  # Use sips to create basic images from a system icon
  sips -z $size $size /System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/GenericQuestionMarkIcon.icns --out "$ICONSET/icon_${size}x${size}.png" 2>/dev/null
done

# Convert to icns
iconutil -c icns "$ICONSET" -o resources/icon.icns 2>/dev/null

# Clean up
rm -rf "$ICONSET"

echo "Icon created at resources/icon.icns"
