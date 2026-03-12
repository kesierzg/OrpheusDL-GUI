#!/bin/bash
# Create macOS DMG installer for OrpheusDL-GUI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
APP_NAME="OrpheusDL_GUI"
DMG_NAME="OrpheusDL_GUI-Installer"
VERSION="${1:-1.0.0}"

echo "=== Creating macOS DMG Installer ==="
echo "Version: $VERSION"
echo "Project root: $PROJECT_ROOT"

# Check for required tools
if ! command -v create-dmg &> /dev/null; then
    echo "Error: create-dmg not found."
    echo "Install with: brew install create-dmg"
    exit 1
fi

# Check for app bundle
APP_PATH="$DIST_DIR/${APP_NAME}.app"
if [ ! -d "$APP_PATH" ]; then
    echo "Error: App bundle not found at $APP_PATH"
    echo "Run PyInstaller first: pyinstaller gui.spec"
    exit 1
fi

# Remove old DMG if exists
DMG_PATH="$DIST_DIR/${DMG_NAME}-${VERSION}.dmg"
rm -f "$DMG_PATH"

# Create DMG
echo "Creating DMG..."
create-dmg \
    --volname "OrpheusDL-GUI $VERSION" \
    --volicon "$PROJECT_ROOT/icon.icns" \
    --window-pos 200 120 \
    --window-size 660 400 \
    --icon-size 100 \
    --icon "$APP_NAME.app" 180 190 \
    --hide-extension "$APP_NAME.app" \
    --app-drop-link 480 190 \
    --background "$SCRIPT_DIR/assets/dmg-background.png" \
    "$DMG_PATH" \
    "$APP_PATH" \
    2>/dev/null || true  # create-dmg returns non-zero if no background image

# Fallback without background if the above failed
if [ ! -f "$DMG_PATH" ]; then
    echo "Creating DMG without custom background..."
    create-dmg \
        --volname "OrpheusDL-GUI $VERSION" \
        --volicon "$PROJECT_ROOT/icon.icns" \
        --window-pos 200 120 \
        --window-size 660 400 \
        --icon-size 100 \
        --icon "$APP_NAME.app" 180 190 \
        --hide-extension "$APP_NAME.app" \
        --app-drop-link 480 190 \
        "$DMG_PATH" \
        "$APP_PATH"
fi

echo ""
echo "=== DMG Created Successfully ==="
echo "Output: $DMG_PATH"
echo ""

# Verify
if [ -f "$DMG_PATH" ]; then
    ls -lh "$DMG_PATH"
else
    echo "Error: DMG creation failed"
    exit 1
fi

