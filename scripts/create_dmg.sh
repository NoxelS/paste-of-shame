#!/bin/bash
# Script to create a DMG installer for Paste of Shame

set -e

APP_NAME="Paste of Shame"
DMG_NAME="Paste-of-Shame"

# Extract version from pyproject.toml
if [ -f "pyproject.toml" ]; then
    VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
    echo "📌 Detected version: ${VERSION}"
else
    VERSION="0.1.2"
    echo "⚠️  Warning: Could not find pyproject.toml, using default version ${VERSION}"
fi

APP_PATH="dist/${APP_NAME}.app"
DMG_PATH="dist/${DMG_NAME}-${VERSION}-macOS.dmg"
VOLUME_NAME="${APP_NAME} ${VERSION}"
TEMP_DMG="dist/temp.dmg"
ICON_FILE="resources/icon.icns"

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
╔══════════════════════════════════════════════════════════════╗
║  Paste of Shame - Clipboard Watchdog for LLM Boilerplate   ║
╚══════════════════════════════════════════════════════════════╝

📦 INSTALLATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Drag "Paste of Shame.app" → "Applications" folder
2. Open "Paste of Shame" from Applications or Spotlight (⌘+Space)
3. The app will appear in your menu bar (🫥 or 🔎 icon)
4. Click the icon and select "Start Watching"

✅ That's it! You'll now get notified when LLM boilerplate
   is detected in your clipboard.


🚀 AUTO-START ON LOGIN (Optional but Recommended)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Make Paste of Shame launch automatically when you log in.

┌─────────────────────────────────────────────────────────────┐
│ METHOD 1: System Settings (Easiest) ⭐                      │
└─────────────────────────────────────────────────────────────┘
  1. Open System Settings → General → Login Items
  2. Click the "+" button under "Open at Login"
  3. Select "Paste of Shame" from Applications
  4. Done! ✅ App will start automatically on every login

┌─────────────────────────────────────────────────────────────┐
│ METHOD 2: Terminal Command (For Developers)                 │
└─────────────────────────────────────────────────────────────┘
  If you have the source repository cloned:

  To enable auto-start:
    cd /path/to/paste-of-shame
    make install-launchagent

  To disable auto-start:
    make uninstall-launchagent

  Manual verification:
    launchctl list | grep pasteofshame


⚙️ FEATURES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ Real-time clipboard monitoring (zero performance impact)
  ✓ Detects 25+ common LLM phrases and patterns
  ✓ Smart suppression for quoted text and code blocks
  ✓ Adjustable sensitivity threshold (1-60)
  ✓ Native macOS notifications with sound toggle
  ✓ Menu bar controls for quick access
  ✓ Privacy-first: 100% local, no network, no AI models


🎛️ MENU BAR CONTROLS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🟢 Start/Stop watching
  🎚️ Adjust detection threshold
  🔇 Toggle notification sound
  ⚙️ Open config file
  🔄 Reload configuration
  🧪 Test notifications


📚 DOCUMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  GitHub: https://github.com/NoxelS/paste-of-shame
  Issues: https://github.com/NoxelS/paste-of-shame/issues


💡 TIPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Set threshold to 10-15 for sensitive detection
  • Set threshold to 30-40 for less frequent alerts
  • Use "Test Notification" to verify permissions
  • Config file: ~/.config/pasteofshame/config.yml


Need help? Found a bug? Open an issue on GitHub! 🐛
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
