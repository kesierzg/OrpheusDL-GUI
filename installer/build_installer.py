#!/usr/bin/env python3
"""
OrpheusDL-GUI Installer Builder
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
import stat
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
INSTALLER_DIR = Path(__file__).parent
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"


AVAILABLE_MODULES = [
    "applemusic",
    "beatport",
    "beatsource",
    "deezer",
    "musixmatch",
    "qobuz",
    "soundcloud",
    "spotify",
    "tidal",
    "youtube",
]


MODULE_NAMES = {
    "applemusic": "Apple Music",
    "beatport": "Beatport",
    "beatsource": "Beatsource",
    "deezer": "Deezer",
    "musixmatch": "Musixmatch",
    "qobuz": "Qobuz",
    "soundcloud": "SoundCloud",
    "spotify": "Spotify",
    "tidal": "Tidal",
    "youtube": "YouTube",
}


def get_version():
    """Extract version from gui.py"""

    gui_path = PROJECT_ROOT / "gui.py"

    if not gui_path.exists():
        print("ERROR: gui.py not found")
        sys.exit(1)

    content = gui_path.read_text(encoding="utf-8")

    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)

    if not match:
        print("ERROR: __version__ not found in gui.py")
        sys.exit(1)

    return match.group(1)


def generate_version_iss():
    """Generate version.iss for Inno Setup"""

    version = get_version().lstrip("v")

    windows_dir = INSTALLER_DIR / "windows"
    windows_dir.mkdir(parents=True, exist_ok=True)

    version_file = windows_dir / "version.iss"

    version_file.write_text(
        f'#define MyAppVersion "{version}"\n',
        encoding="ascii"
    )

    print(f"Generated version.iss ({version})")


def get_available_modules():
    """Detect installed modules"""

    modules_dir = PROJECT_ROOT / "modules"
    available = []

    for module in AVAILABLE_MODULES:
        module_path = modules_dir / module

        if module_path.exists() and (module_path / "interface.py").exists():
            available.append(module)

    return available


def run_command(cmd, cwd=None, check=True, env=None):

    print("Running:", " ".join(cmd))

    if env:
        full_env = os.environ.copy()
        full_env.update(env)
    else:
        full_env = None

    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        env=full_env
    )

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr)

    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)

    return result


def build_pyinstaller():

    print("\n=== PyInstaller build ===")

    for d in [BUILD_DIR, DIST_DIR]:
        if d.exists():
            shutil.rmtree(d)

    run_command([
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        str(PROJECT_ROOT / "gui.spec")
    ], cwd=PROJECT_ROOT)

    print("PyInstaller build complete")


def build_windows_installer(modules=None):

    print("\n=== Windows installer ===")

    generate_version_iss()

    iss = INSTALLER_DIR / "windows" / "installer.iss"

    if not iss.exists():
        create_inno_setup_script(modules)

    inno = None

    for p in [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe"
    ]:
        if os.path.exists(p):
            inno = p
            break

    if not inno:
        print("ERROR: Inno Setup not installed")
        return False

    run_command([inno, str(iss)])

    print("Windows installer created")

    return True


def build_macos_installer(modules=None):
    """Build macOS DMG installer."""
    print("\n=== macOS installer ===")

    # Check for create-dmg
    result = subprocess.run(["which", "create-dmg"], capture_output=True)
    if result.returncode != 0:
        print("ERROR: create-dmg not found. Install with: brew install create-dmg")
        return False

    app_path = DIST_DIR / "OrpheusDL GUI.app"
    if not app_path.exists():
        print(f"ERROR: App not found at {app_path}")
        return False

    # Create DMG
    dmg_path = DIST_DIR / "OrpheusDL_GUI-Installer.dmg"
    run_command([
        "create-dmg",
        "--volname", "OrpheusDL GUI Installer",
        "--volicon", str(PROJECT_ROOT / "icon.icns"),
        "--window-pos", "200", "120",
        "--window-size", "600", "400",
        "--icon-size", "100",
        "--icon", "OrpheusDL GUI.app", "150", "190",
        "--hide-extension", "OrpheusDL GUI.app",
        "--app-drop-link", "450", "190",
        str(dmg_path),
        str(app_path)
    ])

    print(f"macOS installer created: {dmg_path}")
    return True


def build_linux_installer(modules=None):
    """Build Linux AppImage installer."""
    print("\n=== Linux AppImage ===")

    # Check for appimagetool
    appimagetool = shutil.which("appimagetool")
    if not appimagetool:
        local_tool = INSTALLER_DIR / "linux" / "appimagetool-x86_64.AppImage"
        if local_tool.exists():
            appimagetool = str(local_tool)
        else:
            print("appimagetool not found. Downloading...")
            url = "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
            try:
                urllib.request.urlretrieve(url, local_tool)
                os.chmod(local_tool, os.stat(local_tool).st_mode | stat.S_IEXEC)
                appimagetool = str(local_tool)
                print(f"Downloaded appimagetool to {local_tool}")
            except Exception as e:
                print(f"ERROR: Failed to download appimagetool: {e}")
                return False

    appdir = DIST_DIR / "OrpheusDL_GUI.AppDir"
    if appdir.exists():
        shutil.rmtree(appdir)

    appdir.mkdir(parents=True)
    (appdir / "usr" / "bin").mkdir(parents=True)
    (appdir / "usr" / "share" / "applications").mkdir(parents=True)
    (appdir / "usr" / "share" / "icons" / "hicolor" / "scalable" / "apps").mkdir(parents=True)
    (appdir / "usr" / "share" / "metainfo").mkdir(parents=True)

    exe_path = DIST_DIR / "OrpheusDL_GUI"
    if exe_path.exists():
        shutil.copy(exe_path, appdir / "usr" / "bin" / "OrpheusDL_GUI")

    # Use provided high-res icon if available
    linux_icon_src = INSTALLER_DIR / "linux" / "flathub-images" / "icon.png"
    if not linux_icon_src.exists():
        linux_icon_src = PROJECT_ROOT / "icon.png"

    if linux_icon_src.exists():
        (appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps").mkdir(parents=True, exist_ok=True)
        shutil.copy(linux_icon_src, appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps" / "com.github.orpheusdl.orpheusdl-gui.png")
        shutil.copy(linux_icon_src, appdir / "com.github.orpheusdl.orpheusdl-gui.png")
        shutil.copy(linux_icon_src, appdir / "orpheusdl-gui.png")

    icon_svg_path = PROJECT_ROOT / "icon.svg"
    if icon_svg_path.exists():
        shutil.copy(icon_svg_path, appdir / "usr" / "share" / "icons" / "hicolor" / "scalable" / "apps" / "com.github.orpheusdl.orpheusdl-gui.svg")
        shutil.copy(icon_svg_path, appdir / "com.github.orpheusdl.orpheusdl-gui.svg")

    desktop_src = INSTALLER_DIR / "linux" / "com.github.orpheusdl.orpheusdl-gui.desktop"
    if desktop_src.exists():
        shutil.copy(desktop_src, appdir / "usr" / "share" / "applications" / "com.github.orpheusdl.orpheusdl-gui.desktop")
        shutil.copy(desktop_src, appdir / "com.github.orpheusdl.orpheusdl-gui.desktop")
    else:
        # Fallback if desktop file is missing
        desktop_content = """[Desktop Entry]
Name=OrpheusDL GUI
Comment=Music Downloader GUI
Exec=OrpheusDL_GUI
Icon=com.github.orpheusdl.orpheusdl-gui
Type=Application
Categories=AudioVideo;Audio;
Terminal=false
"""
        (appdir / "usr" / "share" / "applications" / "com.github.orpheusdl.orpheusdl-gui.desktop").write_text(desktop_content)
        (appdir / "com.github.orpheusdl.orpheusdl-gui.desktop").write_text(desktop_content)

    appdata_src = INSTALLER_DIR / "linux" / "com.github.orpheusdl.orpheusdl-gui.appdata.xml"
    if appdata_src.exists():
        metainfo_dir = appdir / "usr" / "share" / "metainfo"
        shutil.copy(appdata_src, metainfo_dir / "com.github.orpheusdl.orpheusdl-gui.metainfo.xml")

    apprun_content = """#!/bin/bash
APPDIR="$(dirname "$(readlink -f "$0")")"
exec "$APPDIR/usr/bin/OrpheusDL_GUI" "$@"
"""
    apprun_path = appdir / "AppRun"
    apprun_path.write_text(apprun_content)
    apprun_path.chmod(0o755)

    appimage_path = DIST_DIR / "OrpheusDL_GUI-x86_64.AppImage"
    env = {"APPIMAGE_EXTRACT_AND_RUN": "1"}
    run_command([appimagetool, str(appdir), str(appimage_path)], env=env)

    print(f"Linux AppImage created: {appimage_path}")
    return True


def build_linux_deb(modules=None):
    """Build Debian/Ubuntu .deb package."""
    print("\n=== Debian package ===")

    if not shutil.which("dpkg-deb"):
        print("ERROR: dpkg-deb not found")
        return False

    version = get_version().lstrip('v')
    arch = "amd64"
    package_name = "orpheusdl-gui"

    deb_root = DIST_DIR / "deb_build" / package_name
    if deb_root.exists():
        shutil.rmtree(deb_root)

    (deb_root / "DEBIAN").mkdir(parents=True)
    (deb_root / "usr" / "bin").mkdir(parents=True)
    (deb_root / "usr" / "share" / "applications").mkdir(parents=True)
    (deb_root / "usr" / "share" / "icons" / "hicolor" / "scalable" / "apps").mkdir(parents=True)

    control_content = f"""Package: {package_name}
Version: {version}
Section: sound
Priority: optional
Architecture: {arch}
Depends: python3, ffmpeg
Maintainer: Bas Curtiz <bascurtiz@gmail.com>
Homepage: https://github.com/bascurtiz/OrpheusDL-GUI
Description: OrpheusDL GUI
 A cross-platform graphical user interface for OrpheusDL. Search & download across multiple music streaming services with ease.
"""
    (deb_root / "DEBIAN" / "control").write_text(control_content)

    appdata_src = INSTALLER_DIR / "linux" / "com.github.orpheusdl.orpheusdl-gui.appdata.xml"
    if appdata_src.exists():
        metainfo_dir = deb_root / "usr" / "share" / "metainfo"
        metainfo_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(appdata_src, metainfo_dir / "com.github.orpheusdl.orpheusdl-gui.metainfo.xml")

    # Generate copyright file
    license_src = PROJECT_ROOT / "LICENSE"
    if license_src.exists():
        doc_dir = deb_root / "usr" / "share" / "doc" / package_name
        doc_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(license_src, doc_dir / "copyright")

    exe_path = DIST_DIR / "OrpheusDL_GUI"
    if exe_path.exists():
        shutil.copy(exe_path, deb_root / "usr" / "bin" / "OrpheusDL_GUI")
        (deb_root / "usr" / "bin" / "OrpheusDL_GUI").chmod(0o755)

    # Use provided high-res icon if available
    linux_icon_src = INSTALLER_DIR / "linux" / "flathub-images" / "icon.png"
    if not linux_icon_src.exists():
        linux_icon_src = PROJECT_ROOT / "icon.png"

    if linux_icon_src.exists():
        (deb_root / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps").mkdir(parents=True, exist_ok=True)
        shutil.copy(linux_icon_src, deb_root / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps" / "com.github.orpheusdl.orpheusdl-gui.png")

    icon_svg_path = PROJECT_ROOT / "icon.svg"
    if icon_svg_path.exists():
        shutil.copy(icon_svg_path, deb_root / "usr" / "share" / "icons" / "hicolor" / "scalable" / "apps" / "com.github.orpheusdl.orpheusdl-gui.svg")

    desktop_src = INSTALLER_DIR / "linux" / "com.github.orpheusdl.orpheusdl-gui.desktop"
    if desktop_src.exists():
        shutil.copy(desktop_src, deb_root / "usr" / "share" / "applications" / "com.github.orpheusdl.orpheusdl-gui.desktop")
    else:
        desktop_content = f"""[Desktop Entry]
Name=OrpheusDL GUI
Comment=A cross-platform graphical user interface for OrpheusDL. Search & download across multiple music streaming services with ease.
Exec=OrpheusDL_GUI
Icon=com.github.orpheusdl.orpheusdl-gui
Type=Application
Categories=AudioVideo;Audio;
Terminal=false
StartupWMClass=OrpheusDL_GUI
"""
        (deb_root / "usr" / "share" / "applications" / "com.github.orpheusdl.orpheusdl-gui.desktop").write_text(desktop_content)

    deb_path = DIST_DIR / f"OrpheusDL_GUI-{version}-{arch}.deb"
    run_command(["dpkg-deb", "--build", str(deb_root), str(deb_path)])

    print(f"Debian package created: {deb_path}")
    return True


def build_linux_rpm(modules=None):
    """Build Fedora/RHEL .rpm package."""
    print("\n=== RPM package ===")

    if not shutil.which("rpmbuild"):
        print("ERROR: rpmbuild not found")
        return False

    version = get_version().lstrip('v')
    rpm_root = DIST_DIR / "rpm_build"
    if rpm_root.exists():
        shutil.rmtree(rpm_root)

    for d in ["BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS"]:
        (rpm_root / d).mkdir(parents=True)

    spec_content = f"""
Name:       orpheusdl-gui
Version:    {version}
Release:    1%{{?dist}}
Summary:    OrpheusDL GUI
License:    MIT
URL:        https://github.com/bascurtiz/orpheusdl-gui
BuildArch:  x86_64
Requires:   python3 ffmpeg

%description
A cross-platform graphical user interface for OrpheusDL. Search & download across multiple music streaming services with ease.

%install
mkdir -p %{{buildroot}}/usr/bin
mkdir -p %{{buildroot}}/usr/share/applications
mkdir -p %{{buildroot}}/usr/share/icons/hicolor/scalable/apps

cp {DIST_DIR}/OrpheusDL_GUI %{{buildroot}}/usr/bin/OrpheusDL_GUI
cp {INSTALLER_DIR}/linux/flathub-images/icon.png %{buildroot}/usr/share/icons/hicolor/256x256/apps/com.github.orpheusdl.orpheusdl-gui.png
mkdir -p %{buildroot}/usr/share/metainfo
cp {INSTALLER_DIR}/linux/com.github.orpheusdl.orpheusdl-gui.appdata.xml %{buildroot}/usr/share/metainfo/com.github.orpheusdl.orpheusdl-gui.appdata.xml
cp {INSTALLER_DIR}/linux/com.github.orpheusdl.orpheusdl-gui.appdata.xml %{buildroot}/usr/share/metainfo/com.github.orpheusdl.orpheusdl-gui.metainfo.xml

cat > %{buildroot}/usr/share/applications/com.github.orpheusdl.orpheusdl-gui.desktop <<EOF
[Desktop Entry]
Version=1.0
Name=OrpheusDL GUI
Comment=A cross-platform graphical user interface for OrpheusDL. Search & download across multiple music streaming services with ease.
Exec=OrpheusDL_GUI %U
Icon=com.github.orpheusdl.orpheusdl-gui
Type=Application
Categories=AudioVideo;Audio;Music;
Terminal=false
StartupWMClass=OrpheusDL_GUI
MimeType=x-scheme-handler/orpheusdl;
EOF

%files
/usr/bin/OrpheusDL_GUI
/usr/share/applications/com.github.orpheusdl.orpheusdl-gui.desktop
/usr/share/icons/hicolor/scalable/apps/com.github.orpheusdl.orpheusdl-gui.svg
/usr/share/icons/hicolor/256x256/apps/com.github.orpheusdl.orpheusdl-gui.png
/usr/share/metainfo/com.github.orpheusdl.orpheusdl-gui.appdata.xml
/usr/share/metainfo/com.github.orpheusdl.orpheusdl-gui.metainfo.xml

%changelog
* Thu Mar 12 2026 Bas Curtiz <bascurtiz@gmail.com> - {version}-1
- Updated metadata and icons
* Sat Jan 11 2025 Bas Curtiz <bascurtiz@gmail.com> - 1.0.8-1
- Initial release
"""
    spec_path = rpm_root / "SPECS" / "orpheusdl-gui.spec"
    spec_path.write_text(spec_content)

    run_command([
        "rpmbuild",
        "--define", f"_topdir {rpm_root}",
        "-bb", str(spec_path)
    ])

    built_rpm = list((rpm_root / "RPMS" / "x86_64").glob("*.rpm"))
    if built_rpm:
        shutil.copy(built_rpm[0], DIST_DIR / built_rpm[0].name)
        print(f"RPM package created: {DIST_DIR / built_rpm[0].name}")
        return True
    return False


def build_arch_pkgbuild(modules=None):
    """Prepare Arch Linux PKGBUILD."""
    print("\n=== Arch Linux PKGBUILD ===")

    version = get_version().lstrip('v')

    arch_root = DIST_DIR / "arch_build"
    if not DIST_DIR.exists():
        DIST_DIR.mkdir(parents=True)
    if arch_root.exists():
        shutil.rmtree(arch_root)
    arch_root.mkdir(parents=True)

    exe_path = DIST_DIR / "OrpheusDL_GUI"
    if exe_path.exists():
        shutil.copy(exe_path, arch_root / "OrpheusDL_GUI")

    icon_path = PROJECT_ROOT / "icon.svg"
    if icon_path.exists():
        shutil.copy(icon_path, arch_root / "icon.svg")

    appdata_src = INSTALLER_DIR / "linux" / "com.github.orpheusdl.orpheusdl-gui.appdata.xml"
    if appdata_src.exists():
        shutil.copy(appdata_src, arch_root / "appdata.xml")

    pkgbuild_content = f"""# Maintainer: Bas Curtiz <bascurtiz@gmail.com>
pkgname=orpheusdl-gui
pkgver={version}
pkgrel=1
pkgdesc="OrpheusDL GUI"
arch=('x86_64')
url="https://github.com/bascurtiz/orpheusdl-gui"
license=('MIT')
depends=('python' 'ffmpeg')
# Long description: A cross-platform graphical user interface for OrpheusDL. Search & download across multiple music streaming services with ease.
source=("OrpheusDL_GUI"
        "icon.svg"
        "appdata.xml")
sha256sums=('SKIP' 'SKIP' 'SKIP')

package() {{
    install -Dm755 "$srcdir/OrpheusDL_GUI" "$pkgdir/usr/bin/OrpheusDL_GUI"
    install -Dm644 "$srcdir/icon.svg" "$pkgdir/usr/share/icons/hicolor/scalable/apps/com.github.orpheusdl.orpheusdl-gui.svg"
    install -Dm644 "$srcdir/appdata.xml" "$pkgdir/usr/share/metainfo/com.github.orpheusdl.orpheusdl-gui.appdata.xml"

    install -d "$pkgdir/usr/share/applications"
    cat > "$pkgdir/usr/share/applications/com.github.orpheusdl.orpheusdl-gui.desktop" <<EOF
[Desktop Entry]
Version=1.0
Name=OrpheusDL GUI
Comment=A cross-platform graphical user interface for OrpheusDL. Search & download across multiple music streaming services with ease.
Exec=OrpheusDL_GUI %U
Icon=com.github.orpheusdl.orpheusdl-gui
Type=Application
Categories=AudioVideo;Audio;Music;
Terminal=false
StartupWMClass=OrpheusDL_GUI
MimeType=x-scheme-handler/orpheusdl;
EOF
}}
"""
    pkgbuild_path = arch_root / "PKGBUILD"
    pkgbuild_path.write_text(pkgbuild_content)

    # Zip the arch_build folder for easy distribution
    zip_path = DIST_DIR / "OrpheusDL_GUI-Arch-PKGBUILD"
    shutil.make_archive(str(zip_path), 'zip', str(arch_root))

    print(f"Arch Linux build files prepared in: {arch_root}")
    print(f"Created Arch Linux source zip: {zip_path}.zip")
    print(f"To build for Arch, extract {zip_path.name}.zip and run 'makepkg -si'.")
    return True


def create_inno_setup_script(modules=None):

    windows_dir = INSTALLER_DIR / "windows"
    windows_dir.mkdir(parents=True, exist_ok=True)

    available_modules = modules or get_available_modules()

    module_components = ""
    module_files = ""

    for m in available_modules:

        name = MODULE_NAMES.get(m, m)

        module_components += f'Name: "modules\\{m}"; Description: "{name} support"; Types: full custom\n'

        module_files += f'Source: "{{#RepoDir}}\\modules\\{m}\\*"; DestDir: "{{app}}\\modules\\{m}"; Components: modules\\{m}; Flags: recursesubdirs\n'

    iss = f"""
#define MyAppName "OrpheusDL GUI"
#include "version.iss"
#define MyAppPublisher "OrpheusDL"
#define MyAppURL "https://github.com/bascurtiz/orpheusdl-gui"
#define MyAppExeName "OrpheusDL_GUI.exe"
#define SourcePath "..\\..\\dist"
#define RepoDir "..\\.."

[Setup]

AppId={{{{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}}}

AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}

OutputDir=..\\..\\dist
OutputBaseFilename=OrpheusDL_GUI-Setup-{{#MyAppVersion}}

Compression=lzma
SolidCompression=yes

[Types]

Name: "full"; Description: "Full installation"
Name: "compact"; Description: "Compact installation"
Name: "custom"; Description: "Custom installation"; Flags: iscustom

[Components]

Name: "main"; Description: "OrpheusDL GUI"; Types: full compact custom; Flags: fixed

{module_components}

[Files]

Source: "{{#SourcePath}}\\{{#MyAppExeName}}"; DestDir: "{{app}}"; Components: main

{module_files}

[Icons]

Name: "{{group}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"

[Run]

Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "Launch OrpheusDL GUI"; Flags: nowait postinstall
"""

    path = windows_dir / "installer.iss"

    path.write_text(iss)

    print("Created installer.iss")


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--platform",
        choices=["windows", "macos", "linux", "all", "auto"],
        default="auto"
    )

    parser.add_argument(
        "--format",
        choices=["all", "appimage", "deb", "rpm", "arch"],
        default="all",
        help="Linux installer format (default: all)"
    )

    parser.add_argument(
        "--skip-pyinstaller",
        action="store_true"
    )

    args = parser.parse_args()

    if args.platform == "auto":

        system = platform.system().lower()

        if system == "windows":
            args.platform = "windows"

        elif system == "darwin":
            args.platform = "macos"

        else:
            args.platform = "linux"

    print("\n=== OrpheusDL Installer Builder ===")

    print("Version:", get_version())

    print("Modules:", get_available_modules())

    if not args.skip_pyinstaller:
        build_pyinstaller()

    if args.platform == "windows" or args.platform == "all":
        build_windows_installer()

    if args.platform == "macos" or args.platform == "all":
        build_macos_installer()

    if args.platform == "linux" or args.platform == "all":
        if args.format == "all" or args.format == "appimage":
            build_linux_installer()
        if args.format == "all" or args.format == "deb":
            build_linux_deb()
        if args.format == "all" or args.format == "rpm":
            build_linux_rpm()
        if args.format == "all" or args.format == "arch":
            build_arch_pkgbuild()

    print("\nBuild complete")


if __name__ == "__main__":
    main()