# PyInstaller runtime hook for SSL certificate fix on macOS
# This MUST be the first runtime hook to run, before any library that uses SSL
print("[Runtime Hook] SSL fix starting...")

import sys
import ssl

if sys.platform == 'darwin':
    # Disable SSL certificate verification for bundled macOS apps
    # This is necessary because bundled Python apps can't access system certificates
    ssl._create_default_https_context = ssl._create_unverified_context
    print("[Runtime Hook] Applied ssl._create_unverified_context for macOS bundled app")
