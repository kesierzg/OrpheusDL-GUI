# PyInstaller runtime hook for ffmpeg-python
# This pre-imports ffmpeg submodules in the correct order to avoid circular imports

import sys

def _preimport_ffmpeg():
    """Pre-import ffmpeg submodules to avoid circular import issues."""
    try:
        # Import submodules in dependency order
        import ffmpeg.nodes
        import ffmpeg._ffmpeg
        import ffmpeg._filters  
        import ffmpeg._probe
        import ffmpeg._run
        import ffmpeg._view
        import ffmpeg
        print("[Runtime Hook] Successfully pre-imported ffmpeg-python package")
    except ImportError as e:
        print(f"[Runtime Hook] Warning: Could not pre-import ffmpeg: {e}")
    except Exception as e:
        print(f"[Runtime Hook] Warning: Unexpected error pre-importing ffmpeg: {e}")

_preimport_ffmpeg()
