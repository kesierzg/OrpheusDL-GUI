import platform
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

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

# Include modules folder if it exists and has content
if os.path.isdir('modules'):
    module_contents = [d for d in os.listdir('modules') if os.path.isdir(os.path.join('modules', d))]
    if module_contents:
        additional_datas.append(('modules', 'modules'))
        print(f"[PyInstaller] Including modules folder with: {module_contents}")

# Collect binaries (ffmpeg)
additional_binaries = []

# Include ffmpeg binary if it exists
if platform.system() == 'Darwin':
    if os.path.isfile('ffmpeg'):
        additional_binaries.append(('ffmpeg', '.'))
        print("[PyInstaller] Including macOS ffmpeg binary")
elif platform.system() == 'Windows':
    if os.path.isfile('ffmpeg.exe'):
        additional_binaries.append(('ffmpeg.exe', '.'))
        print("[PyInstaller] Including Windows ffmpeg.exe binary")

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
        icon='icon.icns',
        onefile=False  # <<< added this
    )

    app = BUNDLE(
        exe,
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
