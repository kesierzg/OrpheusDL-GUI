from PyInstaller.utils.hooks import collect_all, collect_submodules

# yt-dlp hook - comprehensive collection
datas, binaries, hiddenimports = collect_all('yt_dlp')

# Also collect any additional submodules that might be missed
hiddenimports += collect_submodules('yt_dlp')

# Specific hidden imports that are often required for yt-dlp in frozen environments.
# We include known internal modules to ensure they are picked up even if dynamic imports are used.
hiddenimports += [
    'yt_dlp.utils',
    'yt_dlp.extractor',
    'yt_dlp.compat',
    'yt_dlp.compat._legacy',
    'yt_dlp.postprocessor',
    'yt_dlp.networking',
    'yt_dlp.YoutubeDL',  # Explicitly include the module where YoutubeDL class is defined
    'yt_dlp.cookies',
    'yt_dlp.downloader',
    'yt_dlp.options',
]

# Ensure the main yt_dlp module is included
if 'yt_dlp' not in hiddenimports:
    hiddenimports.append('yt_dlp')

# Include yt-dlp-ejs (EJS challenge solver scripts) when installed via yt-dlp[default]
try:
    ejs_datas, ejs_binaries, ejs_hidden = collect_all('yt_dlp_ejs')
    datas += ejs_datas
    binaries += ejs_binaries
    hiddenimports += ejs_hidden
    if 'yt_dlp_ejs' not in hiddenimports:
        hiddenimports.append('yt_dlp_ejs')
except Exception:
    pass  # yt-dlp-ejs optional; remote_components ejs:github used as fallback