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
    cp "$PROJECT_ROOT/icon.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/orpheusdl-gui.png"
    cp "$PROJECT_ROOT/icon.png" "$APPDIR/orpheusdl-gui.png"
fi

# Create desktop file
cat > "$APPDIR/usr/share/applications/orpheusdl-gui.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=OrpheusDL GUI
Comment=Music Downloader GUI
Exec=OrpheusDL_GUI %U
Icon=orpheusdl-gui
Terminal=false
Categories=AudioVideo;Audio;Music;
Keywords=music;download;spotify;tidal;deezer;qobuz;
StartupWMClass=OrpheusDL-GUI
EOF

# Copy desktop file to root
cp "$APPDIR/usr/share/applications/orpheusdl-gui.desktop" "$APPDIR/orpheusdl-gui.desktop"

# Create AppStream metadata
cat > "$APPDIR/usr/share/metainfo/orpheusdl-gui.appdata.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>com.orpheusdl.gui</id>
  <name>OrpheusDL-GUI</name>
  <summary>Music Downloader GUI</summary>
  <description>
    <p>
      OrpheusDL-GUI is a graphical interface for downloading music from various 
      streaming platforms including Spotify, Tidal, Deezer, Qobuz, and more.
    </p>
  </description>
  <launchable type="desktop-id">orpheusdl-gui.desktop</launchable>
  <url type="homepage">https://github.com/orpheusdl/orpheusdl-gui</url>
  <provides>
    <binary>OrpheusDL_GUI</binary>
  </provides>
  <releases>
    <release version="$VERSION" date="$(date +%Y-%m-%d)"/>
  </releases>
  <content_rating type="oars-1.1"/>
</component>
EOF

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

