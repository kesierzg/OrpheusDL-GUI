# PyInstaller runtime hook for ffmpeg-python
# This pre-imports ffmpeg submodules in the correct order to avoid circular imports
print("[Runtime Hook] ffmpeg hook starting...")

import sys

try:
    # Force import of nodes first - this is the key module causing circular import
    import ffmpeg.nodes as _nodes
    sys.modules['ffmpeg.nodes'] = _nodes
    print("[Runtime Hook] Pre-imported ffmpeg.nodes")
    
    # Now import the rest
    import ffmpeg
    print("[Runtime Hook] Successfully pre-imported ffmpeg-python package")
except Exception as e:
    print(f"[Runtime Hook] Warning: Could not pre-import ffmpeg: {type(e).__name__}: {e}")
