#!/bin/bash
# Install Paste of Shame as a login item using LaunchAgent
# This allows the app to start automatically when the user logs in

set -e

APP_NAME="Paste of Shame"
BUNDLE_ID="com.pasteofshame.app"
LAUNCH_AGENT_NAME="${BUNDLE_ID}.plist"
LAUNCH_AGENT_DIR="${HOME}/Library/LaunchAgents"
LAUNCH_AGENT_PATH="${LAUNCH_AGENT_DIR}/${LAUNCH_AGENT_NAME}"
APP_PATH="/Applications/${APP_NAME}.app"

echo "🚀 Installing ${APP_NAME} as Login Item..."

# Check if app exists
if [ ! -d "${APP_PATH}" ]; then
    echo "❌ Error: ${APP_NAME}.app not found in /Applications"
    echo "   Please install the app first by copying it to /Applications"
    exit 1
fi

# Create LaunchAgents directory if it doesn't exist
mkdir -p "${LAUNCH_AGENT_DIR}"

# Create the LaunchAgent plist
cat > "${LAUNCH_AGENT_PATH}" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${BUNDLE_ID}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/open</string>
        <string>-a</string>
        <string>${APP_PATH}</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <false/>
    
    <key>ProcessType</key>
    <string>Interactive</string>
    
    <key>StandardOutPath</key>
    <string>${HOME}/Library/Logs/${BUNDLE_ID}.log</string>
    
    <key>StandardErrorPath</key>
    <string>${HOME}/Library/Logs/${BUNDLE_ID}.error.log</string>
</dict>
</plist>
EOF

# Set proper permissions
chmod 644 "${LAUNCH_AGENT_PATH}"

# Load the LaunchAgent (start it now)
launchctl load "${LAUNCH_AGENT_PATH}" 2>/dev/null || true

echo "✅ ${APP_NAME} has been installed as a Login Item"
echo ""
echo "The app will now:"
echo "  • Start automatically when you log in"
echo "  • Run in the background (menu bar only)"
echo ""
echo "To uninstall auto-start, run:"
echo "  ./scripts/uninstall_autostart.sh"
echo ""
echo "Or manually remove:"
echo "  ${LAUNCH_AGENT_PATH}"
