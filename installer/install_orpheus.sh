  #!/bin/bash
set -e

INSTALL_DIR="$HOME/Downloads/OrpheusDL"

echo "[1/17] Installing system dependencies..."
sudo apt update
sudo apt install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    python3-tk \
    binutils \
    wget \
    ffmpeg \
    upx-ucl \
    patchelf

echo "[2/17] Preparing installation directory..."
cd "$HOME/Downloads"
if [ ! -d "OrpheusDL" ]; then
    git clone https://github.com/bascurtiz/OrpheusDL
fi
cd OrpheusDL

echo "[3/17] Creating Python virtual environment..."
python3 -m venv venv

echo "[4/17] Activating virtual environment..."
source venv/bin/activate

echo "[5/17] Upgrading pip..."
pip install --upgrade pip wheel setuptools

echo "[6/17] Installing core requirements..."
pip install -r requirements.txt
pip install --no-deps --target vendor/librespot git+https://github.com/kokarare1212/librespot-python

echo "[7/17] Installing service modules..."
mkdir -p modules

clone_module () {
    if [ ! -d "$2" ]; then
        git clone "$1" "$2"
    else
        cd "$2" && git pull && cd - >/dev/null
    fi
}

clone_module https://github.com/bascurtiz/orpheusdl-applemusic modules/applemusic
clone_module https://github.com/bascurtiz/orpheusdl-beatport modules/beatport
clone_module https://github.com/bascurtiz/orpheusdl-beatsource modules/beatsource
clone_module https://github.com/bascurtiz/orpheusdl-deezer modules/deezer
clone_module https://github.com/bascurtiz/orpheusdl-qobuz modules/qobuz
clone_module https://github.com/bascurtiz/orpheusdl-soundcloud modules/soundcloud
clone_module https://github.com/bascurtiz/orpheusdl-spotify modules/spotify
clone_module https://github.com/bascurtiz/orpheusdl-youtube modules/youtube

if [ ! -d "modules/tidal" ]; then
    git clone --recurse-submodules https://github.com/bascurtiz/orpheusdl-tidal modules/tidal
fi

# Veilig settings refresh
if [ "$(ls -A modules 2>/dev/null)" ]; then
    echo "[8/17] Initializing OrpheusDL settings..."
    python3 orpheus.py settings refresh || true
else
    echo "[8/17] Skipping settings refresh: no modules installed yet"
fi

echo "[9/17] Installing GUI..."
if [ ! -d "temp_gui" ]; then
    git clone https://github.com/bascurtiz/OrpheusDL-GUI temp_gui
fi

cp -a temp_gui/. .
rm -rf temp_gui
pip install -r requirements-gui.txt

echo "[10/17] Installing build dependencies..."
pip install pyinstaller

echo "[11/17] Fixing PyInstaller GUI dependency detection..."
pip install --upgrade customtkinter darkdetect

echo "[12/17] Downloading AppImage tool..."
mkdir -p installer/linux
if [ ! -f "installer/linux/appimagetool-x86_64.AppImage" ]; then
    wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage -O installer/linux/appimagetool-x86_64.AppImage
fi
chmod +x installer/linux/appimagetool-x86_64.AppImage

echo "[13/17] Bundling FFmpeg for portability..."
mkdir -p portable_bin
cp "$(which ffmpeg)" portable_bin/
cp "$(which ffprobe)" portable_bin/

echo "[14/17] Creating GUI launcher..."
cat << 'EOF' > run_gui.sh
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export PATH="$PWD/portable_bin:$PATH"
python3 gui.py
EOF
chmod +x run_gui.sh

echo "[15/17] Preparing PyInstaller hooks..."
mkdir -p build_hooks
cat << 'EOF' > build_hooks/hook-modules.py
from PyInstaller.utils.hooks import collect_submodules
hiddenimports = collect_submodules('modules')
EOF

echo "[16/17] Setting portable build environment..."
export PYINSTALLER_STRIP=1
export UPX_DIR=$(dirname $(which upx))
export PYTHONHASHSEED=0
export PYTHONUTF8=1
export PATH="$PWD/portable_bin:$PATH"
echo "UPX path: $UPX_DIR"

# The metadata (desktop file, icons, and AppData) is handled automatically 
# by build_installer.py using the files in installer/linux/

echo "[17/17] Building fully portable installer..."
python3 installer/build_installer.py --platform linux --format all

echo ""
echo "======================================"
echo "✅ FULLY PORTABLE BUILD COMPLETE"
echo "======================================"
echo ""
echo "Run GUI locally:"
echo "./run_gui.sh"
echo ""
echo "Portable installers are located in:"
echo "dist/"
echo ""
