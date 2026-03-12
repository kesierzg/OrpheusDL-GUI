# OrpheusDL-GUI Installer System

Cross-platform installer for OrpheusDL-GUI with module selection.

## Platforms

| Platform | Installer Type | Tool |
|----------|---------------|------|
| Windows  | .exe installer | Inno Setup |
| macOS    | .dmg with drag-to-Applications | create-dmg |
| Linux    | AppImage | appimagetool |

## Build Process

### Prerequisites

1. Python 3.10+
2. PyInstaller
3. Platform-specific tools (see below)

### Windows

```bash
# Install Inno Setup from https://jrsoftware.org/isinfo.php
# Build the installer
python installer/build_installer.py --platform windows
```

### macOS

```bash
# Install create-dmg
brew install create-dmg
# Build the installer
python3 installer/build_installer.py --platform macos
```

### Linux

```bash
# Install required dependencies
sudo apt install python3-venv python3-tk binutils

# Install appimagetool
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
# Build the installer
python installer/build_installer.py --platform linux --format all
```

Supported formats:
- `appimage`: Universal AppImage (default)
- `deb`: Debian/Ubuntu/Mint package
- `rpm`: Fedora/RHEL package
- `arch`: Arch Linux PKGBUILD
- `all`: Build all available formats

#### Troubleshooting

If you encounter `dlopen(): error loading libfuse.so.2` when running the AppImage on Ubuntu 22.04+:
1.  **Install libfuse2:** `sudo apt install libfuse2`
2.  **Or use the .deb package:** The `.deb` package does not require FUSE.

## Module Selection

During installation, users can select which music platform modules to install:

- Apple Music
- Beatport
- Beatsource
- Deezer
- Qobuz
- SoundCloud
- Spotify
- Tidal
- YouTube

## Directory Structure

```
installer/
├── README.md
├── build_installer.py      # Main build script
├── windows/
│   ├── installer.iss       # Inno Setup script
│   └── assets/             # Windows-specific assets
├── macos/
│   ├── create_dmg.sh       # DMG creation script
│   └── assets/             # macOS-specific assets
├── linux/
│   ├── AppDir/             # AppImage directory structure
│   └── orpheusdl.desktop   # Desktop entry file
└── modules/                # Module packages for selection
```

## Features

- [x] Cross-platform support
- [x] Module selection during install
- [x] Desktop shortcut creation
- [x] All dependencies bundled
- [x] Auto-update support (optional)

