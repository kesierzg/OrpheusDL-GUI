#!/bin/bash
# Build Linux AppImage for OrpheusDL-GUI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
APP_NAME="OrpheusDL_GUI"
VERSION="${1:-1.0.0}"
ARCH="x86_64"

echo "=== Building Linux AppImage ==="
echo "Version: $VERSION"
echo "Architecture: $ARCH"

# Check for appimagetool
APPIMAGETOOL=""
if command -v appimagetool &> /dev/null; then
    APPIMAGETOOL="appimagetool"
elif [ -f "$SCRIPT_DIR/appimagetool-$ARCH.AppImage" ]; then
    APPIMAGETOOL="$SCRIPT_DIR/appimagetool-$ARCH.AppImage"
else
    echo "appimagetool not found. Downloading..."
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-$ARCH.AppImage" \
        -O "$SCRIPT_DIR/appimagetool-$ARCH.AppImage"
    chmod +x "$SCRIPT_DIR/appimagetool-$ARCH.AppImage"
    APPIMAGETOOL="$SCRIPT_DIR/appimagetool-$ARCH.AppImage"
fi

# Check for executable
EXE_PATH="$DIST_DIR/$APP_NAME"
if [ ! -f "$EXE_PATH" ]; then
    echo "Error: Executable not found at $EXE_PATH"
    echo "Run PyInstaller first: pyinstaller --onefile gui.spec"
    exit 1
fi

# Create AppDir structure
APPDIR="$DIST_DIR/${APP_NAME}.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APPDIR/usr/share/metainfo"

# Copy executable
echo "Copying executable..."
cp "$EXE_PATH" "$APPDIR/usr/bin/$APP_NAME"
chmod +x "$APPDIR/usr/bin/$APP_NAME"

# Copy modules if they exist
if [ -d "$DIST_DIR/modules" ]; then
    echo "Copying modules..."
    cp -r "$DIST_DIR/modules" "$APPDIR/usr/bin/"
fi

# Copy config if it exists
if [ -d "$DIST_DIR/config" ]; then
    echo "Copying config..."
    cp -r "$DIST_DIR/config" "$APPDIR/usr/bin/"
fi

# Copy icon
if [ -f "$PROJECT_ROOT/icon.png" ]; then
    cp "$PROJECT_ROOT/icon.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/com.github.orpheusdl.orpheusdl-gui.png"
    cp "$PROJECT_ROOT/icon.png" "$APPDIR/com.github.orpheusdl.orpheusdl-gui.png"
fi

# Copy desktop file and AppStream metadata
echo "Copying metadata files..."
cp "$SCRIPT_DIR/com.github.orpheusdl.orpheusdl-gui.desktop" "$APPDIR/usr/share/applications/com.github.orpheusdl.orpheusdl-gui.desktop"
cp "$SCRIPT_DIR/com.github.orpheusdl.orpheusdl-gui.desktop" "$APPDIR/com.github.orpheusdl.orpheusdl-gui.desktop"
cp "$SCRIPT_DIR/com.github.orpheusdl.orpheusdl-gui.appdata.xml" "$APPDIR/usr/share/metainfo/com.github.orpheusdl.orpheusdl-gui.appdata.xml"
cp "$SCRIPT_DIR/com.github.orpheusdl.orpheusdl-gui.appdata.xml" "$APPDIR/usr/share/metainfo/com.github.orpheusdl.orpheusdl-gui.metainfo.xml"
cp "$SCRIPT_DIR/com.github.orpheusdl.orpheusdl-gui.appdata.xml" "$APPDIR/usr/share/metainfo/com.github.orpheusdl.orpheusdl-gui.desktop.metainfo.xml"

# Create AppRun
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
APPDIR="$(dirname "$(readlink -f "$0")")"
export PATH="$APPDIR/usr/bin:$PATH"
export LD_LIBRARY_PATH="$APPDIR/usr/lib:$LD_LIBRARY_PATH"
exec "$APPDIR/usr/bin/OrpheusDL_GUI" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Build AppImage
echo "Building AppImage..."
APPIMAGE_PATH="$DIST_DIR/${APP_NAME}-${VERSION}-${ARCH}.AppImage"
rm -f "$APPIMAGE_PATH"

ARCH=$ARCH "$APPIMAGETOOL" "$APPDIR" "$APPIMAGE_PATH"

echo ""
echo "=== AppImage Created Successfully ==="
echo "Output: $APPIMAGE_PATH"
echo ""

if [ -f "$APPIMAGE_PATH" ]; then
    ls -lh "$APPIMAGE_PATH"
    chmod +x "$APPIMAGE_PATH"
else
    echo "Error: AppImage creation failed"
    exit 1
fi

