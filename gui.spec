import platform
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules
# Do not import Tree from PyInstaller.building (path changed in 6.x). We build datas as 2-tuples below.

block_cipher = None

# Resolve paths relative to the spec file. PyInstaller injects SPECPATH (spec dir); __file__ is not set when spec runs.
try:
    SPEC_DIR = os.path.abspath(SPECPATH)
except NameError:
    SPEC_DIR = os.getcwd()
MODULES_SRC = os.path.join(SPEC_DIR, 'modules')

# Collect ffmpeg-python package properly to avoid circular import issues
ffmpeg_datas, ffmpeg_binaries, ffmpeg_hiddenimports = collect_all('ffmpeg')
print(f"[PyInstaller] Collected ffmpeg submodules: {ffmpeg_hiddenimports}")

# Collect additional data files based on what exists in the source directory
additional_datas = [
    ('icon.ico', '.'),
    ('icon.icns', '.'),
    ('icon.png', '.'),
    ('update_checker.py', '.'),
]

# Include each module subfolder explicitly as (src, dest) 2-tuples so no module (e.g. youtube) is omitted.
# Tree() returns 3-tuple TOC entries; Analysis(datas=...) expects 2-tuples, so we build the list manually.
if os.path.isdir(MODULES_SRC):
    _exclude_dirs = {'__pycache__', '.git'}
    _exclude_suffixes = ('.pyc',)
    def _should_skip(path):
        if path in _exclude_dirs or path.endswith(_exclude_suffixes) or path == '.gitignore':
            return True
        return False
    modules_init = os.path.join(MODULES_SRC, '__init__.py')
    if os.path.isfile(modules_init):
        additional_datas.append((modules_init, 'modules'))
    module_subdirs = [d for d in os.listdir(MODULES_SRC) if os.path.isdir(os.path.join(MODULES_SRC, d))]
    for subdir in sorted(module_subdirs):
        if subdir == '__pycache__':
            continue
        src_root = os.path.join(MODULES_SRC, subdir)
        dest_prefix = os.path.join('modules', subdir)
        for root, dirs, filenames in os.walk(src_root, topdown=True):
            dirs[:] = [d for d in dirs if not _should_skip(d)]
            rel_root = os.path.relpath(root, src_root)
            for f in filenames:
                if _should_skip(f):
                    continue
                src_path = os.path.join(root, f)
                if rel_root == '.':
                    dest_path = os.path.join(dest_prefix, f)
                else:
                    dest_path = os.path.join(dest_prefix, rel_root, f)
                additional_datas.append((src_path, os.path.dirname(dest_path)))
    print(f"[PyInstaller] Including modules folder with: {module_subdirs}")

# Collect binaries (ffmpeg - Windows only)
# On macOS/Linux, we don't bundle ffmpeg - users should install via package manager
# macOS: brew install ffmpeg
# Linux: sudo apt install ffmpeg (or equivalent for your distro)
additional_binaries = []

# Include ffmpeg binary only on Windows
# Include ffmpeg binary only on Windows
if platform.system() == 'Windows':
    # We do NOT bundle binaries in the EXE anymore, as the installer handles them
    pass
    # if os.path.isfile('ffmpeg.exe'):
    #     additional_binaries.append(('ffmpeg.exe', '.'))
    #     print("[PyInstaller] Including Windows ffmpeg.exe binary")
    # if os.path.isfile('deno.exe'):
    #     additional_binaries.append(('deno.exe', '.'))
    #     print("[PyInstaller] Including Windows deno.exe binary")
elif platform.system() == 'Darwin':
    print("[PyInstaller] macOS: NOT bundling ffmpeg (use Homebrew: brew install ffmpeg)")
elif platform.system() == 'Linux':
    print("[PyInstaller] Linux: NOT bundling ffmpeg (use: sudo apt install ffmpeg)")

a = Analysis(
    ['gui.py'],
    pathex=['.', 'vendor/librespot'],
    binaries=additional_binaries + ffmpeg_binaries,
    datas=additional_datas + ffmpeg_datas,
    hiddenimports=[
        'certifi',
        'colorama',
        'Cryptodome',
        'Cryptodome.Cipher',
        'Cryptodome.Cipher.AES',
        'Cryptodome.Cipher.ARC4',
        'Cryptodome.Cipher.Blowfish',
        'Cryptodome.Hash',
        'Cryptodome.Hash.MD5',
        'CTkToolTip',
        'customtkinter',
        'defusedxml',
        'future',
        'idna',
        'json',
        'm3u8',
        'mutagen',
        'os',
        'PIL',
        'PIL._tkinter_finder',
        'platform',
        'requests',
        'subprocess',
        'sys',
        'threading',
        'time',
        'tkinter',
        'tqdm',
        'urllib3',
        'uuid',
        'wave',
        'webbrowser',
        'librespot',
        'librespot.audio',
        'librespot.audio.decoders',
        'librespot.core',
        'librespot.metadata',
        'websocket_client',  # Dependency for vendored librespot
        'pyogg',  # Dependency for vendored librespot
        'zeroconf',  # Dependency for vendored librespot
        'pkce',
        'pywidevine',
        'yt_dlp',
        'aiohttp',
        'aiofiles'
    ] + ffmpeg_hiddenimports,
    excludes=['torch', 'cuda', 'pytorch', 'matplotlib', 'pandas', 'numpy'],
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=['hook-ffmpeg.py'],  # Pre-import ffmpeg to avoid circular import
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# Use EXE normally unless on macOS (Darwin), where we avoid onefile
if platform.system() == 'Darwin':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='OrpheusDL_GUI',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='icon.icns',
    )
    
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='OrpheusDL_GUI',
    )

    app = BUNDLE(
        coll,
        name='OrpheusDL GUI.app',
        icon='icon.icns',
        bundle_identifier='com.orpheusdl.gui',
        info_plist={
            'CFBundleName': 'OrpheusDL GUI',
            'CFBundleDisplayName': 'OrpheusDL GUI',
            'NSHighResolutionCapable': 'True',
            'NSRequiresAquaSystemAppearance': 'False'
        }
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='OrpheusDL_GUI',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='icon.ico',
        # this will default to onefile, or add `onefile=True` explicitly
    )
