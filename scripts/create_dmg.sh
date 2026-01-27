#!/bin/bash
# Script to create a DMG installer for Paste of Shame

set -e

APP_NAME="Paste of Shame"
DMG_NAME="Paste-of-Shame"
VERSION="0.0.1"
APP_PATH="dist/${APP_NAME}.app"
DMG_PATH="dist/${DMG_NAME}.dmg"
VOLUME_NAME="${APP_NAME} ${VERSION}"
TEMP_DMG="dist/temp.dmg"

echo "📦 Creating DMG installer for ${APP_NAME}..."

# Check if app exists
if [ ! -d "${APP_PATH}" ]; then
    echo "❌ Error: ${APP_PATH} not found. Run 'make build-app' first."
    exit 1
fi

# Remove old DMG if it exists
rm -f "${DMG_PATH}" "${TEMP_DMG}"

# Create temporary directory for DMG contents
STAGING_DIR=$(mktemp -d)
trap "rm -rf ${STAGING_DIR}" EXIT

echo "📂 Staging files..."
cp -R "${APP_PATH}" "${STAGING_DIR}/"

# Create Applications symlink for easy installation
ln -s /Applications "${STAGING_DIR}/Applications"

# Create a simple README
cat > "${STAGING_DIR}/README.txt" << 'EOF'
Paste of Shame - Clipboard Watchdog for LLM Boilerplate
========================================================

Installation:
1. Drag "Paste of Shame.app" to the Applications folder
2. Open "Paste of Shame" from Applications
3. The app will appear in your menu bar (⚠️ icon)
4. Click "Start Watching" to begin monitoring your clipboard

Optional Auto-Start:
To make Paste of Shame start automatically on login:
1. Open System Preferences > Users & Groups
2. Select your user and click "Login Items"
3. Click the "+" button and add "Paste of Shame" from Applications

Or use the command line:
  make install-launchagent

For more information:
https://github.com/NoxelS/paste-of-shame
EOF

# Calculate size for DMG
SIZE=$(du -sm "${STAGING_DIR}" | awk '{print $1}')
SIZE=$((SIZE + 10))  # Add 10MB padding

echo "💾 Creating DMG (${SIZE}MB)..."

# Create DMG
hdiutil create -srcfolder "${STAGING_DIR}" \
    -volname "${VOLUME_NAME}" \
    -fs HFS+ \
    -fsargs "-c c=64,a=16,e=16" \
    -format UDRW \
    -size ${SIZE}m \
    "${TEMP_DMG}"

# Mount it
echo "📌 Mounting DMG..."
DEVICE=$(hdiutil attach -readwrite -noverify -noautoopen "${TEMP_DMG}" | egrep '^/dev/' | sed 1q | awk '{print $1}')
MOUNT_POINT="/Volumes/${VOLUME_NAME}"

# Wait for mount
sleep 2

# Set DMG icon positions and appearance
echo "🎨 Configuring DMG appearance..."
cat > /tmp/dmg_setup.applescript << EOF
tell application "Finder"
    tell disk "${VOLUME_NAME}"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {100, 100, 600, 400}
        set viewOptions to the icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to 72
        set position of item "Paste of Shame.app" of container window to {100, 100}
        set position of item "Applications" of container window to {400, 100}
        set position of item "README.txt" of container window to {250, 250}
        update without registering applications
        delay 1
        close
    end tell
end tell
EOF

osascript /tmp/dmg_setup.applescript || echo "⚠️  Warning: Could not set DMG appearance"
rm /tmp/dmg_setup.applescript

# Unmount
echo "📤 Finalizing DMG..."
sync
hdiutil detach "${DEVICE}"

# Convert to compressed read-only
hdiutil convert "${TEMP_DMG}" \
    -format UDZO \
    -imagekey zlib-level=9 \
    -o "${DMG_PATH}"

# Clean up
rm -f "${TEMP_DMG}"

echo "✅ DMG created successfully: ${DMG_PATH}"
echo "📊 DMG size: $(du -h "${DMG_PATH}" | awk '{print $1}')"
