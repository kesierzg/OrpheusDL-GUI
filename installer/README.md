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
python installer/build_installer.py --platform macos
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

**Running the AppImage requires FUSE 2 (`libfuse.so.2`).**

AppImage (type 2) needs FUSE 2 to mount and run. Older distros shipped it by default, but newer
ones ship FUSE 3 only (e.g. Ubuntu 25.10+, Kubuntu 26.04, recent Fedora), so end users must
install the FUSE 2 compatibility package. Symptom: `dlopen(): error loading libfuse.so.2` (or the
GUI not starting at all).

- **Debian/Ubuntu/Kubuntu/Mint:** `sudo apt install libfuse2`
- **Fedora/RHEL:** `sudo dnf install fuse-libs`
- **Arch:** `sudo pacman -S fuse2`
- **Alternative:** use the `.deb`/`.rpm` package instead — these do not require FUSE.
- **Alternative:** run the AppImage without FUSE by extracting it:
  `./OrpheusDL_GUI-x86_64.AppImage --appimage-extract-and-run`

## Module Selection

During installation, users can select which music platform modules to install:

- Amazon Music
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

