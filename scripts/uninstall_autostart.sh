#!/bin/bash
# Uninstall Paste of Shame from login items

set -e

BUNDLE_ID="com.pasteofshame.app"
LAUNCH_AGENT_NAME="${BUNDLE_ID}.plist"
LAUNCH_AGENT_DIR="${HOME}/Library/LaunchAgents"
LAUNCH_AGENT_PATH="${LAUNCH_AGENT_DIR}/${LAUNCH_AGENT_NAME}"

echo "🗑️  Removing Paste of Shame from Login Items..."

if [ -f "${LAUNCH_AGENT_PATH}" ]; then
    # Unload the LaunchAgent
    launchctl unload "${LAUNCH_AGENT_PATH}" 2>/dev/null || true
    
    # Remove the plist file
    rm -f "${LAUNCH_AGENT_PATH}"
    
    echo "✅ Auto-start has been disabled"
    echo "   The app will no longer launch automatically on login"
else
    echo "ℹ️  Auto-start was not configured"
fi
