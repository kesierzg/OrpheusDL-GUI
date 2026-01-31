from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

# yt-dlp hook - comprehensive collection
datas, binaries, hiddenimports = collect_all('yt_dlp')

# Also collect any additional submodules that might be missed
hiddenimports += collect_submodules('yt_dlp')

# Ensure the main yt_dlp module is included
if 'yt_dlp' not in hiddenimports:
    hiddenimports.append('yt_dlp')

# Include yt-dlp-ejs (EJS challenge solver scripts) when installed via yt-dlp[default]
try:
    ejs_datas, ejs_binaries, ejs_hidden = collect_all('yt_dlp_ejs')
    datas += ejs_datas
    binaries += ejs_binaries
    hiddenimports += ejs_hidden
    hiddenimports.append('yt_dlp_ejs')
except Exception:
    pass  # yt-dlp-ejs optional; remote_components ejs:github used as fallback