# ============================================================================
# SSL Certificate Fix - MUST BE AT VERY TOP BEFORE ANY IMPORTS
# ============================================================================
# On macOS, bundled Python apps can't verify SSL certificates.
# This disables SSL verification for bundled apps BEFORE any library is imported.
# ============================================================================
import ssl
import sys as _sys

if getattr(_sys, 'frozen', False) and _sys.platform == 'darwin':
    # Method 1: Patch the default HTTPS context factory
    ssl._create_default_https_context = ssl._create_unverified_context
    print("[SSL Fix] Applied ssl._create_unverified_context for macOS bundled app")
    
    # Method 2: Patch ssl.SSLContext.wrap_socket to disable verification
    # This is the LOWEST level - intercepts every SSL socket creation
    _original_wrap_socket = ssl.SSLContext.wrap_socket
    
    def _patched_wrap_socket(self, sock, *args, **kwargs):
        """Patched wrap_socket that disables SSL verification."""
        # Force disable verification on this context
        self.check_hostname = False
        self.verify_mode = ssl.CERT_NONE
        return _original_wrap_socket(self, sock, *args, **kwargs)
    
    ssl.SSLContext.wrap_socket = _patched_wrap_socket
    print("[SSL Fix] Patched ssl.SSLContext.wrap_socket to disable verification")
    
    # Method 3: Also patch the deprecated ssl.wrap_socket for older code
    if hasattr(ssl, 'wrap_socket'):
        _original_ssl_wrap_socket = ssl.wrap_socket
        
        def _patched_ssl_wrap_socket(sock, *args, **kwargs):
            """Patched ssl.wrap_socket that uses unverified context."""
            if 'ssl_context' not in kwargs:
                ctx = ssl._create_unverified_context()
                kwargs['ssl_context'] = ctx
            return _original_ssl_wrap_socket(sock, *args, **kwargs)
        
        ssl.wrap_socket = _patched_ssl_wrap_socket
        print("[SSL Fix] Patched ssl.wrap_socket (deprecated) to use unverified context")
# ============================================================================

import os
import sys

# Add script/application directory to sys.path for imports
if getattr(sys, 'frozen', False):
    # Frozen (compiled) app
    application_path = os.path.dirname(sys.executable)
else:
    # Development mode - use script directory
    application_path = os.path.dirname(os.path.abspath(__file__))

if application_path not in sys.path:
    sys.path.insert(0, application_path)

modules_path = os.path.join(application_path, 'modules')
if os.path.isdir(modules_path) and modules_path not in sys.path:
    sys.path.insert(0, modules_path)

gamdl_parent_path = os.path.join(application_path, 'modules', 'applemusic', 'gamdl')
if os.path.isdir(gamdl_parent_path) and gamdl_parent_path not in sys.path:
    sys.path.insert(0, gamdl_parent_path)

os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

from utils.vendor_bootstrap import bootstrap_vendor_paths
bootstrap_vendor_paths()

import copy
import customtkinter
import datetime
import enum
import inspect
import io
import json
import multiprocessing
import os
import warnings
# Suppress resource_tracker semaphore leak warning on macOS when using os._exit() for GUI shutdown
warnings.filterwarnings("ignore", message="resource_tracker: There appear to be .* leaked semaphore.*")
import platform
import queue
import re
import requests
import subprocess
import sys
import threading
import tkinter
import tkinter.filedialog
import tkinter.messagebox
import shutil
from CTkToolTip import CTkToolTip
from PIL import Image, ImageDraw, ImageTk
from pathlib import Path
from tkinter import ttk
from tqdm import tqdm
from urllib.parse import urlparse
import pickle
import traceback
import logging
import webbrowser
import time
import asyncio
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        print("[Patch] Applied asyncio.WindowsSelectorEventLoopPolicy() for Windows.")
    except Exception as e:
        print(f"[Patch] WARNING: Failed to set asyncio.WindowsSelectorEventLoopPolicy(): {e}")

# Native Audio Playback Imports
if platform.system() == "Windows":
    import ctypes
    from ctypes import wintypes


# Log capture system for debugging initialization errors
class LogCapture:
    """Captures stdout/stderr for later display in GUI."""
    def __init__(self, max_lines=500):
        self.log_lines = []
        self.max_lines = max_lines
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        self._capturing = False
    
    def start_capture(self):
        """Start capturing stdout and stderr."""
        if self._capturing:
            return
        self._capturing = True
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
    
    def stop_capture(self):
        """Stop capturing and restore original streams."""
        if not self._capturing:
            return
        self._capturing = False
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
    
    def write(self, text):
        """Write to both capture buffer and original stream."""
        if text.strip():  # Don't capture empty lines
            self.log_lines.append(text.rstrip())
            if len(self.log_lines) > self.max_lines:
                self.log_lines.pop(0)
        # Also write to original stdout so terminal still shows output
        if self._original_stdout:
            try:
                self._original_stdout.write(text)
                self._original_stdout.flush()
            except:
                pass
    
    def flush(self):
        if self._original_stdout:
            try:
                self._original_stdout.flush()
            except:
                pass
    
    def get_logs(self):
        """Get all captured log lines as a string."""
        return "\n".join(self.log_lines)
    
    def clear(self):
        """Clear the log buffer."""
        self.log_lines.clear()

# Global log capture instance
_log_capture = LogCapture()
_log_capture.start_capture()

_SCRIPT_DIR = None
_DATA_DIR = None

SERVICE_COLORS = {
    "tidal": "#33ffe7",
    "apple music": "#FA586A",
    "beatport": "#00ff89",
    "beatsource": "#16a8f4",
    "deezer": "#a238ff",
    "qobuz": "#0070ef",
    "soundcloud": "#ff5502",
    "spotify": "#1cc659",
    "napster": "#295EFF",
    "kkbox": "#27B1D8",
    "idagio": "#5C34FE",
    "bugs": "#FF3B28",
    "nugs": "#C83B30",
    "youtube": "#FF0000"
}

SERVICE_DISPLAY_NAMES = {
    "tidal": "TIDAL",
    "apple music": "Apple Music",
    "beatport": "Beatport",
    "beatsource": "Beatsource",
    "deezer": "Deezer",
    "qobuz": "Qobuz",
    "soundcloud": "SoundCloud",
    "spotify": "Spotify",
    "napster": "Napster",
    "kkbox": "KKBOX",
    "idagio": "IDAGIO",
    "bugs": "Bugs!",
    "nugs": "Nugs.net",
    "youtube": "YouTube"
}

# Standardized UI Colors
SECONDARY_TEXT_COLOR = "#898c8d"
LINK_COLOR = "#1F6AA5"
LINK_HOVER_COLOR = "#4A9EFF"
WARNING_COLOR = "#F2C94C"
ERROR_COLOR = "#FF6B6B"
LIGHT_TEXT_COLOR = "#dddddd"
WHITE_TEXT_COLOR = "#FFFFFF"
# Cursor for clickable items: macOS uses "pointinghand", Windows/Linux use "hand2" (unified for context menus and tree hover)
HAND_CURSOR = "pointinghand" if platform.system() == "Darwin" else "hand2"

def _simple_slugify(text):
    if not text: return None
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = re.sub(r'--+', '-', text)
    text = text.strip('-')
    return text if text else None

def _get_ffmpeg_path():
    """Get the path to ffmpeg executable."""
    # Check bundled ffmpeg first (for frozen apps)
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
        bundled = os.path.join(app_dir, 'ffmpeg.exe' if platform.system() == 'Windows' else 'ffmpeg')
        if os.path.exists(bundled):
            return bundled
    
    # Check script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_ffmpeg = os.path.join(script_dir, 'ffmpeg.exe' if platform.system() == 'Windows' else 'ffmpeg')
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg
    
    # Fall back to PATH
    return 'ffmpeg'

def _audio_debug():
    """Return True if Advanced debug_mode is on (so [Audio] messages can be printed)."""
    return (current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False)
            if 'current_settings' in globals() else False)

def _convert_to_wav(input_path, output_path):
    """Convert audio file to WAV using ffmpeg (for better Windows MCI compatibility)."""
    try:
        ffmpeg = _get_ffmpeg_path()
        cmd = [
            ffmpeg, '-y', '-hide_banner', '-loglevel', 'error',
            '-i', input_path,
            '-acodec', 'pcm_s16le',  # Standard 16-bit PCM WAV
            '-ar', '44100',           # 44.1kHz sample rate
            '-ac', '2',               # Stereo
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=15)
        if result.returncode == 0 and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            if _audio_debug():
                print(f"[Audio] Converted to WAV: {file_size} bytes")
            return True
        else:
            stderr = result.stderr.decode('utf-8', errors='ignore') if result.stderr else ''
            if _audio_debug():
                print(f"[Audio] FFmpeg WAV conversion failed: {stderr[:200]}")
            return False
    except Exception as e:
        if _audio_debug():
            print(f"[Audio] FFmpeg WAV conversion error: {e}")
        return False

def play_audio(source):
    """
    Plays audio from a URL or local file using native platform tools.
    - Windows: Uses mciSendString (winmm.dll). Downloads URLs to temp file first.
              Converts audio to WAV using ffmpeg for reliable MCI playback.
    - macOS: Uses afplay (subprocess).
    - Linux: Uses xdg-open (subprocess) with system default player.
    """
    global _audio_process, _current_volume
    system = platform.system()
    if _audio_debug():
        print(f"[Audio] play_audio called with source: {source[:100]}..." if len(str(source)) > 100 else f"[Audio] play_audio called with source: {source}")

    # Stop any current playback FIRST
    stop_audio()
    
    # Small delay to ensure file handles are released
    import time
    time.sleep(0.1)
    
    # Check if this is a stream (HLS/m3u8 or SoundCloud)
    # Convert streams to WAV using ffmpeg on Windows (for winsound). On macOS, skip conversion for SoundCloud (afplay supports M4A natively).
    source_lower = source.lower()
    is_hls_stream = '.m3u8' in source_lower or 'hls' in source_lower
    is_soundcloud_stream = 'sndcdn.com' in source_lower
    is_stream = is_hls_stream or is_soundcloud_stream
    
    # For streams, convert to WAV using ffmpeg first (limited to 30 seconds) on Windows, or non-SoundCloud streams on other platforms.
    # On macOS, SoundCloud previews (e.g. M4A) are played natively by afplay after download; WAV conversion can break playback.
    if is_stream and not (system == "Darwin" and is_soundcloud_stream):
        try:
            import tempfile
            ffmpeg_path = _get_ffmpeg_path()
            temp_dir = tempfile.gettempdir()
            wav_path = os.path.join(temp_dir, "orpheus_preview_stream.wav")
            
            try:
                if os.path.exists(wav_path):
                    os.remove(wav_path)
            except:
                import uuid
                wav_path = os.path.join(temp_dir, f"orpheus_preview_stream_{uuid.uuid4().hex[:8]}.wav")
            if _audio_debug():
                print(f"[Audio] Converting stream to WAV with ffmpeg...")

            # Use ffmpeg to convert first 30 seconds to WAV
            convert_cmd = [
                ffmpeg_path, '-y', '-hide_banner', '-loglevel', 'error',
                '-i', source,
                '-t', '30',  # Limit to 30 seconds for preview
                '-acodec', 'pcm_s16le',
                '-ar', '44100',
                '-ac', '2',
                wav_path
            ]
            
            # Run conversion synchronously (blocking)
            result = subprocess.run(convert_cmd, capture_output=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
                if _audio_debug():
                    print(f"[Audio] Stream converted to WAV: {os.path.getsize(wav_path)} bytes")
                # Return the path - caller should play on main thread
                return ('play_file', wav_path)
            else:
                stderr = result.stderr.decode('utf-8', errors='ignore') if result.stderr else ''
                if _audio_debug():
                    print(f"[Audio] Failed to convert stream: {stderr[:200]}")
                return False
        except subprocess.TimeoutExpired:
            if _audio_debug():
                print(f"[Audio] Stream conversion timed out")
            return False
        except Exception as e:
            if _audio_debug():
                print(f"[Audio] Error converting stream: {e}")
            return False
    
    # Handle online URLs by downloading to a temp file first (especially for Windows MCI)
    if source.startswith(('http://', 'https://')):
        try:
            import tempfile
            import requests
            
            # Create a temp file with the correct extension if possible, or .mp3 default (or .m4a for SoundCloud on macOS)
            ext = '.mp3'
            if system == "Darwin" and 'sndcdn.com' in source.lower():
                ext = '.m4a'  # SoundCloud CDN often serves M4A; afplay supports it natively
            if '.' in source.split('/')[-1]:
                possible_ext = '.' + source.split('/')[-1].split('.')[-1].split('?')[0]
                if len(possible_ext) <= 5: # Sanity check
                    ext = possible_ext
            
            # Use a consistent temp file for previews to avoid clutter
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"orpheus_preview{ext}")
            
            # Try to remove existing temp file first (in case it's stale)
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                # If we can't remove it, use a unique name instead
                import uuid
                temp_path = os.path.join(temp_dir, f"orpheus_preview_{uuid.uuid4().hex[:8]}{ext}")
            
            # Download the file
            if _audio_debug():
                print(f"[Audio] Downloading preview from: {source[:80]}...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(source, stream=True, timeout=15, headers=headers)
            if response.status_code == 200:
                # Check content type to make sure it's audio
                content_type = response.headers.get('content-type', '').lower()
                if 'html' in content_type or 'text' in content_type:
                    if _audio_debug():
                        print(f"[Audio] Server returned HTML/text instead of audio (content-type: {content_type})")
                    return False
                
                total_bytes = 0
                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        total_bytes += len(chunk)
                
                # Verify the file was actually written
                if os.path.exists(temp_path):
                    file_size = os.path.getsize(temp_path)
                    if _audio_debug():
                        print(f"[Audio] Downloaded {file_size} bytes to {temp_path}")
                    if file_size > 1000:  # At least 1KB for valid audio
                        # Quick sanity check - MP3 files start with ID3 or 0xFF
                        with open(temp_path, 'rb') as f:
                            header = f.read(4)
                        if header[:3] == b'ID3' or header[:2] == b'\xff\xfb' or header[:2] == b'\xff\xfa':
                            source = temp_path
                        else:
                            if _audio_debug():
                                print(f"[Audio] Downloaded file doesn't look like MP3 (header: {header.hex()})")
                            # Still try to play it - might be a different format
                            source = temp_path
                    elif file_size > 0:
                        if _audio_debug():
                            print(f"[Audio] Downloaded file is too small ({file_size} bytes) - likely not valid audio")
                        source = temp_path  # Try anyway
                    else:
                        if _audio_debug():
                            print(f"[Audio] Downloaded file is empty!")
                        return False
                else:
                    if _audio_debug():
                        print(f"[Audio] Temp file was not created!")
                    return False
            else:
                if _audio_debug():
                    print(f"[Audio] Failed to download preview: HTTP {response.status_code}")
                return False
        except Exception as e:
            if _audio_debug():
                print(f"[Audio] Error downloading preview: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to trying to play the URL directly
            pass

    try:
        if system == "Windows":
            import tempfile
            temp_dir = tempfile.gettempdir()
            source_lower = source.lower()
            
            # Convert all audio to WAV for reliable winsound playback
            # winsound.PlaySound with SND_ASYNC can be properly stopped
            wav_path = os.path.join(temp_dir, "orpheus_preview_play.wav")
            
            needs_conversion = not source_lower.endswith('.wav')
            if needs_conversion:
                try:
                    if os.path.exists(wav_path):
                        os.remove(wav_path)
                except:
                    import uuid
                    wav_path = os.path.join(temp_dir, f"orpheus_preview_play_{uuid.uuid4().hex[:8]}.wav")
                
                if _audio_debug():
                    print(f"[Audio] Converting to WAV for playback...")
                if _convert_to_wav(source, wav_path):
                    source = wav_path
                else:
                    if _audio_debug():
                        print(f"[Audio] Failed to convert to WAV")
                    return False

            # Use winsound for WAV playback - this can be reliably stopped
            import winsound

            # Set volume before playing
            wave_volume = int((_current_volume / 100) * 0xFFFF)
            stereo_volume = (wave_volume << 16) | wave_volume
            ctypes.windll.winmm.waveOutSetVolume(0, stereo_volume)

            # Play asynchronously (SND_ASYNC = 0x0001, SND_FILENAME = 0x00020000)
            if _audio_debug():
                print(f"[Audio] Playing with winsound: {os.path.basename(source)}")
            winsound.PlaySound(source, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return True
            
        elif system == "Darwin":
            # macOS - use afplay (supports M4A natively)
            # We use Popen to not block the GUI and track process for stopping
            _audio_process = subprocess.Popen(["afplay", source], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
            
        elif system == "Linux":
            # Linux - use xdg-open to play audio with default system player
            _audio_process = subprocess.Popen(["xdg-open", source], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
            
    except Exception as e:
        if _audio_debug():
            print(f"[Audio] Error playing audio: {e}")
        return False

def stop_audio():
    """Stops any currently playing audio."""
    global _audio_process
    system = platform.system()
    if _audio_debug():
        print(f"[Audio] stop_audio() called")
    try:
        # Kill any tracked subprocess (afplay on macOS, xdg-open on Linux)
        if _audio_process is not None:
            if _audio_debug():
                print(f"[Audio] Stopping subprocess (pid: {_audio_process.pid})")
            try:
                _audio_process.terminate()
                _audio_process.wait(timeout=1)
            except:
                try:
                    _audio_process.kill()
                except:
                    pass
            _audio_process = None
        
        # Stop audio playback
        if system == "Windows":
            # Stop winsound playback by playing None
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
            if _audio_debug():
                print(f"[Audio] winsound stopped")

            # Also close any MCI devices as safety net
            ctypes.windll.winmm.mciSendStringW("close all", None, 0, 0)
        elif system == "Darwin":
            # Kill any afplay processes
            subprocess.run(["killall", "afplay"], capture_output=True)
    except Exception as e:
        if _audio_debug():
            print(f"[Audio] Error stopping audio: {e}")


class DummyStderr:
    """A dummy file-like object that discards stderr output."""
    def write(self, msg): pass
    def flush(self): pass
    def isatty(self): return False

class TidalAutoAuthPatcher:
    """
    Context manager that patches input() to automatically handle Tidal TV authentication.
    When Tidal prompts for login method, this auto-selects TV (option 1).
    The browser will open automatically via webbrowser.open() in the Tidal module.
    """
    def __init__(self, output_queue_ref=None):
        self.output_queue = output_queue_ref
        self._original_input = None
    
    def __enter__(self):
        import builtins
        self._original_input = builtins.input
        builtins.input = self._tidal_auto_input
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import builtins
        builtins.input = self._original_input
        return False
    
    def _tidal_auto_input(self, prompt=''):
        """
        Patched input function for Tidal authentication.
        Automatically responds to known prompts.
        """
        prompt_lower = prompt.lower().strip()
        
        # Tidal login method selection - auto-select TV (option 1)
        if 'login method' in prompt_lower:
            if self.output_queue:
                self.output_queue.put("TIDAL: Auto-selecting TV login method...\n")
            return '1'
        
        # Tidal relogin prompt - auto-accept
        if 'relogin' in prompt_lower or ('y/n' in prompt_lower and 'relogin' in prompt_lower):
            if self.output_queue:
                self.output_queue.put("TIDAL: Auto-accepting relogin...\n")
            return 'Y'
        
        # For any other prompts, return empty string (shouldn't happen in TV flow)
        if self.output_queue:
            self.output_queue.put(f"TIDAL Auth: Unexpected prompt '{prompt}' - returning empty\n")
        return ''

file_download_queue = []
output_queue = queue.Queue()
current_batch_output_path = None
_current_download_context = None

_queue_log_handler_instance = None

class QueueLogHandler(logging.Handler):
    """A handler class which sends records to a queue."""
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
        self.reset_ffmpeg_state_for_current_download()

    def reset_ffmpeg_state_for_current_download(self):
        self._specific_ffmpeg_hls_error_logged_this_download = False

    def emit(self, record):
        import re
        global current_settings
        is_debug_mode = current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False)

        if is_debug_mode:
            log_entry = f"[{record.levelname}] {self.format(record)}\n"
            self.log_queue.put(log_entry)
            return
        return

        msg_content = record.getMessage()
        hls_ffmpeg_warning_pattern = r"soundcloud --> HLS_UNEXPECTED_ERROR_IN_TRY_BLOCK: \[(WinError 2|Errno 2)\] (The system cannot find the file specified|No such file or directory)"
        is_primary_hls_ffmpeg_warning = (
            record.levelname == 'WARNING' and
            "Track download attempt" in msg_content and
            "failed for" in msg_content and
            re.search(hls_ffmpeg_warning_pattern, msg_content)
        )

        if is_primary_hls_ffmpeg_warning:
            if not self._specific_ffmpeg_hls_error_logged_this_download:
                self._specific_ffmpeg_hls_error_logged_this_download = True
                ffmpeg_path_setting = current_settings.get("globals", {}).get("advanced", {}).get("ffmpeg_path", "ffmpeg").strip()
                user_friendly_ffmpeg_msg = (
                    "\n[FFMPEG ERROR] FFmpeg was not found or is misconfigured. This is required for audio conversion (e.g., SoundCloud HLS streams).\n\n"
                    "Possible Solutions:\n"
                    "1. Install FFmpeg: If not installed, download from ffmpeg.org and install it.\n"
                    "2. Check PATH: Ensure the directory containing ffmpeg.exe (or ffmpeg) is in your system's PATH environment variable.\n"
                    "3. Configure in GUI: Go to Settings > Global > Advanced > FFmpeg Path, and set the full path to your ffmpeg executable.\n"
                    "4. Place in App Folder: Download the FFmpeg binary and place it in the application folder or data folder.\n\n"
                    f"Current FFmpeg Path setting in GUI: '{ffmpeg_path_setting}'\n\n"
                    "Download process aborted due to FFmpeg issue."
                )
                self.log_queue.put(user_friendly_ffmpeg_msg + '\n')
            return
        if self._specific_ffmpeg_hls_error_logged_this_download:
            if record.levelname == 'ERROR' and "Failed after 3 attempts" in msg_content:
                return
        is_beatsource_404_warning = (
            record.name == 'root' and
            record.levelname == 'WARNING' and
            "Fetching as playlist failed (404)" in msg_content
        )
        if is_beatsource_404_warning:
            return
        
        if "Librespot:AudioKeyManager" in record.name and "Audio key error" in msg_content:
            return            
        if "modules.spotify" in record.name and "Rate limit suspected" in msg_content:
            return            
        if record.name == 'root' and record.levelname == 'ERROR' and "SpotifyAuthError" in msg_content:
            return
        if record.levelno == logging.INFO and ':' in record.name:
            return        
        if record.name == 'modules.spotify.spotify_api' and \
           record.levelname == 'ERROR' and \
           msg_content.startswith("GLOBAL_PATCH_DEBUG: Unexpected generic exception during Librespot session creation: [Errno 61] Connection refused"):
            return
        cleaned_msg = self.format(record) 
        cleaned_msg = re.sub(r' - \w+ - ', ' - ', cleaned_msg)
        if "Track download attempt" in cleaned_msg and "failed for" in cleaned_msg:            
            attempt_match = re.search(r'Track download attempt (\d+) failed for \w+\. Retrying in (\d+) seconds', cleaned_msg)
            if attempt_match:
                attempt_num = attempt_match.group(1)
                retry_seconds = attempt_match.group(2)
                cleaned_msg = re.sub(r'Track download attempt \d+ failed for \w+\. Retrying in \d+ seconds.*', 
                                   f'Download attempt {attempt_num} failed. Retrying in {retry_seconds} seconds...', cleaned_msg)
        
        if "Track download failed for" in cleaned_msg and "Module get_track_download returned None" in cleaned_msg:
            if "after 3 attempts" in cleaned_msg:
                cleaned_msg = re.sub(r'Track download failed for \w+: Module get_track_download returned None after \d+ attempts.*', 
                                   'Failed after 3 attempts (likely due to rate-limiting)', cleaned_msg)
            else:
                cleaned_msg = re.sub(r'Track download failed for \w+: Module get_track_download returned None.*', 
                                   'Download failed (likely due to rate-limiting)', cleaned_msg)
        
        log_entry = f"[{record.levelname}] {cleaned_msg}\n"
        self.log_queue.put(log_entry)

    def flush(self):
        pass
    def readable(self):
        return False
    def seekable(self):
        return False
    def writable(self):
        return True
    
def setup_logging(log_queue):
    global current_settings, _queue_log_handler_instance

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    _queue_log_handler_instance = QueueLogHandler(log_queue)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s', datefmt='%H:%M:%S')
    _queue_log_handler_instance.setFormatter(formatter)
    root_logger.addHandler(_queue_log_handler_instance)
    if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
        root_logger.setLevel(logging.INFO)
        logging.info("Logging configured to use GUI queue (debug mode enabled).")
    else:
        root_logger.setLevel(logging.CRITICAL)
__version__ = "v1.0.8"
from update_checker import run_check_in_thread
_mutex_handle = None
if platform.system() == "Windows":
    try:
        import winsound
    except ImportError:
        print("[Warning] 'winsound' module not found, sound notifications disabled on Windows.")
        winsound = None
else:
    winsound = None

# ============================================================================
# Cover Preview & Audio Preview System
# ============================================================================
# Global cache for PhotoImages to prevent garbage collection
_cover_image_cache = {}
_cover_hover_cache = {}  # Cache for hover (darkened) versions of covers
_cover_hover_iid = None  # Track which cover is currently being hovered
_cover_fade_in_progress_count = 0  # Limit concurrent fade-ins to avoid GUI freeze
_placeholder_cover_image = None
_currently_playing_preview_iid = None  # Track which row is currently playing
_preview_hover_iid = None  # Track which row's preview button is being hovered
_row_hover_iid = None  # Track which row has hover highlight (#272828)
_cover_load_requested = set()  # Track which covers have been requested (for lazy loading)
_youtube_thumbnail_fetching = set()  # Track which YouTube items are currently fetching thumbnails (to avoid duplicates)
_youtube_thumbnail_queue = []  # Queue for YouTube thumbnail fetches to limit concurrent requests
_youtube_max_concurrent_fetches = 2  # Maximum number of concurrent YouTube thumbnail fetches
_lazy_loading_preview_iid = None  # Track which item is currently fetching a preview URL
_audio_process = None  # Track subprocess for afplay/xdg-open (for stopping)
_pulse_after_id = None  # Track the after() ID for pulsing animation
_pulse_state = False  # Track current pulse state (bright/dim)
_loading_after_id = None  # Track the after() ID for loading dots animation
_loading_dot_position = 0  # Track current position in walking dots animation (0-2)
_loading_animation_iid = None  # Track which item is currently showing loading animation
# Long expand message: show after 8s when opening playlist/artist/album via ≡ icon (or when "All" search runs)
_expand_long_loading_after_id = None  # 8s delayed show of message with "(this can take up to ~1 minute)"
_expand_loading_dots_after_id = None  # Walking dots animation for that message
_expand_loading_dots_position = 0
_expand_loading_message_prefix = "Fetching all data"  # Or "Searching all platforms" for All search
_expanded_album_playlist_iids = set()  # Tree iids of expanded album/playlist rows (show tracks as children)
# When viewing an album's tracks in the list view (instead of inline expand), holds saved search state for "Back"
_album_track_list_context = None  # None or list of {"saved_data": [...], "title": "..."}; stack for Back navigation
_current_results_header_title = None  # Full title (e.g. "Artist: Name") for current view; used when pushing album track list
# Bordered pill badge showing content type (Album / Playlist / Artist) in results header; created in search tab setup
_content_type_badge = None
_content_type_badge_label = None
# Label shown after 8s when expand takes long: "Fetching all data... (this can take up to ~1 minute)"
_expand_loading_label = None

# Preview button styling
# Note: ttk.Treeview doesn't support per-cell coloring, only per-row via tags
# So we use distinct icon shapes instead of colors for visual feedback
PREVIEW_PLAY_ICON = " ▶ "  # Play triangle with spacing for visibility
PREVIEW_PLAY_HOVER = "[ ▶ ]"  # Enlarged appearance on hover
PREVIEW_STOP_ICON = " ▶ "  # Stop square with spacing for visibility
PREVIEW_STOP_ICON_PULSE = "   "  # Pulsing stop icon (hollow square for animation)
PREVIEW_STOP_HOVER = "[ ■ ]"  # Enlarged appearance on hover
PREVIEW_UNAVAILABLE = " · "  # Small dot for unavailable
# Expand/collapse: list icon = expand to show tracks, up = collapse
PREVIEW_EXPAND_COLLAPSED = "  ≡  "   # List/sort icon: click to expand and show tracks below
PREVIEW_EXPAND_COLLAPSED_HOVER = " [ ≡ ] "  # Hover: brackets like play icon
PREVIEW_EXPAND_EXPANDED = "  ▲  "    # Up: expanded, click to collapse
PREVIEW_EXPAND_EXPANDED_HOVER = " [ ▲ ] "  # Hover: brackets
PREVIEW_LOADING_ICON = " ... "  # Placeholder for loading animation
PREVIEW_LOADING_ICON = " … "  # Loading indicator for lazy-loaded previews (ellipsis) - base, will be animated
LOADING_ANIMATION_FRAMES = [" . ", " .. ", " ... "]  # Animation frames for loading state

# Volume control widgets (initialized later in GUI setup)
_volume_frame = None
_volume_slider = None
_volume_label = None
_current_volume = 75  # 0-100

# Cover image size constant
COVER_SIZE = 44
# Tree column #0 (cover) width; Preview column (≡/▶) follows and has this width
PREVIEW_COLUMN_START = COVER_SIZE + 6   # tree.column("#0", width=COVER_SIZE+6)
PREVIEW_COLUMN_WIDTH = 56               # col_configs["Preview"]["width"]
COVER_CORNER_RADIUS = 3  # Radius for rounded corners
# Fade-in when cover appears in search results
COVER_FADE_IN_STEPS = 5
COVER_FADE_IN_STEP_MS = 45
COVER_FADE_MAX_CONCURRENT = 4  # Max fades at once; excess show immediately to avoid GUI freeze
TREEVIEW_BG_HEX = "#1D1E1E"  # Match Custom.Treeview fieldbackground

# Fixed width for all right-click context menus (matches main action buttons: 100)
CONTEXT_MENU_WIDTH = 100
# Icon and text color for context menu items (match so icons = text)
CONTEXT_MENU_TEXT_COLOR = "#DCE4EE"
CONTEXT_MENU_TEXT_DISABLED = "#808080"  # gray (hex for PIL and CTk)
# Background for all tooltips and right-click context menus
TOOLTIP_MENU_BG = "#222323"

# Content width for download log, search results, and platform help sections (kept in sync)
HELP_CONTENT_WIDTH = 920

# Platform icons on cover in column #0 (loaded from local "platforms" folder)
PLATFORM_ICON_NAMES = ("AppleMusic", "Beatport", "Beatsource", "Deezer", "Qobuz", "SoundCloud", "Spotify", "Tidal", "YouTube")
PLATFORM_ICON_SIZE = 16  # Size of platform icon in the overlay (compact so it doesn’t dominate the row)
_platform_icon_cache = {}  # platform_name -> PhotoImage (keep references)
_platform_icon_cache_lock = threading.Lock()
_platform_icon_photo_refs = []  # Unused (platform icons drawn on cover in column #0)

def _platform_icon_path(platform_name):
    """Return path to platform icon file in application_path/platforms, or None if not found.
    When frozen (e.g. macOS .app), bundled datas live in sys._MEIPASS, not next to the executable."""
    if not platform_name:
        return None
    # Use _MEIPASS for bundled resources (macOS .app, Windows onefile); else use application_path
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base = os.path.join(sys._MEIPASS, "platforms")
    else:
        base = os.path.join(application_path, "platforms")
    for name in (platform_name, platform_name.replace(" ", ""), platform_name.lower().replace(" ", "")):
        for ext in (".png", ".jpg", ".jpeg", ".webp"):
            p = os.path.join(base, name + ext)
            if os.path.isfile(p):
                return p
    return None

def _load_platform_icon_sync(platform_name):
    """Load platform icon from local platforms folder and return a small PhotoImage; cache it."""
    with _platform_icon_cache_lock:
        if platform_name in _platform_icon_cache:
            return _platform_icon_cache[platform_name]
    path = _platform_icon_path(platform_name)
    if not path:
        return None
    try:
        img = Image.open(path)
        img = img.convert("RGBA")
        size = PLATFORM_ICON_SIZE
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        with _platform_icon_cache_lock:
            if platform_name in _platform_icon_cache:
                return _platform_icon_cache[platform_name]
            photo = ImageTk.PhotoImage(img)
            _platform_icon_cache[platform_name] = photo
            return photo
    except Exception as e:
        if not getattr(sys, 'frozen', False):
            print(f"[Platform icon] Failed to load {platform_name} from {path}: {e}")
        return None

def _load_platform_icon_pil(platform_name):
    """Load platform icon from local platforms folder and return a small PIL Image (RGBA), or None."""
    path = _platform_icon_path(platform_name)
    if not path:
        return None
    try:
        img = Image.open(path)
        img = img.convert("RGBA")
        return img.resize((PLATFORM_ICON_SIZE, PLATFORM_ICON_SIZE), Image.Resampling.LANCZOS)
    except Exception:
        return None

def _composite_platform_icon_on_cover(pil_cover, platform_name, cover_size=COVER_SIZE):
    """Paste platform icon onto bottom-right of cover; return new PIL Image. pil_cover must be RGBA."""
    icon_pil = _load_platform_icon_pil(platform_name)
    if not icon_pil:
        return pil_cover
    if pil_cover.mode != "RGBA":
        pil_cover = pil_cover.convert("RGBA")
    out = pil_cover.copy()
    pad = 2
    x = cover_size - PLATFORM_ICON_SIZE - pad
    y = cover_size - PLATFORM_ICON_SIZE - pad
    out.paste(icon_pil, (x, y), icon_pil)
    return out

def _tidal_has_saved_sessions(app_path):
    """Return True only if Tidal has at least one saved session with a valid refresh_token (user has logged in successfully).
    Tidal requires interactive login; without valid sessions, loading the module can open the browser or block.
    Exclude Tidal from 'All' until user has completed login so 'Search All' never hangs on Tidal."""
    try:
        storage_path = os.path.join(app_path, 'config', 'loginstorage.bin')
        if not os.path.isfile(storage_path):
            return False
        with open(storage_path, 'rb') as f:
            data = pickle.load(f)
        modules = data.get('modules', {})
        tidal_mod = modules.get('tidal', {})
        if not tidal_mod:
            return False
        sessions = tidal_mod.get('sessions', {})
        selected = tidal_mod.get('selected', 'default')
        session_data = sessions.get(selected, {})
        custom_data = session_data.get('custom_data', {})
        tidal_sessions = custom_data.get('sessions', {})
        if not tidal_sessions:
            return False
        for _name, storage in tidal_sessions.items():
            if isinstance(storage, dict) and str(storage.get('refresh_token') or '').strip():
                return True
        return False
    except Exception:
        return False

def get_searchable_platforms(settings, installed_platform_keys, app_path):
    """Return list of platform names that can be searched: YouTube, Apple Music, and Deezer always (optional credentials); others if credentials are set.
    Tidal is excluded until the user has successfully logged in (saved sessions exist), since loading it without sessions opens the browser."""
    base = [pk for pk in installed_platform_keys if pk != "Musixmatch"]
    platforms_with_optional_credentials = ["YouTube", "AppleMusic", "Deezer", "Qobuz"]
    configured = []
    creds = (settings or {}).get("credentials", {})
    try:
        default_creds = (DEFAULT_SETTINGS or {}).get("credentials", {})
    except NameError:
        default_creds = {}
    for platform_name in base:
        if platform_name in platforms_with_optional_credentials:
            configured.append(platform_name)
            continue
        default_platform_fields = (default_creds or {}).get(platform_name, {})
        if not default_platform_fields:
            configured.append(platform_name)
            continue
        current_platform_creds = creds.get(platform_name, {})
        if platform_name == "Qobuz":
            has_email_pass = bool(str(current_platform_creds.get("username", "") or "").strip() and str(current_platform_creds.get("password", "") or "").strip())
            has_id_token = bool(str(current_platform_creds.get("user_id", "") or "").strip() and str(current_platform_creds.get("auth_token", "") or "").strip())
            is_fully_filled = has_email_pass or has_id_token
        elif platform_name == "Deezer":
            has_email_pass = bool(str(current_platform_creds.get("email", "") or "").strip() and str(current_platform_creds.get("password", "") or "").strip())
            has_arl = bool(str(current_platform_creds.get("arl", "") or "").strip())
            is_fully_filled = has_email_pass or has_arl
        else:
            is_fully_filled = True
            for field_key in default_platform_fields.keys():
                v = current_platform_creds.get(field_key, "")
                if isinstance(default_platform_fields.get(field_key), bool):
                    pass
                elif not str(v).strip():
                    is_fully_filled = False
                    break
        # Tidal: only include if user has saved sessions (has logged in before).
        # Without sessions, loading Tidal opens the browser for OAuth - skip for users without a Tidal account.
        if platform_name == "Tidal" and is_fully_filled and not _tidal_has_saved_sessions(app_path):
            is_fully_filled = False
        if is_fully_filled:
            configured.append(platform_name)
    return sorted(configured)

def round_corners(image, radius):
    """Add rounded corners to an image using a mask."""
    from PIL import Image, ImageDraw
    
    # Ensure image has alpha channel
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Create a mask with rounded corners
    # Use (w-1, h-1) so the bottom-right corner arc stays inside the image;
    # [(0,0), (w,h)] clips the arc and makes the bottom-right appear square.
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    w, h = image.size
    draw.rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=radius, fill=255)
    
    # Apply the mask
    output = Image.new('RGBA', image.size, (0, 0, 0, 0))
    output.paste(image, (0, 0))
    output.putalpha(mask)
    
    return output

def create_placeholder_cover(size=COVER_SIZE):
    """Loads placeholder cover image from URL and applies rounded corners."""
    from PIL import Image, ImageDraw, ImageTk
    import io
    
    placeholder_url = "https://i.imgur.com/H7R8hBA.png"
    
    try:
        response = requests.get(placeholder_url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        if response.status_code == 200:
            img_data = io.BytesIO(response.content)
            img = Image.open(img_data)
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            img = round_corners(img, COVER_CORNER_RADIUS)
            return ImageTk.PhotoImage(img)
    except:
        pass
    
    # Fallback: create a simple gray placeholder if download fails
    img = Image.new('RGB', (size, size), color='#3d3d3d')
    draw = ImageDraw.Draw(img)
    note_color = '#666666'
    cx, cy = size // 2, size * 2 // 3
    r = size // 6
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=note_color)
    stem_x = cx + r - 1
    draw.line([(stem_x, cy - r + 2), (stem_x, size // 4)], fill=note_color, width=2)
    img = round_corners(img, COVER_CORNER_RADIUS)
    return ImageTk.PhotoImage(img)

def _show_placeholder_cover(item_iid):
    """Show placeholder cover for an item."""
    global _cover_load_requested, _cover_image_cache, _cover_hover_cache, tree
    _cover_load_requested.add(item_iid)
    placeholder = get_placeholder_cover()
    if placeholder and 'tree' in globals() and tree and tree.winfo_exists():
        try:
            if tree.exists(item_iid):
                tree.item(item_iid, image=placeholder)
                _cover_image_cache[item_iid] = placeholder  # Cache to prevent GC
                
                # Create hover version for placeholder
                try:
                    from PIL import Image, ImageTk
                    # Get the PIL Image from the PhotoImage (we need to recreate it)
                    # For placeholder, create a darkened version
                    placeholder_img = Image.new('RGB', (COVER_SIZE, COVER_SIZE), color='#3d3d3d')
                    placeholder_img = round_corners(placeholder_img, COVER_CORNER_RADIUS)
                    darkened_placeholder = create_darkened_cover(placeholder_img, opacity=0.7)
                    placeholder_hover = ImageTk.PhotoImage(darkened_placeholder)
                    _cover_hover_cache[item_iid] = placeholder_hover
                except:
                    pass  # If hover version fails, just use normal placeholder
        except:
            pass

def _try_lazy_load_artist_cover(item_iid, item_data, artist_id):
    """Try to lazy-load artist cover image for Tidal artists."""
    global orpheus_instance, _cover_load_requested, tree
    
    # Mark as requested to prevent duplicate requests
    _cover_load_requested.add(item_iid)
    
    # Check if we have the necessary globals
    if 'orpheus_instance' not in globals() or not orpheus_instance:
        _show_placeholder_cover(item_iid)
        return
    
    if not artist_id:
        _show_placeholder_cover(item_iid)
        return
    
    # Fetch artist image in background thread
    def fetch_artist_image():
        try:
            module_instance = orpheus_instance.load_module('tidal')
            if hasattr(module_instance, 'session') and hasattr(module_instance.session, 'get_artist'):
                artist_data = module_instance.session.get_artist(artist_id)
                
                # First, check if we already have the picture ID from the search results
                raw_result = item_data.get('raw_result')
                artist_image_id = None
                
                # Default fallback image UUID (same as python-tidal library uses)
                DEFAULT_ARTIST_IMG = "1e01cdb6-f15d-4d8b-8440-a047976c1cac"
                
                # Try to get picture from raw search result first (more reliable)
                if isinstance(raw_result, dict):
                    artist_image_id = raw_result.get('picture')
                
                # If not found in search result, try get_artist API response
                if not artist_image_id and isinstance(artist_data, dict):
                    # Check top-level fields first
                    artist_image_id = (
                        artist_data.get('picture') or
                        artist_data.get('image') or
                        artist_data.get('squareImage') or
                        artist_data.get('cover') or
                        artist_data.get('pictureId') or
                        artist_data.get('imageId') or
                        artist_data.get('selectedAlbumCoverFallback')  # Try this as fallback
                    )
                    
                    # Check nested structures if not found at top level
                    if not artist_image_id:
                        # Check if there's an 'images' object
                        images_obj = artist_data.get('images')
                        if isinstance(images_obj, dict):
                            artist_image_id = (
                                images_obj.get('picture') or
                                images_obj.get('cover') or
                                images_obj.get('squareImage')
                            )
                        # Check if there's a 'media' object
                        if not artist_image_id:
                            media_obj = artist_data.get('media')
                            if isinstance(media_obj, dict):
                                artist_image_id = media_obj.get('picture') or media_obj.get('cover')
                    
                    # Fallback to default image if still not found
                    if not artist_image_id:
                        artist_image_id = DEFAULT_ARTIST_IMG
                
                if artist_image_id:
                    from modules.tidal.interface import ModuleInterface
                    cover_url = ModuleInterface._generate_artwork_url(artist_image_id, size=56)
                    
                    # Update the item_data with the cover URL
                    item_data['cover_url'] = cover_url
                    # Update raw_result for future use (if it's a dict)
                    raw_result = item_data.get('raw_result')
                    if isinstance(raw_result, dict):
                        raw_result['picture'] = artist_image_id
                    
                    # Update UI on main thread - use default parameter to avoid closure issue
                    if 'app' in globals() and app and app.winfo_exists():
                        app.after(0, lambda url=cover_url: _on_artist_cover_fetched(item_iid, url))
                else:
                    # No image found - show placeholder
                    if 'app' in globals() and app and app.winfo_exists():
                        app.after(0, lambda: _show_placeholder_cover(item_iid))
        except Exception as e:
            # On error, show placeholder
            if 'app' in globals() and app and app.winfo_exists():
                app.after(0, lambda: _show_placeholder_cover(item_iid))
    
    # Start background thread
    import threading
    threading.Thread(target=fetch_artist_image, daemon=True).start()

def _on_artist_cover_fetched(item_iid, cover_url):
    """Called when an artist cover has been fetched."""
    global _cover_load_requested, tree
    
    # Check if item still exists and hasn't been loaded yet
    if 'tree' in globals() and tree and tree.winfo_exists():
        try:
            if tree.exists(item_iid) and item_iid not in _cover_image_cache:
                # Remove from requested set so we can load it
                if item_iid in _cover_load_requested:
                    _cover_load_requested.remove(item_iid)
                # Load the cover
                load_cover_from_url(cover_url, size=COVER_SIZE, item_iid=item_iid)
        except:
            pass

def get_placeholder_cover():
    """Returns the cached placeholder cover image, creating it if needed."""
    global _placeholder_cover_image
    if _placeholder_cover_image is None:
        _placeholder_cover_image = create_placeholder_cover(COVER_SIZE)
    return _placeholder_cover_image

def create_darkened_cover(img, opacity=0.7):
    """Create a darkened/transparent version of the cover image for hover effect."""
    from PIL import Image
    
    # Create a copy to avoid modifying the original
    darkened = img.copy()
    
    # Convert to RGBA if not already
    if darkened.mode != 'RGBA':
        darkened = darkened.convert('RGBA')
    
    # Create a dark overlay
    overlay = Image.new('RGBA', darkened.size, (0, 0, 0, int(255 * (1 - opacity))))
    
    # Composite the overlay onto the image
    darkened = Image.alpha_composite(darkened, overlay)
    
    return darkened

def _create_fade_in_frames(pil_img, size, bg_hex=TREEVIEW_BG_HEX):
    """Create a list of PhotoImages for fade-in (alpha steps from 0.2 to 1.0). pil_img must be RGBA."""
    from PIL import Image, ImageTk
    if pil_img.mode != 'RGBA':
        pil_img = pil_img.convert('RGBA')
    r, g, b, a = pil_img.split()
    bg_r = int(bg_hex[1:3], 16)
    bg_g = int(bg_hex[3:5], 16)
    bg_b = int(bg_hex[5:7], 16)
    bg_rgb = Image.new('RGB', (size, size), (bg_r, bg_g, bg_b))
    frames = []
    for step_alpha in [0.2, 0.4, 0.6, 0.8, 1.0]:
        a_scaled = a.point(lambda x: int(x * step_alpha))
        img_step = Image.merge('RGBA', (r, g, b, a_scaled))
        frame_rgb = bg_rgb.copy()
        frame_rgb.paste(img_step, (0, 0), a_scaled)
        frames.append(ImageTk.PhotoImage(frame_rgb))
    return frames

def load_cover_from_url(url, size=COVER_SIZE, item_iid=None, apply_to_iids=None):
    """
    Loads a cover image from URL asynchronously and updates the treeview.
    If apply_to_iids is a list, the same image is applied to all those item_iids (e.g. album track list).
    """
    def _apply_cover_on_main(img, darkened_img, item_iid, apply_to_iids=None):
        """Create Tk PhotoImages and update tree on main thread (PIL/Tk must not run in worker). Composites platform icon onto cover when available."""
        global tree, app, _cover_image_cache, _cover_hover_cache, _cover_hover_iid, _cover_fade_in_progress_count, search_results_data
        try:
            from PIL import ImageTk
            iids_to_apply = list(apply_to_iids) if apply_to_iids else ([item_iid] if item_iid else [])
            primary_iid = item_iid or (iids_to_apply[0] if iids_to_apply else None)
            platform_name = None
            if primary_iid and "search_results_data" in globals():
                item_data = next((d for d in search_results_data if str(d.get("tree_iid")) == str(primary_iid)), None)
                platform_name = (item_data or {}).get("platform") or None
            if platform_name:
                img = _composite_platform_icon_on_cover(img, platform_name, size)
                darkened_img = _composite_platform_icon_on_cover(darkened_img, platform_name, size)
            photo = ImageTk.PhotoImage(img)
            hover_photo = ImageTk.PhotoImage(darkened_img)
            for iid in iids_to_apply:
                _cover_image_cache[iid] = photo
                _cover_hover_cache[iid] = hover_photo
                try:
                    if 'tree' in globals() and tree and tree.winfo_exists() and tree.exists(iid) and _cover_hover_iid != iid:
                        tree.item(iid, image=photo)
                except Exception:
                    pass

            def _update_tree_with_fade():
                try:
                    if 'tree' not in globals() or not tree or not tree.winfo_exists() or not primary_iid or not tree.exists(primary_iid) or _cover_hover_iid == primary_iid:
                        return
                    if _cover_fade_in_progress_count >= COVER_FADE_MAX_CONCURRENT:
                        tree.item(primary_iid, image=photo)
                        return
                    _cover_fade_in_progress_count += 1
                    try:
                        frames = _create_fade_in_frames(img, size)
                    except Exception:
                        _cover_fade_in_progress_count -= 1
                        tree.item(primary_iid, image=photo)
                        return
                    def _run_fade(step=0):
                        try:
                            global _cover_fade_in_progress_count
                            if not tree.winfo_exists() or not tree.exists(primary_iid) or _cover_hover_iid == primary_iid:
                                _cover_fade_in_progress_count -= 1
                                return
                            if step < len(frames):
                                tree.item(primary_iid, image=frames[step])
                                if step < len(frames) - 1:
                                    app.after(COVER_FADE_IN_STEP_MS, lambda s=step + 1: _run_fade(s))
                                else:
                                    tree.item(primary_iid, image=photo)
                                    _cover_fade_in_progress_count -= 1
                        except Exception:
                            _cover_fade_in_progress_count -= 1
                    _run_fade(0)
                except Exception:
                    pass

            if 'app' in globals() and app and app.winfo_exists():
                app.after(0, _update_tree_with_fade)
        except Exception:
            fallback_iid = item_iid or (apply_to_iids[0] if apply_to_iids else None)
            if fallback_iid and 'app' in globals() and app and app.winfo_exists():
                app.after(0, lambda: _show_placeholder_cover(fallback_iid))

    def _load():
        nonlocal url  # Allow modifying the outer scope url variable
        global tree, app, _cover_image_cache, _cover_hover_cache, current_settings, search_results_data
        try:
            from PIL import Image
            import io
            
            # Debug output
            debug_mode = current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False) if 'current_settings' in globals() else False
            
            # Get platform name for logging
            platform_name = "Unknown"
            if item_iid and 'search_results_data' in globals():
                item_data = next((item for item in search_results_data if str(item.get('tree_iid')) == str(item_iid)), None)
                if item_data:
                    platform_name = item_data.get('platform', 'Unknown')
            
            # Add headers to avoid 403 errors from Tidal
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://tidal.com/',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'cross-site',
            }
            
            if debug_mode:
                print(f"[{platform_name} Cover Load] Loading: {url} for item {item_iid}")
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if debug_mode:
                print(f"[{platform_name} Cover Load] Response: HTTP {response.status_code} for item {item_iid}")
            
            # For YouTube, if maxresdefault.jpg returns 404, try fallback qualities
            if response.status_code == 404 and platform_name.lower() == 'youtube' and 'maxresdefault.jpg' in url:
                # Try fallback qualities in order: hqdefault.jpg -> mqdefault.jpg -> default.jpg
                fallback_qualities = ['hqdefault.jpg', 'mqdefault.jpg', 'default.jpg']
                for quality in fallback_qualities:
                    fallback_url = url.replace('maxresdefault.jpg', quality)
                    if debug_mode:
                        print(f"[{platform_name} Cover Load] maxresdefault.jpg not available, trying {quality}")
                    try:
                        fallback_response = requests.get(fallback_url, headers=headers, timeout=5)
                        if debug_mode:
                            print(f"[{platform_name} Cover Load] Fallback ({quality}) response: HTTP {fallback_response.status_code}")
                        if fallback_response.status_code == 200:
                            response = fallback_response
                            url = fallback_url  # Update URL for caching
                            break
                    except Exception as e:
                        if debug_mode:
                            print(f"[{platform_name} Cover Load] Fallback ({quality}) request failed: {e}")
                        continue
            
            # Handle successful response (200)
            if response.status_code == 200:
                img_data = io.BytesIO(response.content)
                img = Image.open(img_data)
                img = img.resize((size, size), Image.Resampling.LANCZOS)
                
                # Apply rounded corners
                img = round_corners(img, COVER_CORNER_RADIUS)
                
                # Hover (darkened) version — PIL only, safe in thread
                darkened_img = create_darkened_cover(img, opacity=0.7)
                
                # PhotoImage must be created on main thread to avoid GIL/crash
                if 'app' in globals() and app and app.winfo_exists():
                    app.after(0, lambda: _apply_cover_on_main(img, darkened_img, item_iid, apply_to_iids))
            elif response.status_code == 403:
                # 403 Forbidden - Tidal is blocking the request
                # Try retrying with 750x750.jpg as fallback (smaller sizes may not be available)
                if 'resources.tidal.com/images' in url:
                    # Check if URL already uses 750x750.jpg
                    # Match patterns like 80x80.jpg, 160x160.jpg, etc.
                    size_pattern = r'/(\d+x\d+)\.jpg'
                    match = re.search(size_pattern, url)
                    
                    if match and match.group(1) != '750x750':
                        # Retry with 750x750.jpg
                        fallback_url = re.sub(size_pattern, '/750x750.jpg', url)
                        if debug_mode:
                            print(f"[{platform_name} Cover Load] 403 for {url}, retrying with {fallback_url}")
                        
                        try:
                            fallback_response = requests.get(fallback_url, headers=headers, timeout=5)
                            if debug_mode:
                                print(f"[{platform_name} Cover Load] Fallback response: HTTP {fallback_response.status_code} for item {item_iid}")
                            
                            if fallback_response.status_code == 200:
                                # Success! Use the fallback image
                                img_data = io.BytesIO(fallback_response.content)
                                img = Image.open(img_data)
                                img = img.resize((size, size), Image.Resampling.LANCZOS)
                                
                                # Apply rounded corners
                                img = round_corners(img, COVER_CORNER_RADIUS)
                                
                                # Hover (darkened) version — PIL only, safe in thread
                                darkened_img = create_darkened_cover(img, opacity=0.7)
                                
                                # PhotoImage must be created on main thread to avoid GIL/crash
                                if 'app' in globals() and app and app.winfo_exists():
                                    app.after(0, lambda: _apply_cover_on_main(img, darkened_img, item_iid, apply_to_iids))
                                return  # Success, exit early
                        except Exception as e:
                            if debug_mode:
                                print(f"[{platform_name} Cover Load] Fallback request failed: {e}")
                
                # If we get here, both original and fallback failed - show placeholder
                if debug_mode:
                    print(f"[{platform_name} Cover Load] 403 Forbidden for item {item_iid}, showing placeholder")
                if 'app' in globals() and app and app.winfo_exists():
                    app.after(0, lambda: _show_placeholder_cover(item_iid))
            elif response.status_code == 404:
                # 404 Not Found - show placeholder
                if debug_mode:
                    print(f"[{platform_name} Cover Load] 404 Not Found for item {item_iid}, showing placeholder")
                if 'app' in globals() and app and app.winfo_exists():
                    app.after(0, lambda: _show_placeholder_cover(item_iid))
        except Exception as e:
            if debug_mode:
                print(f"[{platform_name} Cover Load] Exception loading cover for item {item_iid}: {e}")
            # Show placeholder on error
            if 'app' in globals() and app and app.winfo_exists():
                app.after(0, lambda: _show_placeholder_cover(item_iid))
    
    threading.Thread(target=_load, daemon=True).start()

# Number of items below viewport to include for cover loading (fixes last covers not loading when maximized)
COVER_LOAD_VIEWPORT_BUFFER = 25

def get_visible_tree_items():
    """Get the list of item IDs currently visible in the treeview, plus a buffer below so the last covers load when maximized."""
    global tree
    visible_items = []
    try:
        if 'tree' not in globals() or not tree or not tree.winfo_exists():
            return visible_items
        
        # Get all children
        all_items = list(tree.get_children())
        if not all_items:
            return visible_items
        
        # Check each item's visibility by its bbox (bbox can miss bottom rows when window is large)
        for item_iid in all_items:
            try:
                bbox = tree.bbox(item_iid)
                if bbox:  # bbox returns empty tuple if not visible
                    visible_items.append(item_iid)
            except:
                pass
        
        # Include items just below the viewport so scrolling loads them and last rows aren't missed (bbox quirk when maximized)
        if visible_items:
            visible_set = set(visible_items)
            last_visible_iid = visible_items[-1]
            try:
                last_idx = all_items.index(last_visible_iid)
            except ValueError:
                last_idx = -1
            for i in range(last_idx + 1, min(last_idx + 1 + COVER_LOAD_VIEWPORT_BUFFER, len(all_items))):
                iid = all_items[i]
                if iid not in visible_set:
                    visible_items.append(iid)
                    visible_set.add(iid)
    except:
        pass
    
    return visible_items

def lazy_load_visible_covers():
    """Load covers only for currently visible items in the treeview."""
    global search_results_data, _cover_load_requested, _cover_image_cache, _cover_hover_cache, tree
    
    try:
        visible_items = get_visible_tree_items()
        
        # Process up to 25 items per call; take first N that still need loading so we make progress toward bottom rows
        max_items_per_call = 25
        items_to_process = []
        for item_iid in visible_items:
            if item_iid in _cover_image_cache or item_iid in _cover_load_requested:
                continue
            items_to_process.append(item_iid)
            if len(items_to_process) >= max_items_per_call:
                break
        
        for item_iid in items_to_process:
            # Skip if already loaded or already requested
            if item_iid in _cover_image_cache or item_iid in _cover_load_requested:
                continue
            
            # Find the cover URL for this item
            item_data = next((item for item in search_results_data if str(item.get('tree_iid')) == str(item_iid)), None)
            if item_data:
                if item_data.get('cover_url'):
                    # Has cover URL - load it
                    debug_mode = current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False) if 'current_settings' in globals() else False
                    if debug_mode:
                        platform_name = item_data.get('platform', 'Unknown')
                        search_type = item_data.get('type', '').lower() if item_data.get('type') else ''
                        # For artist search, name is in 'artist'; for others use 'title'
                        display_name = (item_data.get('artist') or item_data.get('title') or 'Unknown').strip() or 'Unknown'
                        raw_result = item_data.get('raw_result')
                        square_image_info = ""
                        if platform_name.lower() == 'tidal' and isinstance(raw_result, dict):
                            square_image_info = f", squareImage in raw_result: {raw_result.get('squareImage') is not None}"
                        print(f"[{platform_name} Cover] {search_type.capitalize()} '{display_name}' (item {item_iid}): cover_url={item_data['cover_url']}{square_image_info}")
                    _cover_load_requested.add(item_iid)
                    load_cover_from_url(item_data['cover_url'], size=COVER_SIZE, item_iid=item_iid)
                else:
                    # No cover URL - try lazy-loading for Tidal artists and YouTube channels/playlists
                    platform_name = item_data.get('platform', '').lower() if item_data.get('platform') else ''
                    search_type = item_data.get('type', '').lower() if item_data.get('type') else ''
                    raw_result = item_data.get('raw_result')
                    
                    # For YouTube channels, try to fetch the thumbnail lazily (only if not already requested)
                    if platform_name == 'youtube' and search_type == 'artist' and item_data.get('id'):
                        channel_id = item_data.get('id')
                        # Check if we've already requested this thumbnail or are currently fetching it
                        if item_iid not in _cover_load_requested and item_iid not in _youtube_thumbnail_fetching:
                            # Limit concurrent fetches to avoid overwhelming the system
                            if len(_youtube_thumbnail_fetching) >= _youtube_max_concurrent_fetches:
                                # Queue this request for later
                                _youtube_thumbnail_queue.append(('channel', item_iid, channel_id, item_data))
                                _show_placeholder_cover(item_iid)
                                continue
                            
                            _cover_load_requested.add(item_iid)
                            _youtube_thumbnail_fetching.add(item_iid)
                            debug_mode = current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False) if 'current_settings' in globals() else False
                            if debug_mode:
                                channel_name = item_data.get('title', 'Unknown')
                                print(f"[YouTube Cover] Channel '{channel_name}' (item {item_iid}): No thumbnail in search results, fetching channel info")
                            
                            # Fetch channel thumbnail in background thread
                            def fetch_channel_thumbnail():
                                try:
                                    if 'orpheus_instance' not in globals() or not orpheus_instance:
                                        return
                                    module_instance = orpheus_instance.load_module('youtube')
                                    if hasattr(module_instance, 'api') and hasattr(module_instance.api, 'get_channel_thumbnail'):
                                        thumbnail_url = module_instance.api.get_channel_thumbnail(channel_id)
                                        if thumbnail_url:
                                            # Upgrade to full-size if needed
                                            thumbnail_url = _get_fullsize_cover_url(thumbnail_url, 'youtube', None)
                                            # Update item_data and load cover
                                            item_data['cover_url'] = thumbnail_url
                                            if 'app' in globals() and app and app.winfo_exists():
                                                app.after(0, lambda: load_cover_from_url(thumbnail_url, size=COVER_SIZE, item_iid=item_iid))
                                except Exception as e:
                                    if debug_mode:
                                        print(f"[YouTube Cover] Error fetching channel thumbnail: {e}")
                                finally:
                                    # Remove from fetching set when done and process next in queue
                                    if item_iid in _youtube_thumbnail_fetching:
                                        _youtube_thumbnail_fetching.remove(item_iid)
                                    # Process next item in queue if any
                                    _process_youtube_thumbnail_queue()
                            
                            threading.Thread(target=fetch_channel_thumbnail, daemon=True).start()
                        # Show placeholder while loading
                        _show_placeholder_cover(item_iid)
                        continue
                    
                    # For YouTube playlists, try to fetch the thumbnail lazily (only if not already requested)
                    elif platform_name == 'youtube' and search_type == 'playlist' and item_data.get('id'):
                        playlist_id = item_data.get('id')
                        # Check if we've already requested this thumbnail or are currently fetching it
                        if item_iid not in _cover_load_requested and item_iid not in _youtube_thumbnail_fetching:
                            # Limit concurrent fetches to avoid overwhelming the system
                            if len(_youtube_thumbnail_fetching) >= _youtube_max_concurrent_fetches:
                                # Queue this request for later
                                _youtube_thumbnail_queue.append(('playlist', item_iid, playlist_id, item_data))
                                _show_placeholder_cover(item_iid)
                                continue
                            
                            _cover_load_requested.add(item_iid)
                            _youtube_thumbnail_fetching.add(item_iid)
                            debug_mode = current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False) if 'current_settings' in globals() else False
                            if debug_mode:
                                playlist_name = item_data.get('title', 'Unknown')
                                print(f"[YouTube Cover] Playlist '{playlist_name}' (item {item_iid}): No thumbnail in search results, fetching playlist info")
                            
                            # Fetch playlist thumbnail in background thread
                            def fetch_playlist_thumbnail():
                                try:
                                    if 'orpheus_instance' not in globals() or not orpheus_instance:
                                        return
                                    module_instance = orpheus_instance.load_module('youtube')
                                    if hasattr(module_instance, 'api') and hasattr(module_instance.api, 'get_playlist_info'):
                                        playlist_info = module_instance.api.get_playlist_info(playlist_id)
                                        if playlist_info:
                                            thumbnail_url = playlist_info.get('thumbnail')
                                            if thumbnail_url:
                                                # Upgrade to full-size if needed
                                                thumbnail_url = _get_fullsize_cover_url(thumbnail_url, 'youtube', playlist_info)
                                                # Update item_data and load cover
                                                item_data['cover_url'] = thumbnail_url
                                                if 'app' in globals() and app and app.winfo_exists():
                                                    app.after(0, lambda: load_cover_from_url(thumbnail_url, size=COVER_SIZE, item_iid=item_iid))
                                except Exception as e:
                                    if debug_mode:
                                        print(f"[YouTube Cover] Error fetching playlist thumbnail: {e}")
                                finally:
                                    # Remove from fetching set when done and process next in queue
                                    if item_iid in _youtube_thumbnail_fetching:
                                        _youtube_thumbnail_fetching.remove(item_iid)
                                    # Process next item in queue if any
                                    _process_youtube_thumbnail_queue()
                            
                            threading.Thread(target=fetch_playlist_thumbnail, daemon=True).start()
                        # Show placeholder while loading
                        _show_placeholder_cover(item_iid)
                        continue
                    
                    # For Tidal artists, try to fetch the image lazily
                    # Check if it's a Tidal artist search result
                    elif platform_name == 'tidal' and search_type == 'artist' and raw_result:
                        # Check multiple possible field names for artist image ID (same as search function)
                        # Default fallback image UUID (same as python-tidal library uses)
                        DEFAULT_ARTIST_IMG = "1e01cdb6-f15d-4d8b-8440-a047976c1cac"
                        
                        picture_id = None
                        if isinstance(raw_result, dict):
                            # Check all possible fields (same as search function)
                            picture_id = (
                                raw_result.get('picture') or 
                                raw_result.get('image') or 
                                raw_result.get('squareImage') or 
                                raw_result.get('cover') or
                                raw_result.get('pictureId') or
                                raw_result.get('imageId') or
                                (raw_result.get('images', {}).get('picture') if isinstance(raw_result.get('images'), dict) else None) or
                                (raw_result.get('images', {}).get('cover') if isinstance(raw_result.get('images'), dict) else None) or
                                (raw_result.get('images', {}).get('squareImage') if isinstance(raw_result.get('images'), dict) else None)
                            )
                        
                        # Fallback to default image if none found
                        if not picture_id:
                            picture_id = DEFAULT_ARTIST_IMG
                        
                        # Debug output
                        debug_mode = current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False) if 'current_settings' in globals() else False
                        if debug_mode:
                            artist_name = item_data.get('title', 'Unknown')
                            from_search = isinstance(raw_result, dict) and any([
                                raw_result.get('picture'),
                                raw_result.get('image'),
                                raw_result.get('squareImage'),
                                raw_result.get('cover'),
                                raw_result.get('pictureId'),
                                raw_result.get('imageId'),
                            ])
                            print(f"[{platform_name.capitalize()} Cover] Artist '{artist_name}' (item {item_iid}): picture_id={picture_id} (from_search={from_search})")
                        
                        # Generate cover URL and load it
                        # Use 750x750.jpg for artists as it's more reliably available
                        cover_url = f'https://resources.tidal.com/images/{picture_id.replace("-", "/")}/750x750.jpg'
                        item_data['cover_url'] = cover_url
                        _cover_load_requested.add(item_iid)
                        load_cover_from_url(cover_url, size=COVER_SIZE, item_iid=item_iid)
                    elif platform_name == 'tidal' and search_type == 'playlist' and raw_result:
                        # For Tidal playlists, check if squareImage is in raw_result
                        debug_mode = current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False) if 'current_settings' in globals() else False
                        if isinstance(raw_result, dict):
                            square_image = raw_result.get('squareImage') or raw_result.get('image') or raw_result.get('cover')
                            if debug_mode:
                                playlist_name = item_data.get('title', 'Unknown')
                                print(f"[{platform_name.capitalize()} Cover] Playlist '{playlist_name}' (item {item_iid}): squareImage={square_image}, available_keys={list(raw_result.keys())}")
                            if square_image:
                                # Use 750x750.jpg for playlists as it's more reliably available
                                cover_url = f'https://resources.tidal.com/images/{square_image.replace("-", "/")}/750x750.jpg'
                                item_data['cover_url'] = cover_url
                                _cover_load_requested.add(item_iid)
                                load_cover_from_url(cover_url, size=COVER_SIZE, item_iid=item_iid)
                            elif debug_mode:
                                print(f"[{platform_name.capitalize()} Cover] Playlist '{playlist_name}' (item {item_iid}): No squareImage found, showing placeholder")
                                _show_placeholder_cover(item_iid)
                        else:
                            if debug_mode:
                                print(f"[{platform_name.capitalize()} Cover] Playlist (item {item_iid}): raw_result is not a dict, type={type(raw_result)}")
                            _show_placeholder_cover(item_iid)
                    else:
                        # Not Tidal artist - show placeholder
                        _show_placeholder_cover(item_iid)
    except:
        pass

def on_tree_scroll(*args):
    """Handle treeview scroll event to trigger lazy loading."""
    # Schedule lazy loading after a delay to avoid excessive calls and reduce CPU usage
    global app
    try:
        if 'app' in globals() and app and app.winfo_exists():
            # Cancel previous scheduled call if exists
            if hasattr(on_tree_scroll, '_scheduled_id') and on_tree_scroll._scheduled_id:
                try:
                    app.after_cancel(on_tree_scroll._scheduled_id)
                except:
                    pass
            # Schedule new call with longer delay (debounce) to reduce CPU usage
            # Increased from 50ms to 200ms to reduce load when scrolling quickly
            on_tree_scroll._scheduled_id = app.after(200, lazy_load_visible_covers)
    except:
        pass

def _process_youtube_thumbnail_queue():
    """Process the next item in the YouTube thumbnail fetch queue."""
    global _youtube_thumbnail_queue, _youtube_thumbnail_fetching, _cover_load_requested, _youtube_max_concurrent_fetches
    
    # Process items from queue if we have capacity
    while len(_youtube_thumbnail_fetching) < _youtube_max_concurrent_fetches and _youtube_thumbnail_queue:
        item_type, item_iid, item_id, item_data = _youtube_thumbnail_queue.pop(0)
        
        # Skip if already loaded or requested
        if item_iid in _cover_image_cache or item_iid in _cover_load_requested or item_iid in _youtube_thumbnail_fetching:
            continue
        
        _cover_load_requested.add(item_iid)
        _youtube_thumbnail_fetching.add(item_iid)
        
        debug_mode = current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False) if 'current_settings' in globals() else False
        
        if item_type == 'channel':
            if debug_mode:
                channel_name = item_data.get('title', 'Unknown')
                print(f"[YouTube Cover] Channel '{channel_name}' (item {item_iid}): Processing from queue")
            
            def fetch_channel_thumbnail():
                try:
                    if 'orpheus_instance' not in globals() or not orpheus_instance:
                        return
                    module_instance = orpheus_instance.load_module('youtube')
                    if hasattr(module_instance, 'api') and hasattr(module_instance.api, 'get_channel_thumbnail'):
                        thumbnail_url = module_instance.api.get_channel_thumbnail(item_id)
                        if thumbnail_url:
                            thumbnail_url = _get_fullsize_cover_url(thumbnail_url, 'youtube', None)
                            item_data['cover_url'] = thumbnail_url
                            if 'app' in globals() and app and app.winfo_exists():
                                app.after(0, lambda: load_cover_from_url(thumbnail_url, size=COVER_SIZE, item_iid=item_iid))
                except Exception as e:
                    if debug_mode:
                        print(f"[YouTube Cover] Error fetching channel thumbnail: {e}")
                finally:
                    if item_iid in _youtube_thumbnail_fetching:
                        _youtube_thumbnail_fetching.remove(item_iid)
                    _process_youtube_thumbnail_queue()
            
            threading.Thread(target=fetch_channel_thumbnail, daemon=True).start()
        
        elif item_type == 'playlist':
            if debug_mode:
                playlist_name = item_data.get('title', 'Unknown')
                print(f"[YouTube Cover] Playlist '{playlist_name}' (item {item_iid}): Processing from queue")
            
            def fetch_playlist_thumbnail():
                try:
                    if 'orpheus_instance' not in globals() or not orpheus_instance:
                        return
                    module_instance = orpheus_instance.load_module('youtube')
                    if hasattr(module_instance, 'api') and hasattr(module_instance.api, 'get_playlist_info'):
                        playlist_info = module_instance.api.get_playlist_info(item_id)
                        if playlist_info:
                            thumbnail_url = playlist_info.get('thumbnail')
                            if thumbnail_url:
                                thumbnail_url = _get_fullsize_cover_url(thumbnail_url, 'youtube', playlist_info)
                                item_data['cover_url'] = thumbnail_url
                                if 'app' in globals() and app and app.winfo_exists():
                                    app.after(0, lambda: load_cover_from_url(thumbnail_url, size=COVER_SIZE, item_iid=item_iid))
                except Exception as e:
                    if debug_mode:
                        print(f"[YouTube Cover] Error fetching playlist thumbnail: {e}")
                finally:
                    if item_iid in _youtube_thumbnail_fetching:
                        _youtube_thumbnail_fetching.remove(item_iid)
                    _process_youtube_thumbnail_queue()
            
            threading.Thread(target=fetch_playlist_thumbnail, daemon=True).start()

def clear_cover_load_state():
    """Clear the cover loading state (called when clearing search results)."""
    global _cover_load_requested, _youtube_thumbnail_fetching, _youtube_thumbnail_queue
    _cover_load_requested.clear()
    _youtube_thumbnail_fetching.clear()
    _youtube_thumbnail_queue.clear()

def setup_preview_tags(tree_widget):
    """Setup tags for preview button styling and alternating row colors."""
    # Tag for playing items - blue foreground for stop icon
    tree_widget.tag_configure("playing", foreground="#1F6AA5")
    # Alternating row background (odd = slightly lighter, even = default)
    tree_widget.tag_configure("oddrow", background="#222323")
    tree_widget.tag_configure("evenrow", background=TREEVIEW_BG_HEX)
    # Row hover highlight (set foreground too so it persists when hover is the only tag)
    tree_widget.tag_configure("hover", background="#2B2B2B", foreground="#DCE4EE")

def _row_tag_for_index(idx):
    """Return oddrow or evenrow based on row index (0-based)."""
    return "oddrow" if idx % 2 == 0 else "evenrow"

def _tree_row_tags(item_iid, playing=False):
    """Return tags for a tree item, preserving oddrow/evenrow when updating for playing state."""
    try:
        if 'tree' in globals() and tree and tree.winfo_exists():
            current = tree.item(item_iid, 'tags')
            if "oddrow" in current or "evenrow" in current:
                row_tag = "oddrow" if "oddrow" in current else "evenrow"
            else:
                idx = tree.index(item_iid)
                row_tag = _row_tag_for_index(idx)
            return (row_tag, "playing") if playing else (row_tag,)
    except Exception:
        pass
    return ("oddrow", "playing") if playing else ("oddrow",)

def _start_pulse_animation():
    """Start the pulsing animation for the currently playing preview icon."""
    global _pulse_after_id, _pulse_state, _currently_playing_preview_iid, tree, _preview_hover_iid
    _stop_pulse_animation()  # Stop any existing pulse
    
    if _currently_playing_preview_iid is None:
        return
    
    def pulse():
        global _pulse_state, _pulse_after_id, _currently_playing_preview_iid, tree, _preview_hover_iid
        if _currently_playing_preview_iid is None or ('tree' not in globals() or not tree or not tree.winfo_exists()):
            _stop_pulse_animation()
            return
        
        try:
            # Toggle pulse state
            _pulse_state = not _pulse_state
            
            # Get current values
            current_values = list(tree.item(_currently_playing_preview_iid, 'values'))
            if len(current_values) > 0:
                # Only pulse if not hovering (hover has its own icon)
                if _preview_hover_iid != _currently_playing_preview_iid:
                    if _pulse_state:
                        current_values[0] = PREVIEW_STOP_ICON_PULSE
                    else:
                        current_values[0] = PREVIEW_STOP_ICON
                    tree.item(_currently_playing_preview_iid, values=tuple(current_values), tags=_tree_row_tags(_currently_playing_preview_iid, playing=True))
            
            # Schedule next pulse (500ms interval for smooth animation)
            if 'app' in globals() and app and app.winfo_exists():
                _pulse_after_id = app.after(500, pulse)
        except:
            _stop_pulse_animation()
    
    # Start first pulse
    if 'app' in globals() and app and app.winfo_exists():
        _pulse_after_id = app.after(500, pulse)

def _stop_pulse_animation():
    """Stop the pulsing animation."""
    global _pulse_after_id, _pulse_state, _currently_playing_preview_iid, tree
    if _pulse_after_id is not None and 'app' in globals() and app and app.winfo_exists():
        try:
            app.after_cancel(_pulse_after_id)
        except:
            pass
        _pulse_after_id = None
    _pulse_state = False

def _start_loading_animation(item_iid):
    """Start the walking dots animation for the loading icon."""
    global _loading_after_id, _loading_dot_position, _loading_animation_iid, tree
    _stop_loading_animation()  # Stop any existing loading animation
    
    if item_iid is None:
        return
    
    _loading_animation_iid = item_iid
    
    def animate_dots():
        global _loading_after_id, _loading_dot_position, _loading_animation_iid, tree
        # Check if this item is still supposed to be animating
        if _loading_animation_iid != item_iid or item_iid is None or ('tree' not in globals() or not tree or not tree.winfo_exists()):
            _stop_loading_animation()
            return
        
        try:
            # Get current values
            current_values = list(tree.item(item_iid, 'values'))
            if len(current_values) > 0:
                # Check if current icon is still a loading state (might have been changed by another function)
                current_icon = current_values[0] if current_values else ""
                # If icon was changed to something other than loading states, stop animation
                if current_icon not in LOADING_ANIMATION_FRAMES and current_icon != PREVIEW_LOADING_ICON:
                    _stop_loading_animation()
                    return
                
                # Create walking dots pattern: " . ", " .. ", " ... ", then repeat
                current_values[0] = LOADING_ANIMATION_FRAMES[_loading_dot_position]
                
                tree.item(item_iid, values=tuple(current_values))
                
                # Move to next position (0 -> 1 -> 2 -> 0)
                _loading_dot_position = (_loading_dot_position + 1) % len(LOADING_ANIMATION_FRAMES)
            
            # Schedule next animation frame (300ms for smooth walking effect)
            if 'app' in globals() and app and app.winfo_exists():
                _loading_after_id = app.after(300, animate_dots)
        except:
            _stop_loading_animation()
    
    # Start first frame
    _loading_dot_position = 0
    if 'app' in globals() and app and app.winfo_exists():
        _loading_after_id = app.after(300, animate_dots)

def _stop_loading_animation():
    """Stop the walking dots animation."""
    global _loading_after_id, _loading_dot_position, _loading_animation_iid
    if _loading_after_id is not None and 'app' in globals() and app and app.winfo_exists():
        try:
            app.after_cancel(_loading_after_id)
        except:
            pass
        _loading_after_id = None
    _loading_dot_position = 0
    _loading_animation_iid = None
    
    # Restore normal stop icon if item is still playing
    if _currently_playing_preview_iid is not None and ('tree' in globals() and tree and tree.winfo_exists()):
        try:
            current_values = list(tree.item(_currently_playing_preview_iid, 'values'))
            if len(current_values) > 0 and _preview_hover_iid != _currently_playing_preview_iid:
                current_values[0] = PREVIEW_STOP_ICON
                tree.item(_currently_playing_preview_iid, values=tuple(current_values), tags=_tree_row_tags(_currently_playing_preview_iid, playing=True))
        except:
            pass

def _clear_expand_long_loading_message():
    """Cancel 8s delayed message and hide 'Fetching all data... ' label."""
    global _expand_long_loading_after_id, _expand_loading_dots_after_id
    if _expand_long_loading_after_id is not None and 'app' in globals() and app and app.winfo_exists():
        try:
            app.after_cancel(_expand_long_loading_after_id)
        except Exception:
            pass
        _expand_long_loading_after_id = None
    if _expand_loading_dots_after_id is not None and 'app' in globals() and app and app.winfo_exists():
        try:
            app.after_cancel(_expand_loading_dots_after_id)
        except Exception:
            pass
        _expand_loading_dots_after_id = None
    if '_expand_loading_label' in globals() and _expand_loading_label and _expand_loading_label.winfo_exists():
        try:
            _expand_loading_label.pack_forget()
        except Exception:
            pass

def _expand_loading_dots_tick():
    """Update walking dots in the long-loading message (e.g. 'Fetching all data...' or 'Searching all platforms...')."""
    global _expand_loading_dots_after_id, _expand_loading_dots_position, _expand_loading_message_prefix
    if '_expand_loading_label' not in globals() or not _expand_loading_label:
        return
    if not _expand_loading_label.winfo_ismapped():
        return
    try:
        prefix = _expand_loading_message_prefix if '_expand_loading_message_prefix' in globals() else "Fetching all data"
        dots = LOADING_ANIMATION_FRAMES[_expand_loading_dots_position]
        _expand_loading_label.configure(text=f"{prefix}{dots} (this can take up to ~1 minute)")
        _expand_loading_dots_position = (_expand_loading_dots_position + 1) % len(LOADING_ANIMATION_FRAMES)
    except Exception:
        pass
    if 'app' in globals() and app and app.winfo_exists():
        _expand_loading_dots_after_id = app.after(300, _expand_loading_dots_tick)

def _show_expand_long_loading_message():
    """Show long-loading message with walking dots (called after 8s). Uses _expand_loading_message_prefix."""
    global _expand_long_loading_after_id, _expand_loading_dots_after_id, _expand_loading_dots_position, _expand_loading_message_prefix
    _expand_long_loading_after_id = None  # already fired
    if '_expand_loading_label' not in globals() or not _expand_loading_label:
        return
    try:
        prefix = _expand_loading_message_prefix if '_expand_loading_message_prefix' in globals() else "Fetching all data"
        _expand_loading_dots_position = 0
        _expand_loading_label.configure(text=prefix + LOADING_ANIMATION_FRAMES[0] + " (this can take up to ~1 minute)")
        _expand_loading_label.pack(side="left", anchor="w", padx=(12, 0), pady=0)
        if 'app' in globals() and app and app.winfo_exists():
            _expand_loading_dots_after_id = app.after(300, _expand_loading_dots_tick)
    except Exception:
        pass

def toggle_preview_playback(item_iid, preview_url=None):
    """
    Toggle audio preview playback for a tree item.
    If the same item is playing, stop it. Otherwise, start playing.
    """
    global _currently_playing_preview_iid, _preview_hover_iid, tree, _current_volume, app, _lazy_loading_preview_iid
    
    try:
        if _currently_playing_preview_iid == item_iid:
            # Currently playing this item - stop it
            stop_audio()
            _currently_playing_preview_iid = None
            _lazy_loading_preview_iid = None  # Cancel any pending lazy loads
            _stop_pulse_animation()  # Stop pulsing animation
            _stop_loading_animation()  # Stop loading animation
            # Hide volume control
            hide_volume_control()
            # Update the icon back to play (enlarged if still hovering)
            if 'tree' in globals() and tree and tree.winfo_exists():
                if _preview_hover_iid == item_iid:
                    _enlarge_preview_icon(item_iid)  # Show enlarged play icon
                else:
                    update_preview_icon(item_iid, playing=False)
            return False
        else:
            # Stop any currently playing preview
            if _currently_playing_preview_iid:
                stop_audio()
                old_iid = _currently_playing_preview_iid
                _stop_pulse_animation()  # Stop pulsing animation
                if 'tree' in globals() and tree and tree.winfo_exists():
                    update_preview_icon(old_iid, playing=False)
            
            # Start playing the new preview
            if preview_url:
                _currently_playing_preview_iid = item_iid
                
                # Always show loading and run playback in a background thread so that:
                # - Loading dots show for all platforms (Apple Music, Beatport, Beatsource, Deezer, etc.) on macOS,
                #   not just Qobuz/SoundCloud/Spotify (which show loading during lazy URL fetch).
                # - UI does not freeze during download on macOS/Linux (play_audio downloads then plays).
                # - Windows already used background thread for conversion; same pattern for everyone.
                if 'tree' in globals() and tree and tree.winfo_exists():
                    try:
                        current_values = list(tree.item(item_iid, 'values'))
                        if current_values:
                            current_values[0] = PREVIEW_LOADING_ICON
                            tree.item(item_iid, values=tuple(current_values))
                            _start_loading_animation(item_iid)
                    except Exception:
                        pass
                
                target_iid = item_iid
                def play_in_background():
                    global _currently_playing_preview_iid
                    try:
                        if _currently_playing_preview_iid != target_iid:
                            print(f"[Preview] Playback cancelled for {target_iid}")
                            return
                        
                        result = play_audio(preview_url)
                        
                        if _currently_playing_preview_iid != target_iid:
                            stop_audio()
                            return
                        
                        # Deferred playback (e.g. Windows WAV on main thread)
                        if isinstance(result, tuple) and result[0] == 'play_file':
                            file_path = result[1]
                            if 'app' in globals() and app and app.winfo_exists():
                                app.after(0, lambda: _play_file_on_main_thread(target_iid, file_path))
                            return
                        
                        success = bool(result)
                        if 'app' in globals() and app and app.winfo_exists():
                            app.after(0, lambda: _on_preview_started(target_iid, success))
                    except Exception as e:
                        print(f"[Preview] Error during playback: {e}")
                        if 'app' in globals() and app and app.winfo_exists():
                            app.after(0, lambda: _on_preview_started(target_iid, False))
                
                threading.Thread(target=play_in_background, daemon=True).start()
                return True
            else:
                print(f"[Preview] No preview URL for item {item_iid}")
                _currently_playing_preview_iid = None
                return False
    except Exception as e:
        print(f"[Preview] Error toggling playback: {e}")
        _currently_playing_preview_iid = None
        return False

def _play_file_on_main_thread(item_iid, file_path):
    """Play a file using winsound on the main thread (required for proper stop functionality)."""
    global _currently_playing_preview_iid, _preview_hover_iid, _current_volume
    
    try:
        # Check if we should still play (user might have stopped)
        if _currently_playing_preview_iid != item_iid:
            return
        
        system = platform.system()
        if system == "Windows":
            import winsound
            
            # Set volume before playing
            wave_volume = int((_current_volume / 100) * 0xFFFF)
            stereo_volume = (wave_volume << 16) | wave_volume
            ctypes.windll.winmm.waveOutSetVolume(0, stereo_volume)
            
            # Play with winsound (async so it doesn't block)
            if _audio_debug():
                print(f"[Audio] Playing on main thread: {os.path.basename(file_path)}")
            winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            # Call _on_preview_started after a tiny delay to ensure playback actually started
            # This ensures the UI only updates after "[Audio] Playing on main thread:" appears
            if 'app' in globals() and app and app.winfo_exists():
                app.after(50, lambda: _on_preview_started(item_iid, True))
            else:
                _on_preview_started(item_iid, True)
        else:
            # On other systems, just call _on_preview_started with success
            _on_preview_started(item_iid, True)
    except Exception as e:
        if _audio_debug():
            print(f"[Audio] Error playing file on main thread: {e}")
        _on_preview_started(item_iid, False)

def _on_preview_started(item_iid, success):
    """Called when a preview with conversion has finished loading and started playing."""
    global _currently_playing_preview_iid, _preview_hover_iid, tree, _current_volume
    
    try:
        # Stop loading animation since we're done loading
        _stop_loading_animation()
        
        # Check if this item is still supposed to be playing (user might have pressed stop)
        if _currently_playing_preview_iid != item_iid:
            # User pressed stop or switched to another preview - don't update UI
            return
        
        if success:
            # Update icon to stop icon (playing)
            if 'tree' in globals() and tree and tree.winfo_exists():
                if _preview_hover_iid == item_iid:
                    _enlarge_preview_icon(item_iid)
                else:
                    update_preview_icon(item_iid, playing=True)
            # Show volume control and set initial volume
            show_volume_control()
            set_audio_volume(_current_volume)
            # Start pulsing animation
            _start_pulse_animation()
        else:
            # Playback failed - restore play icon
            _currently_playing_preview_iid = None
            _stop_pulse_animation()
            if 'tree' in globals() and tree and tree.winfo_exists():
                update_preview_icon(item_iid, playing=False)
    except Exception as e:
        print(f"[Preview] Error in _on_preview_started: {e}")

def update_preview_icon(item_iid, playing=False, has_preview=True):
    """Update the preview icon in the treeview for a specific item."""
    global tree, _loading_animation_iid
    try:
        # Don't update icon if this item is currently showing loading animation
        if _loading_animation_iid == item_iid:
            return
        
        if 'tree' in globals() and tree and tree.winfo_exists():
            current_values = list(tree.item(item_iid, 'values'))
            if len(current_values) > 0:  # Preview column is at index 0
                # Also check if current value is a loading animation state
                current_icon = current_values[0] if current_values else ""
                # Also check if current value is a loading animation state
                current_icon = current_values[0] if current_values else ""
                if current_icon in LOADING_ANIMATION_FRAMES or current_icon == PREVIEW_LOADING_ICON:
                    # Item is showing loading animation, don't overwrite it
                    return
                
                if not has_preview:
                    current_values[0] = PREVIEW_UNAVAILABLE
                    tree.item(item_iid, values=tuple(current_values), tags=_tree_row_tags(item_iid, playing=False))
                elif playing and _loading_animation_iid != item_iid:
                    # Only show stop icon if we're actually playing (not loading)
                    current_values[0] = PREVIEW_STOP_ICON
                    tree.item(item_iid, values=tuple(current_values), tags=_tree_row_tags(item_iid, playing=True))
                else:
                    current_values[0] = PREVIEW_PLAY_ICON
                    tree.item(item_iid, values=tuple(current_values), tags=_tree_row_tags(item_iid, playing=False))
    except tkinter.TclError as e:
        print(f"[Preview] TclError updating icon: {e}")
    except Exception as e:
        print(f"[Preview] Error updating icon: {e}")

def on_tree_motion(event):
    """Handle mouse motion over treeview for preview column, cover column, and row hover effects."""
    global tree, _preview_hover_iid, search_results_data, _currently_playing_preview_iid, platform_var, COVER_SIZE, _cover_hover_iid, _row_hover_iid
    
    try:
        if 'tree' not in globals() or not tree or not tree.winfo_exists():
            return
        
        column = tree.identify_column(event.x)
        item_iid = tree.identify_row(event.y)
        region = tree.identify("region", event.x, event.y)
        
        # Heading hover: show hand cursor so user knows columns are clickable to sort
        try:
            tree.configure(cursor="hand2" if region == "heading" else "")
        except (tkinter.TclError, Exception):
            pass
        
        # Row hover: light up row with #272828 when mouse is over any part of it (skip if row is selected)
        if item_iid:
            if _row_hover_iid != item_iid:
                if _row_hover_iid and tree.exists(_row_hover_iid):
                    is_playing = _currently_playing_preview_iid == _row_hover_iid
                    tree.item(_row_hover_iid, tags=_tree_row_tags(_row_hover_iid, playing=is_playing))
                if item_iid not in tree.selection():
                    # Use only "hover" (+ "playing" if needed) to avoid oddrow/evenrow overriding background
                    playing = _currently_playing_preview_iid == item_iid
                    tags = ("hover", "playing") if playing else ("hover",)
                    tree.item(item_iid, tags=tags)
                _row_hover_iid = item_iid
        else:
            if _row_hover_iid and tree.exists(_row_hover_iid):
                is_playing = _currently_playing_preview_iid == _row_hover_iid
                tree.item(_row_hover_iid, tags=_tree_row_tags(_row_hover_iid, playing=is_playing))
            _row_hover_iid = None
        
        # If we were hovering over a different item, restore its icon first
        if _preview_hover_iid and _preview_hover_iid != item_iid:
            _restore_preview_icon(_preview_hover_iid)
            _preview_hover_iid = None
        
        # Cover vs Preview: use COVER_SIZE only so play column is never treated as cover
        is_over_cover_column = (event.x >= 0 and event.x <= COVER_SIZE)
        
        if is_over_cover_column and item_iid:
            # Accept any region type for tree column (tree, cell, etc.)
            item_data = next((item for item in search_results_data if str(item.get('tree_iid')) == str(item_iid)), None)
            if item_data and item_data.get('cover_url'):
                # Change cursor to hand for clickable covers (same as context menu on macOS)
                tree.configure(cursor=HAND_CURSOR)
                
                # Apply hover effect (darken cover)
                if _cover_hover_iid != item_iid:
                    # Restore previous hover if any
                    if _cover_hover_iid:
                        _restore_cover_hover(_cover_hover_iid)
                    
                    # Apply hover to current item
                    _cover_hover_iid = item_iid
                    _apply_cover_hover(item_iid)
                return
        
        # Preview column: only the ≡/▶ column (same bounds as click)
        is_over_preview_column = (PREVIEW_COLUMN_START < event.x <= PREVIEW_COLUMN_START + PREVIEW_COLUMN_WIDTH)
        if is_over_preview_column and item_iid:
            item_data = next((item for item in search_results_data if str(item.get('tree_iid')) == str(item_iid)), None)
            if item_data:
                has_preview = item_data.get('preview_url')
                row_type = (item_data.get('type') or '').lower()
                # Normalize platform (e.g. "Apple Music" -> "applemusic")
                current_platform = (item_data.get('platform') or '').lower().replace(' ', '')
                can_lazy_load = False
                is_youtube_track = False
                if not has_preview and row_type == 'track':
                    if current_platform in ('qobuz', 'soundcloud', 'spotify', 'tidal', 'deezer', 'applemusic'):
                        can_lazy_load = True
                    elif current_platform == 'youtube':
                        is_youtube_track = True
                is_album_playlist = item_data.get('is_album_playlist')
                is_artist = item_data.get('is_artist')
                if has_preview or can_lazy_load or is_youtube_track or is_album_playlist or is_artist:
                    tree.configure(cursor=HAND_CURSOR)
                    if (has_preview or can_lazy_load or is_youtube_track or is_album_playlist or is_artist) and _preview_hover_iid != item_iid:
                        _preview_hover_iid = item_iid
                        _enlarge_preview_icon(item_iid)
                    return
        
        # Reset cursor and restore icon if not over preview/cover column or no preview/cover available
        tree.configure(cursor="")
        
        # Restore cover hover if we were hovering over a cover
        if _cover_hover_iid:
            _restore_cover_hover(_cover_hover_iid)
            _cover_hover_iid = None
        
        if _preview_hover_iid:
            _restore_preview_icon(_preview_hover_iid)
            _preview_hover_iid = None
            
    except Exception as e:
        pass  # Silently ignore motion errors

def _enlarge_preview_icon(item_iid):
    """Enlarge the preview icon for hover effect."""
    global tree, _currently_playing_preview_iid, _loading_animation_iid
    try:
        # Don't enlarge icon if this item is currently showing loading animation
        if _loading_animation_iid == item_iid:
            return
        
        if 'tree' in globals() and tree and tree.winfo_exists():
            current_values = list(tree.item(item_iid, 'values'))
            if len(current_values) > 0:
                # Check if current value is a loading animation state
                current_icon = current_values[0] if current_values else ""
                # Check if current value is a loading animation state
                current_icon = current_values[0] if current_values else ""
                if current_icon in LOADING_ANIMATION_FRAMES or current_icon == PREVIEW_LOADING_ICON:
                    # Item is showing loading animation, don't overwrite it
                    return
                
                # Expand icon (≡ / ▲) hover: show [ ≡ ] / [ ▲ ]
                if current_icon.strip() == PREVIEW_EXPAND_COLLAPSED.strip():
                    current_values[0] = PREVIEW_EXPAND_COLLAPSED_HOVER
                    tree.item(item_iid, values=tuple(current_values), tags=_tree_row_tags(item_iid, playing=False))
                    return
                if current_icon.strip() == PREVIEW_EXPAND_EXPANDED.strip():
                    current_values[0] = PREVIEW_EXPAND_EXPANDED_HOVER
                    tree.item(item_iid, values=tuple(current_values), tags=_tree_row_tags(item_iid, playing=False))
                    return
                # Determine which hover icon to show based on play state
                # IMPORTANT: Don't show stop hover icon if we're still loading (even if _currently_playing_preview_iid is set)
                # The loading animation should continue until playback actually starts
                if _currently_playing_preview_iid == item_iid and _loading_animation_iid != item_iid:
                    # Only show stop hover icon if we're actually playing (not loading)
                    current_values[0] = PREVIEW_STOP_HOVER
                    tree.item(item_iid, values=tuple(current_values), tags=_tree_row_tags(item_iid, playing=True))
                else:
                    current_values[0] = PREVIEW_PLAY_HOVER
                    tree.item(item_iid, values=tuple(current_values), tags=_tree_row_tags(item_iid, playing=False))
    except:
        pass

def _apply_cover_hover(item_iid):
    """Apply hover effect (darkened) to cover image."""
    global tree, _cover_hover_cache
    try:
        if 'tree' in globals() and tree and tree.winfo_exists():
            if tree.exists(item_iid):
                hover_image = _cover_hover_cache.get(item_iid)
                if hover_image:
                    tree.item(item_iid, image=hover_image)
    except Exception as e:
        pass

def _restore_cover_hover(item_iid):
    """Restore cover image to normal (non-hover) state."""
    global tree, _cover_image_cache
    try:
        if 'tree' in globals() and tree and tree.winfo_exists():
            if tree.exists(item_iid):
                normal_image = _cover_image_cache.get(item_iid)
                if normal_image:
                    tree.item(item_iid, image=normal_image)
    except Exception as e:
        pass

def _restore_preview_icon(item_iid):
    """Restore the preview icon to normal size."""
    global tree, _currently_playing_preview_iid, search_results_data, platform_var, type_var, _loading_animation_iid
    try:
        # Don't restore icon if this item is currently showing loading animation
        if _loading_animation_iid == item_iid:
            return
        
        if 'tree' in globals() and tree and tree.winfo_exists():
            current_values = list(tree.item(item_iid, 'values'))
            if len(current_values) > 0:
                # Check if current value is a loading animation state
                current_icon = current_values[0] if current_values else ""
                # Check if current value is a loading animation state
                current_icon = current_values[0] if current_values else ""
                if current_icon in LOADING_ANIMATION_FRAMES or current_icon == PREVIEW_LOADING_ICON:
                    # Item is showing loading animation, don't overwrite it
                    return
                
                # Find if this item has a preview URL
                item_data = next((item for item in search_results_data if str(item.get('tree_iid')) == str(item_iid)), None)
                # Album/playlist/artist: restore to ≡ (expand icon)
                if item_data and (item_data.get('is_album_playlist') or item_data.get('is_artist')):
                    current_values[0] = PREVIEW_EXPAND_COLLAPSED
                    tree.item(item_iid, values=tuple(current_values), tags=_tree_row_tags(item_iid, playing=False))
                    return
                has_preview = item_data and item_data.get('preview_url')
                
                # Check if we can lazy-load preview for Qobuz/SoundCloud/Spotify/Tidal (tracks only)
                # YouTube: tracks show play icon (opens in browser)
                # Album tracklist rows: use row's platform and treat as track (ignore search type_var which may be "album")
                can_lazy_load = False
                is_youtube_track = False
                is_track_row = item_data and (
                    (isinstance(item_iid, str) and item_iid.startswith("album_track_")) or
                    (item_data.get('duration') is not None and not item_data.get('is_album_playlist'))
                )
                if not has_preview:
                    if is_track_row and item_data:
                        current_platform = (item_data.get('platform') or '').lower().replace(' ', '')
                        if current_platform in ('qobuz', 'soundcloud', 'spotify', 'tidal', 'deezer', 'applemusic'):
                            can_lazy_load = True
                        elif current_platform == 'youtube':
                            is_youtube_track = True
                    elif 'platform_var' in globals() and platform_var and 'type_var' in globals() and type_var:
                        current_platform = platform_var.get().lower()
                        current_type = type_var.get().lower()
                        # Use row type when available so preview works for track rows (e.g. expanded album/playlist) even when search type is album/playlist
                        row_is_track = (item_data and (item_data.get('type') or '').lower() == 'track') if item_data else (current_type == 'track')
                        if current_platform in ('qobuz', 'soundcloud', 'spotify', 'tidal') and row_is_track:
                            can_lazy_load = True
                        elif current_platform == 'youtube' and row_is_track:
                            is_youtube_track = True
                
                # Restore to normal icon
                # IMPORTANT: Don't show stop icon if we're still loading (even if _currently_playing_preview_iid is set)
                # The loading animation should continue until playback actually starts
                if not has_preview and not can_lazy_load and not is_youtube_track:
                    current_values[0] = PREVIEW_UNAVAILABLE
                    tree.item(item_iid, values=tuple(current_values), tags=_tree_row_tags(item_iid, playing=False))
                elif _currently_playing_preview_iid == item_iid and _loading_animation_iid != item_iid:
                    # Only show stop icon if we're actually playing (not loading)
                    current_values[0] = PREVIEW_STOP_ICON
                    tree.item(item_iid, values=tuple(current_values), tags=_tree_row_tags(item_iid, playing=True))
                else:
                    current_values[0] = PREVIEW_PLAY_ICON
                    tree.item(item_iid, values=tuple(current_values), tags=_tree_row_tags(item_iid, playing=False))
    except:
        pass

def on_tree_leave(event):
    """Handle mouse leaving the treeview."""
    global tree, _preview_hover_iid, _row_hover_iid, _currently_playing_preview_iid
    
    try:
        if 'tree' in globals() and tree and tree.winfo_exists():
            tree.configure(cursor="")
        # Restore the icon of the previously hovered item
        if _preview_hover_iid:
            _restore_preview_icon(_preview_hover_iid)
            _preview_hover_iid = None
        # Clear row hover highlight
        if _row_hover_iid and tree.exists(_row_hover_iid):
            is_playing = _currently_playing_preview_iid == _row_hover_iid
            tree.item(_row_hover_iid, tags=_tree_row_tags(_row_hover_iid, playing=is_playing))
        _row_hover_iid = None
    except:
        pass

def _get_fullsize_cover_url(thumbnail_url, platform_name, raw_result=None):
    """Convert thumbnail cover URL to full-size URL based on platform."""
    if not thumbnail_url:
        return None
    
    platform_lower = platform_name.lower() if platform_name else ""
    
    try:
        # Beatport/Beatsource: URLs use {w}x{h} format, replace with larger size
        if platform_lower in ('beatport', 'beatsource'):
            # Try to get original image_uri from raw_result first (most reliable)
            if raw_result:
                try:
                    if isinstance(raw_result, dict):
                        image_uri = None
                        # Try multiple paths to find image_uri
                        # For releases/albums
                        if 'release' in raw_result:
                            release_data = raw_result.get('release', {})
                            if isinstance(release_data, dict):
                                image_data = release_data.get('image', {})
                                if isinstance(image_data, dict):
                                    image_uri = image_data.get('uri') or image_data.get('dynamic_uri')
                        # For tracks
                        if not image_uri and 'image' in raw_result:
                            image_data = raw_result.get('image', {})
                            if isinstance(image_data, dict):
                                image_uri = image_data.get('uri') or image_data.get('dynamic_uri')
                        # Direct image_uri field
                        if not image_uri:
                            image_uri = raw_result.get('image_uri') or raw_result.get('cover_uri')
                        
                        if image_uri:
                            # Import the method from the appropriate module
                            try:
                                if platform_lower == 'beatport':
                                    from modules.beatport.interface import ModuleInterface
                                else:  # beatsource
                                    from modules.beatsource.interface import ModuleInterface
                                return ModuleInterface._generate_artwork_url(image_uri, 1400)
                            except Exception as e:
                                print(f"Error generating {platform_lower} artwork URL: {e}")
                except Exception as e:
                    print(f"Error processing {platform_lower} raw_result: {e}")
            
            # Fallback: try to modify the existing URL
            import re
            # Beatport URLs are like: https://geo-media.beatport.com/image_size/56x56/{image_id}.jpg
            # We need to replace the size part (can be 1-4 digits x 1-4 digits)
            # More flexible pattern to match any size like 56x56, 500x500, 1400x1400, etc.
            res_pattern = re.compile(r'/\d{1,4}x\d{1,4}/')
            match = re.search(res_pattern, thumbnail_url)
            if match:
                # Replace with larger size (1400x1400)
                return re.sub(res_pattern, '/1400x1400/', thumbnail_url)
            # Also check for pattern without leading slash (in case URL format differs)
            res_pattern2 = re.compile(r'\d{1,4}x\d{1,4}')
            match2 = re.search(res_pattern2, thumbnail_url)
            if match2:
                # Replace with larger size (1400x1400)
                return re.sub(res_pattern2, '1400x1400', thumbnail_url)
            # If it has {w}x{h} format, replace with 1400
            if "{w}" in thumbnail_url and "{h}" in thumbnail_url:
                return thumbnail_url.format(w=1400, h=1400)
        
        # SoundCloud: Replace thumbnail suffix with -original
        elif platform_lower == 'soundcloud':
            if '-t200x200' in thumbnail_url:
                return thumbnail_url.replace('-t200x200', '-original')
            elif '-large' in thumbnail_url:
                return thumbnail_url.replace('-large', '-original')
            # If it's already original or doesn't have size suffix, return as-is
        
        # Apple Music: Replace size placeholders with larger size
        elif platform_lower in ('applemusic', 'apple music'):
            # Apple Music uses {w}x{h}bb.jpg format, replace with 1400x1400bb.jpg
            if '{w}x{h}bb.jpg' in thumbnail_url:
                return thumbnail_url.replace('{w}x{h}bb.jpg', '1400x1400bb.jpg')
            # If it has hardcoded size like 56x56bb.jpg, replace with 1400x1400bb.jpg
            import re
            size_pattern = re.compile(r'\d+x\d+bb\.jpg')
            if re.search(size_pattern, thumbnail_url):
                return re.sub(size_pattern, '1400x1400bb.jpg', thumbnail_url)
            # Fallback: try to replace any size pattern
            size_pattern2 = re.compile(r'(\d+)x(\d+)')
            if re.search(size_pattern2, thumbnail_url):
                return re.sub(size_pattern2, '1400x1400', thumbnail_url)
        
        # Tidal: URLs use size parameter, try to get original from raw_result
        elif platform_lower == 'tidal':
            if raw_result:
                try:
                    from modules.tidal.interface import ModuleInterface
                    # Try to extract cover ID from raw_result
                    cover_id = None
                    if isinstance(raw_result, dict):
                        # For tracks: check album cover
                        if 'album' in raw_result and 'cover' in raw_result['album']:
                            cover_id = raw_result['album']['cover']
                        # For albums: check cover field
                        elif 'cover' in raw_result:
                            cover_id = raw_result['cover']
                        # For playlists: check squareImage and other possible fields
                        elif 'squareImage' in raw_result:
                            cover_id = raw_result['squareImage']
                        # For artists: check multiple possible field names
                        elif 'picture' in raw_result:
                            cover_id = raw_result['picture']
                        elif 'image' in raw_result:
                            cover_id = raw_result['image']
                        elif 'cover' in raw_result:
                            cover_id = raw_result['cover']
                        # Check nested images structure
                        elif 'images' in raw_result and isinstance(raw_result['images'], dict):
                            cover_id = (
                                raw_result['images'].get('picture') or
                                raw_result['images'].get('cover') or
                                raw_result['images'].get('squareImage')
                            )
                        # Check if this is an artist (no 'title' field suggests artist)
                        is_artist = 'title' not in raw_result and 'name' in raw_result
                        
                        # Fallback: if we have an artist ID but no image, try fetching artist details
                        # This is slower but ensures we get the image if it exists
                        if not cover_id and 'id' in raw_result:
                            try:
                                if is_artist:
                                    artist_id = raw_result.get('id')
                                    if artist_id:
                                        # Fetch full artist details to get image
                                        # We need access to the module instance, but we can't easily get it here
                                        # So we'll just try to use the thumbnail URL if available
                                        pass
                            except:
                                pass
                    if cover_id:
                        # For artists, use 750x750.jpg as it's more reliably available
                        if is_artist:
                            return f'https://resources.tidal.com/images/{cover_id.replace("-", "/")}/750x750.jpg'
                        else:
                            # Use 750x750.jpg as it's more reliably available
                            return f'https://resources.tidal.com/images/{cover_id.replace("-", "/")}/750x750.jpg'
                except:
                    pass
            # Fallback: try to replace size in URL if present
            import re
            size_pattern = re.compile(r'/\d+x\d+')
            match = re.search(size_pattern, thumbnail_url)
            if match:
                # Check if this is an artist by examining the URL or raw_result
                is_artist = False
                if raw_result and isinstance(raw_result, dict):
                    is_artist = 'title' not in raw_result and 'name' in raw_result
                
                # Use 750x750.jpg as it's more reliably available for all Tidal content
                return re.sub(size_pattern, '/750x750', thumbnail_url)
        
        # Qobuz: URLs often have size parameters, use _org.jpg for full-size
        elif platform_lower == 'qobuz':
            import re
            # Qobuz URLs have size like _230.jpg or _300.jpg, replace with _org.jpg for full-size
            # Pattern: anything ending with _number.jpg or _number.png
            size_pattern = re.compile(r'_(\d+)\.(jpg|png)$')
            if re.search(size_pattern, thumbnail_url):
                # Replace size suffix with _org.jpg for full-size
                return re.sub(r'_(\d+)\.(jpg|png)$', r'_org.jpg', thumbnail_url)
            # If no size pattern found, try appending _org.jpg (remove extension first)
            if '.' in thumbnail_url:
                base_url = thumbnail_url.rsplit('.', 1)[0]
                return base_url + '_org.jpg'
        
        # Deezer: URLs have size parameters
        elif platform_lower == 'deezer':
            import re
            # Deezer URLs like .../cover/56x56-000000-80-0-0.jpg
            size_pattern = re.compile(r'/\d+x\d+-')
            match = re.search(size_pattern, thumbnail_url)
            if match:
                # Replace with larger size (1000x1000)
                return re.sub(size_pattern, '/1000x1000-', thumbnail_url)
        
        # Spotify: URLs have size parameters
        elif platform_lower == 'spotify':
            import re
            # Spotify URLs like .../image/ab67616d0000b273...?size=64
            if '?size=' in thumbnail_url:
                return thumbnail_url.split('?size=')[0] + '?size=640'
            # Or .../640x640 format
            size_pattern = re.compile(r'/\d+x\d+')
            match = re.search(size_pattern, thumbnail_url)
            if match:
                return re.sub(size_pattern, '/640x640', thumbnail_url)
        
        # YouTube: URLs use quality suffixes, upgrade to maxresdefault.jpg for best quality
        elif platform_lower == 'youtube':
            import re
            # YouTube thumbnail URLs: https://i.ytimg.com/vi/VIDEO_ID/quality.jpg
            # Quality options: default.jpg, mqdefault.jpg, hqdefault.jpg, maxresdefault.jpg
            # Try to upgrade to maxresdefault.jpg (highest quality)
            yt_pattern = re.compile(r'(https?://i\.ytimg\.com/vi/[^/]+/)(?:default|mqdefault|hqdefault|sddefault)\.jpg')
            match = re.search(yt_pattern, thumbnail_url)
            if match:
                return match.group(1) + 'maxresdefault.jpg'
            # If pattern doesn't match but it's a YouTube thumbnail URL, try to replace anyway
            if 'i.ytimg.com/vi/' in thumbnail_url and '/default.jpg' in thumbnail_url:
                return thumbnail_url.replace('/default.jpg', '/maxresdefault.jpg')
            elif 'i.ytimg.com/vi/' in thumbnail_url and '/mqdefault.jpg' in thumbnail_url:
                return thumbnail_url.replace('/mqdefault.jpg', '/maxresdefault.jpg')
            elif 'i.ytimg.com/vi/' in thumbnail_url and '/hqdefault.jpg' in thumbnail_url:
                return thumbnail_url.replace('/hqdefault.jpg', '/maxresdefault.jpg')
        
        # Default: return original URL (might already be full-size or we can't determine)
        return thumbnail_url
        
    except Exception as e:
        print(f"Error converting cover URL to full-size: {e}")
        # Fallback to original URL
        return thumbnail_url

def show_cover_popup(cover_url, title="", artist="", platform_name="", raw_result=None, fallback_cover_url=None):
    """Show a pop-up window with the full-size album cover image. If full-size fails, fallback_cover_url (e.g. small thumbnail) is used."""
    global app, orpheus_instance
    
    # For Tidal artists, if we don't have a cover URL, try to fetch it lazily
    if not cover_url and platform_name and platform_name.lower() == 'tidal' and raw_result:
        if isinstance(raw_result, dict) and 'id' in raw_result and 'name' in raw_result:
            # This looks like an artist - try to fetch the artist image
            try:
                if 'orpheus_instance' in globals() and orpheus_instance:
                    artist_id = raw_result.get('id')
                    if artist_id:
                        # Fetch artist details to get the image
                        module_instance = orpheus_instance.load_module('tidal')
                        if hasattr(module_instance, 'session') and hasattr(module_instance.session, 'get_artist'):
                            artist_data = module_instance.session.get_artist(artist_id)
                            
                            # Check for image fields in the artist data - check multiple possible locations
                            # Default fallback image UUID (same as python-tidal library uses)
                            DEFAULT_ARTIST_IMG = "1e01cdb6-f15d-4d8b-8440-a047976c1cac"
                            artist_image_id = None
                            if isinstance(artist_data, dict):
                                # Check top-level fields first
                                artist_image_id = (
                                    artist_data.get('picture') or
                                    artist_data.get('image') or
                                    artist_data.get('squareImage') or
                                    artist_data.get('cover') or
                                    artist_data.get('pictureId') or
                                    artist_data.get('imageId')
                                )
                                
                                # Check nested structures if not found at top level
                                if not artist_image_id:
                                    # Check if there's an 'images' object
                                    images_obj = artist_data.get('images')
                                    if isinstance(images_obj, dict):
                                        artist_image_id = (
                                            images_obj.get('picture') or
                                            images_obj.get('cover') or
                                            images_obj.get('squareImage')
                                        )
                                    # Check if there's a 'media' object
                                    if not artist_image_id:
                                        media_obj = artist_data.get('media')
                                        if isinstance(media_obj, dict):
                                            artist_image_id = media_obj.get('picture') or media_obj.get('cover')
                            
                            # Fallback to default image if still not found
                            if not artist_image_id:
                                artist_image_id = DEFAULT_ARTIST_IMG
                            
                            if artist_image_id:
                                from modules.tidal.interface import ModuleInterface
                                cover_url = ModuleInterface._generate_artwork_url(artist_image_id, size=56)
                                # Update the raw_result with the image for future use
                                raw_result['picture'] = artist_image_id
            except Exception as e:
                # Silently fail - if we can't fetch it, just show without image
                pass
    
    if not cover_url:
        return
    
    # Convert thumbnail URL to full-size URL
    fullsize_url = _get_fullsize_cover_url(cover_url, platform_name, raw_result)
    # Fallback to original URL if conversion failed
    if not fullsize_url:
        fullsize_url = cover_url
    
    try:
        # Create pop-up window
        popup = customtkinter.CTkToplevel(app)
        popup.title(f"Artwork - {title}" if title else "Artwork")
        popup.attributes("-topmost", True)
        popup.transient(app)
        popup.resizable(True, True)
        
        # Set initial size; center after UI is built and laid out
        initial_width = 500
        initial_height = 500
        popup.geometry(f"{initial_width}x{initial_height}")
        
        # Create a frame to hold the image
        image_frame = customtkinter.CTkFrame(popup, fg_color="#1D1E1E")
        image_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create a label to show loading message
        loading_label = customtkinter.CTkLabel(
            image_frame,
            text="Loading cover...",
            font=("Segoe UI", 12)
        )
        loading_label.pack(expand=True)
        
        # Create info label at bottom
        info_text = f"{title}" if title else ""
        if artist:
            info_text += f" - {artist}" if info_text else artist
        info_label = customtkinter.CTkLabel(
            popup,
            text=info_text,
            font=("Segoe UI", 11),
            text_color="#AAAAAA"
        )
        info_label.pack(pady=(0, 10))
        
        # Center on screen (same logic as main window for scaled Windows / DPI)
        popup.update()
        scaling = popup._get_window_scaling()
        screen_width = popup.winfo_screenwidth()
        screen_height = popup.winfo_screenheight()
        actual_width = popup.winfo_width()
        actual_height = popup.winfo_height()
        x_phys = (screen_width - actual_width) // 2
        y_phys = (screen_height - actual_height) // 2
        if platform.system() == "Windows":
            popup.geometry(f"+{x_phys}+{y_phys}")
        else:
            x_logical = int(x_phys / scaling)
            y_logical = int(y_phys / scaling)
            popup.geometry(f"+{x_logical}+{y_logical}")
        
        # Defer popup close on WM_DELETE_WINDOW to avoid macOS Tk crash (EXC_BAD_ACCESS in TkMacOSXGetHostToplevel)
        def _on_popup_close():
            def _do_close():
                try:
                    if context_menu_ref['menu']:
                        cm = context_menu_ref['menu']
                        context_menu_ref['menu'] = None
                        try:
                            if cm.winfo_exists():
                                cm.destroy()
                        except Exception:
                            pass
                    if popup.winfo_exists():
                        popup.destroy()
                except Exception:
                    pass
            popup.after_idle(_do_close)
        popup.protocol("WM_DELETE_WINDOW", _on_popup_close)
        
        # Store PIL Image for copy/save operations
        pil_image_ref = {'image': None, 'original_image': None}
        # Store context menu reference for closing
        context_menu_ref = {'menu': None}

        def _deferred_destroy_menu(menu):
            """Defer menu destruction to avoid Tk/Cocoa crash on macOS (EXC_BAD_ACCESS in TkMacOSXGetHostToplevel)."""
            if not menu:
                return
            try:
                m = menu
                context_menu_ref['menu'] = None
                def _destroy_later():
                    try:
                        if m.winfo_exists():
                            m.destroy()
                    except Exception:
                        pass
                if popup.winfo_exists():
                    popup.after_idle(_destroy_later)
            except Exception:
                pass
        
        # Copy image to clipboard function
        def _copy_image_to_clipboard(menu=None):
            try:
                if menu:
                    _deferred_destroy_menu(menu)
                
                if not pil_image_ref['image']:
                    return
                
                # Copy to clipboard (Windows-specific method)
                if platform.system() == "Windows":
                    try:
                        import win32clipboard
                        from io import BytesIO
                        
                        output = BytesIO()
                        pil_image_ref['image'].save(output, 'BMP')
                        data = output.getvalue()[14:]  # Remove BMP header
                        output.close()
                        
                        win32clipboard.OpenClipboard()
                        win32clipboard.EmptyClipboard()
                        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                        win32clipboard.CloseClipboard()
                        
                        print("Image copied to clipboard.")
                    except ImportError:
                        # Fallback: save to temp file and inform user
                        import tempfile
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                        pil_image_ref['image'].save(temp_file.name, 'PNG')
                        temp_file.close()
                        print(f"Image saved to temporary file: {temp_file.name}")
                        print("Note: Install pywin32 for direct clipboard copy on Windows.")
                else:
                    # macOS/Linux: use different method
                    print("Image copy to clipboard not fully supported on this platform.")
                    
            except Exception as e:
                print(f"Error copying image to clipboard: {e}")
        
        # Save image to file function
        def _save_image_to_file(menu=None):
            try:
                if menu:
                    _deferred_destroy_menu(menu)
                
                if not pil_image_ref['original_image']:
                    return
                
                # Generate filename from artist and title
                filename = "artwork.jpg"
                if artist and title:
                    # Sanitize filename (remove invalid characters)
                    safe_artist = re.sub(r'[<>:"/\\|?*]', '_', artist)
                    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                    filename = f"{safe_artist} - {safe_title} - artwork.jpg"
                elif title:
                    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                    filename = f"{safe_title} - artwork.jpg"
                elif artist:
                    safe_artist = re.sub(r'[<>:"/\\|?*]', '_', artist)
                    filename = f"{safe_artist} - artwork.jpg"
                
                # Open file dialog
                file_path = tkinter.filedialog.asksaveasfilename(
                    parent=popup,
                    title="Save Artwork As...",
                    defaultextension=".jpg",
                    filetypes=[
                        ("JPEG files", "*.jpg *.jpeg"),
                        ("PNG files", "*.png"),
                        ("All files", "*.*")
                    ],
                    initialfile=filename
                )
                
                if file_path:
                    # Determine format from extension
                    ext = os.path.splitext(file_path)[1].lower()
                    format_map = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG'}
                    save_format = format_map.get(ext, 'JPEG')
                    
                    # Save the original (full-size) image
                    pil_image_ref['original_image'].save(file_path, save_format, quality=95)
                    print(f"Artwork saved to: {file_path}")
                    
            except Exception as e:
                print(f"Error saving image: {e}")
                tkinter.messagebox.showerror("Error", f"Failed to save image: {e}", parent=popup)
        
        # Load image asynchronously (use fallback_cover_url or original cover_url when fullsize fails)
        original_cover_url = fallback_cover_url if fallback_cover_url else cover_url

        def _load_fullsize_image():
            nonlocal fullsize_url  # Allow modification of outer scope variable
            try:
                from PIL import Image
                import io
                
                # Debug output
                global current_settings
                debug_mode = current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False) if 'current_settings' in globals() else False
                
                # Use full-size URL instead of thumbnail
                # Add headers to avoid 403 errors from Tidal and other services
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://tidal.com/',
                    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Sec-Fetch-Dest': 'image',
                    'Sec-Fetch-Mode': 'no-cors',
                    'Sec-Fetch-Site': 'cross-site',
                }
                
                # Get platform name for logging (capitalize for display)
                platform_display = platform_name.capitalize() if platform_name else "Unknown"
                
                if debug_mode:
                    print(f"[{platform_display} Cover Popup] Loading: {fullsize_url}")
                
                response = requests.get(fullsize_url, timeout=10, headers=headers)
                
                if debug_mode:
                    print(f"[{platform_display} Cover Popup] Response: HTTP {response.status_code}")
                
                # If fullsize failed and we have a different original (thumbnail) URL, retry with that
                # (Apple Music, Qobuz, etc. may allow thumbnails but block or 403 on large sizes)
                if response.status_code != 200 and original_cover_url and original_cover_url != fullsize_url:
                    try:
                        fallback_response = requests.get(original_cover_url, timeout=10, headers=headers)
                        if debug_mode:
                            print(f"[{platform_display} Cover Popup] Fallback (thumbnail) response: HTTP {fallback_response.status_code}")
                        if fallback_response.status_code == 200:
                            fullsize_url = original_cover_url
                            response = fallback_response
                    except Exception as e:
                        if debug_mode:
                            print(f"[{platform_display} Cover Popup] Fallback request failed: {e}")
                
                # YouTube: if maxresdefault returned 404, try hqdefault/mqdefault/default (many videos don't have maxres)
                yt_platform = (platform_name or '').lower() == 'youtube'
                if response.status_code != 200 and yt_platform and fullsize_url and 'maxresdefault.jpg' in fullsize_url and 'i.ytimg.com/vi/' in fullsize_url:
                    for yt_quality in ('hqdefault.jpg', 'mqdefault.jpg', 'default.jpg'):
                        yt_fallback = fullsize_url.replace('maxresdefault.jpg', yt_quality)
                        if yt_fallback == fullsize_url:
                            continue
                        try:
                            yt_resp = requests.get(yt_fallback, timeout=10, headers=headers)
                            if debug_mode:
                                print(f"[{platform_display} Cover Popup] YouTube fallback ({yt_quality}) response: HTTP {yt_resp.status_code}")
                            if yt_resp.status_code == 200:
                                fullsize_url = yt_fallback
                                response = yt_resp
                                break
                        except Exception as e:
                            if debug_mode:
                                print(f"[{platform_display} Cover Popup] YouTube fallback ({yt_quality}) failed: {e}")
                            continue
                
                # Apple Music: 1400x1400 may 403 in some contexts (e.g. playlist tracklist); try smaller size
                am_platform = (platform_name or '').lower().replace(' ', '')
                if response.status_code != 200 and am_platform in ('applemusic', 'applemusic') and 'bb.jpg' in fullsize_url:
                    am_fallback = re.sub(r'\d+x\d+bb\.jpg', '500x500bb.jpg', fullsize_url)
                    if am_fallback != fullsize_url:
                        try:
                            am_response = requests.get(am_fallback, timeout=10, headers=headers)
                            if debug_mode:
                                print(f"[{platform_display} Cover Popup] Apple Music fallback (500x500): HTTP {am_response.status_code}")
                            if am_response.status_code == 200:
                                fullsize_url = am_fallback
                                response = am_response
                        except Exception as e:
                            if debug_mode:
                                print(f"[{platform_display} Cover Popup] Apple Music fallback failed: {e}")

                # If non-200 status and Tidal URL, try retrying with 750x750.jpg as fallback
                # (smaller sizes like 80x80 or larger like 1280x1280 may not be available)
                if response.status_code != 200 and 'resources.tidal.com/images' in fullsize_url:
                    # Check if URL already uses 750x750.jpg
                    size_pattern = r'/(\d+x\d+)\.jpg'
                    match = re.search(size_pattern, fullsize_url)
                    
                    if match and match.group(1) != '750x750':
                        # Retry with 750x750.jpg
                        fallback_url = re.sub(size_pattern, '/750x750.jpg', fullsize_url)
                        if debug_mode:
                            print(f"[{platform_display} Cover Popup] {response.status_code} for {fullsize_url}, retrying with {fallback_url}")
                        try:
                            fallback_response = requests.get(fallback_url, timeout=10, headers=headers)
                            if debug_mode:
                                print(f"[{platform_display} Cover Popup] Fallback response: HTTP {fallback_response.status_code}")
                            if fallback_response.status_code == 200:
                                # Use the fallback URL
                                fullsize_url = fallback_url
                                response = fallback_response
                        except Exception as e:
                            if debug_mode:
                                print(f"[{platform_display} Cover Popup] Fallback request failed: {e}")
                            pass  # Continue with original response if fallback fails
                
                if response.status_code == 200:
                    img_data = io.BytesIO(response.content)
                    original_img = Image.open(img_data)
                    pil_image_ref['original_image'] = original_img.copy()  # Store original for saving
                    
                    # Get original dimensions
                    orig_width, orig_height = original_img.size
                    
                    # Limit maximum size to fit screen (max 800px on longest side)
                    max_size = 800
                    if orig_width > max_size or orig_height > max_size:
                        if orig_width > orig_height:
                            new_width = max_size
                            new_height = int(orig_height * (max_size / orig_width))
                        else:
                            new_height = max_size
                            new_width = int(orig_width * (max_size / orig_height))
                        img = original_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    else:
                        img = original_img
                    
                    pil_image_ref['image'] = img  # Store display image for copying
                    
                    # Update UI on main thread (CTkImage must be created on main thread)
                    def _update_ui():
                        try:
                            if popup.winfo_exists():
                                loading_label.destroy()
                                
                                disp = pil_image_ref.get('image')
                                if not disp:
                                    return
                                # CTkImage requires PIL Image objects (not path); created on main thread for HighDPI
                                ctk_img = customtkinter.CTkImage(
                                    light_image=disp,
                                    dark_image=disp,
                                    size=(disp.width, disp.height)
                                )
                                img_label = customtkinter.CTkLabel(
                                    image_frame,
                                    image=ctk_img,
                                    text=""
                                )
                                img_label.image = ctk_img  # Keep reference
                                img_label.pack(expand=True)
                                
                                # Add right-click context menu to image label
                                def _show_image_context_menu(event):
                                    if not pil_image_ref['image']:
                                        return
                                    
                                    # Close existing menu if open (deferred to avoid macOS Tk crash)
                                    if context_menu_ref['menu']:
                                        _deferred_destroy_menu(context_menu_ref['menu'])
                                    
                                    # Create context menu
                                    context_menu = customtkinter.CTkToplevel(popup)
                                    context_menu.overrideredirect(True)
                                    context_menu.attributes("-topmost", True)
                                    context_menu_ref['menu'] = context_menu
                                    
                                    # Position menu near cursor
                                    x = event.x_root
                                    y = event.y_root
                                    context_menu.geometry(f"+{x}+{y}")
                                    
                                    # Match tooltip background and fixed width; border matches separator color (#2B2B2B)
                                    menu_frame = customtkinter.CTkFrame(context_menu, border_width=1, border_color="#565B5E", fg_color=TOOLTIP_MENU_BG, width=CONTEXT_MENU_WIDTH)
                                    menu_frame.pack(fill="both", expand=True, padx=1, pady=1)
                                    button_color = TOOLTIP_MENU_BG
                                    hover_color_artwork = "#1F6AA5"
                                    
                                    # macOS: plain tk rows + motion-based hover (Enter/Leave often don't fire in overrideredirect on macOS)
                                    if platform.system() == "Darwin":
                                        from PIL import Image, ImageDraw, ImageTk
                                        text_fg = CONTEXT_MENU_TEXT_COLOR
                                        # Icons as PhotoImage for tk.Label (keep refs so they aren't GC'd)
                                        def _artwork_copy_pil():
                                            img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
                                            d = ImageDraw.Draw(img)
                                            bx1, by1, bx2, by2 = 2, 2, 10, 10
                                            fx1, fy1, fx2, fy2 = 5, 5, 13, 13
                                            d.line([(bx1, by1), (bx2, by1)], fill=text_fg, width=1)
                                            d.line([(bx1, by1), (bx1, by2)], fill=text_fg, width=1)
                                            d.line([(bx2, by1), (bx2, fy1)], fill=text_fg, width=1)
                                            d.line([(bx1, by2), (fx1, by2)], fill=text_fg, width=1)
                                            d.rectangle([fx1, fy1, fx2, fy2], outline=text_fg, width=1)
                                            return img
                                        def _artwork_download_pil():
                                            img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
                                            d = ImageDraw.Draw(img)
                                            cx = 8
                                            d.line([(3, 13), (13, 13)], fill=text_fg, width=1)
                                            d.line([(cx, 2), (cx, 10)], fill=text_fg, width=1)
                                            d.line([(cx - 3, 7), (cx, 10), (cx + 3, 7)], fill=text_fg, width=1)
                                            return img
                                        _artwork_copy_photo = ImageTk.PhotoImage(_artwork_copy_pil())
                                        _artwork_save_photo = ImageTk.PhotoImage(_artwork_download_pil())
                                        
                                        copy_row_tk = tkinter.Frame(menu_frame, bg=button_color, height=24, width=CONTEXT_MENU_WIDTH, cursor="", highlightthickness=0)
                                        copy_row_tk.pack(pady=(2, 1), padx=2)
                                        copy_row_tk.pack_propagate(False)
                                        copy_lbl_tk = tkinter.Label(copy_row_tk, text=" Copy Image", image=_artwork_copy_photo, compound="left", bg=button_color, fg=text_fg, font=("Segoe UI", 11), anchor="w", cursor="", highlightthickness=0)
                                        copy_lbl_tk.pack(fill="both", expand=True, padx=4, pady=1)
                                        copy_lbl_tk.image = _artwork_copy_photo
                                        
                                        sep_tk = tkinter.Frame(menu_frame, bg="#2B2B2B", height=2, highlightthickness=0)
                                        sep_tk.pack(fill="x", padx=2, pady=2)
                                        sep_tk.pack_propagate(False)
                                        
                                        save_row_tk = tkinter.Frame(menu_frame, bg=button_color, height=24, width=CONTEXT_MENU_WIDTH, cursor="", highlightthickness=0)
                                        save_row_tk.pack(pady=(1, 2), padx=2)
                                        save_row_tk.pack_propagate(False)
                                        save_lbl_tk = tkinter.Label(save_row_tk, text=" Save as...", image=_artwork_save_photo, compound="left", bg=button_color, fg=text_fg, font=("Segoe UI", 11), anchor="w", cursor="", highlightthickness=0)
                                        save_lbl_tk.pack(fill="both", expand=True, padx=4, pady=1)
                                        save_lbl_tk.image = _artwork_save_photo
                                        
                                        # Motion-based hover + polling fallback (Enter/Leave and sometimes Motion don't fire in overrideredirect on macOS)
                                        def _artwork_update_hover(x_root, y_root):
                                            try:
                                                r1x, r1y = copy_row_tk.winfo_rootx(), copy_row_tk.winfo_rooty()
                                                r1w, r1h = copy_row_tk.winfo_width(), copy_row_tk.winfo_height()
                                                r2x, r2y = save_row_tk.winfo_rootx(), save_row_tk.winfo_rooty()
                                                r2w, r2h = save_row_tk.winfo_width(), save_row_tk.winfo_height()
                                            except tkinter.TclError:
                                                return
                                            in_copy = r1x <= x_root < r1x + r1w and r1y <= y_root < r1y + r1h
                                            in_save = r2x <= x_root < r2x + r2w and r2y <= y_root < r2y + r2h
                                            hover = hover_color_artwork
                                            if in_copy:
                                                copy_row_tk.config(bg=hover, cursor=HAND_CURSOR)
                                                copy_lbl_tk.config(bg=hover, cursor=HAND_CURSOR)
                                                save_row_tk.config(bg=button_color, cursor="")
                                                save_lbl_tk.config(bg=button_color, cursor="")
                                                context_menu.configure(cursor=HAND_CURSOR)
                                            elif in_save:
                                                save_row_tk.config(bg=hover, cursor=HAND_CURSOR)
                                                save_lbl_tk.config(bg=hover, cursor=HAND_CURSOR)
                                                copy_row_tk.config(bg=button_color, cursor="")
                                                copy_lbl_tk.config(bg=button_color, cursor="")
                                                context_menu.configure(cursor=HAND_CURSOR)
                                            else:
                                                copy_row_tk.config(bg=button_color, cursor="")
                                                copy_lbl_tk.config(bg=button_color, cursor="")
                                                save_row_tk.config(bg=button_color, cursor="")
                                                save_lbl_tk.config(bg=button_color, cursor="")
                                                context_menu.configure(cursor="")
                                        
                                        def _artwork_motion(e):
                                            _artwork_update_hover(e.x_root, e.y_root)
                                        
                                        def _artwork_poll():
                                            try:
                                                if not context_menu.winfo_exists():
                                                    return
                                                x = context_menu.winfo_pointerx()
                                                y = context_menu.winfo_pointery()
                                                _artwork_update_hover(x, y)
                                                context_menu.after(50, _artwork_poll)
                                            except tkinter.TclError:
                                                pass
                                        
                                        context_menu.bind("<Motion>", _artwork_motion)
                                        menu_frame.bind("<Motion>", _artwork_motion)
                                        for _w in (copy_row_tk, copy_lbl_tk, save_row_tk, save_lbl_tk):
                                            _w.bind("<Motion>", _artwork_motion)
                                        context_menu.after(50, _artwork_poll)  # fallback when Motion doesn't fire on macOS overrideredirect
                                        copy_row_tk.bind("<Button-1>", lambda e: (_copy_image_to_clipboard(context_menu), _deferred_destroy_menu(context_menu)))
                                        copy_lbl_tk.bind("<Button-1>", lambda e: (_copy_image_to_clipboard(context_menu), _deferred_destroy_menu(context_menu)))
                                        save_row_tk.bind("<Button-1>", lambda e: (_save_image_to_file(context_menu), _deferred_destroy_menu(context_menu)))
                                        save_lbl_tk.bind("<Button-1>", lambda e: (_save_image_to_file(context_menu), _deferred_destroy_menu(context_menu)))
                                    else:
                                        menu_frame.configure(cursor=HAND_CURSOR)
                                        copy_icon = _create_copy_icon(color=CONTEXT_MENU_TEXT_COLOR)
                                        copy_btn = customtkinter.CTkButton(
                                            menu_frame,
                                            text="Copy Image",
                                            image=copy_icon,
                                            compound="left",
                                            anchor="w",
                                            width=100,
                                            height=24,
                                            font=("Segoe UI", 11),
                                            fg_color=button_color,
                                            hover_color=hover_color_artwork,
                                            text_color=CONTEXT_MENU_TEXT_COLOR,
                                            text_color_disabled=CONTEXT_MENU_TEXT_DISABLED,
                                            border_width=0,
                                            command=lambda: _copy_image_to_clipboard(context_menu)
                                        )
                                        copy_btn.image = copy_icon
                                        copy_btn.pack(pady=(2, 1), padx=2, fill="x")
                                        
                                        sep_frame = customtkinter.CTkFrame(menu_frame, width=50, height=2, fg_color="#2B2B2B")
                                        sep_frame.pack(fill="x", padx=2, pady=2)
                                        
                                        save_icon = _create_download_icon(color=CONTEXT_MENU_TEXT_COLOR)
                                        save_btn = customtkinter.CTkButton(
                                            menu_frame,
                                            text="Save as...",
                                            image=save_icon,
                                            compound="left",
                                            anchor="w",
                                            width=100,
                                            height=24,
                                            font=("Segoe UI", 11),
                                            fg_color=button_color,
                                            hover_color=hover_color_artwork,
                                            text_color=CONTEXT_MENU_TEXT_COLOR,
                                            text_color_disabled=CONTEXT_MENU_TEXT_DISABLED,
                                            border_width=0,
                                            command=lambda: _save_image_to_file(context_menu)
                                        )
                                        save_btn.image = save_icon
                                        save_btn.pack(pady=(1, 2), padx=2, fill="x")
                                    
                                    # Close menu when clicking outside (deferred to avoid macOS Tk crash)
                                    def _close_menu(event=None):
                                        if context_menu_ref['menu']:
                                            _deferred_destroy_menu(context_menu_ref['menu'])
                                    
                                    # Bind close events
                                    context_menu.bind("<FocusOut>", lambda e: _close_menu())
                                    popup.bind("<Button-1>", lambda e: _close_menu(), add="+")
                                    img_label.bind("<Button-1>", lambda e: _close_menu(), add="+")
                                
                                # Bind right-click (Button-3 on Windows/Linux, Button-2 on macOS)
                                img_label.bind("<Button-3>", _show_image_context_menu)  # Right-click
                                if platform.system() == "Darwin":
                                    img_label.bind("<Button-2>", _show_image_context_menu)  # macOS right-click
                                
                                # Update window size to fit image and keep it centered (same DPI logic as main window)
                                disp = pil_image_ref.get('image')
                                img_width = disp.width if disp else 500
                                img_height = disp.height if disp else 500
                                new_width = img_width + 40
                                new_height = img_height + 100
                                popup.geometry(f"{new_width}x{new_height}")
                                popup.update_idletasks()
                                scaling = popup._get_window_scaling()
                                screen_width = popup.winfo_screenwidth()
                                screen_height = popup.winfo_screenheight()
                                actual_width = popup.winfo_width()
                                actual_height = popup.winfo_height()
                                x_phys = (screen_width - actual_width) // 2
                                y_phys = (screen_height - actual_height) // 2
                                if platform.system() == "Windows":
                                    popup.geometry(f"+{x_phys}+{y_phys}")
                                else:
                                    x_logical = int(x_phys / scaling)
                                    y_logical = int(y_phys / scaling)
                                    popup.geometry(f"+{x_logical}+{y_logical}")
                        except Exception as e:
                            print(f"Error updating cover popup UI: {e}")
                    
                    if 'app' in globals() and app and app.winfo_exists():
                        app.after(0, _update_ui)
                else:
                    def _show_error():
                        if popup.winfo_exists():
                            loading_label.configure(text="Failed to load cover image")
                    if 'app' in globals() and app and app.winfo_exists():
                        app.after(0, _show_error)
            except Exception as e:
                print(f"Error loading full-size cover: {e}")
                def _show_error():
                    if popup.winfo_exists():
                        loading_label.configure(text="Error loading cover image")
                if 'app' in globals() and app and app.winfo_exists():
                    app.after(0, _show_error)
        
        # Start loading in background thread
        import threading
        thread = threading.Thread(target=_load_fullsize_image, daemon=True)
        thread.start()
        
    except Exception as e:
        print(f"Error creating cover popup: {e}")

def on_tree_click(event):
    """Handle clicks on the treeview, specifically for the Preview column and Cover column."""
    global tree, search_results_data
    
    try:
        if 'tree' not in globals() or not tree or not tree.winfo_exists():
            return
        
        # Identify the clicked region
        region = tree.identify("region", event.x, event.y)
        
        # Identify the column
        column = tree.identify_column(event.x)
        item_iid = tree.identify_row(event.y)
        
        if not item_iid:
            return
        
        # Find item data
        item_data = next((item for item in search_results_data if str(item.get('tree_iid')) == str(item_iid)), None)
        if not item_data:
            return
        
        # Cover vs Preview: use only the cover image width so play column is never treated as cover.
        # Tree column #0 can be reported wide on some themes/OS; use COVER_SIZE so clicks on play icon always count.
        is_over_cover_column = (event.x >= 0 and event.x <= COVER_SIZE)
        
        if is_over_cover_column:  # Cover column
            cover_url = item_data.get('cover_url')
            if cover_url:
                title = item_data.get('title', '')
                artist = item_data.get('artist', '')
                platform_name = item_data.get('platform', '')
                raw_result = item_data.get('raw_result')
                fallback_url = item_data.get('thumbnail_url')  # e.g. YouTube small thumbnail when full-size fails
                show_cover_popup(cover_url, title, artist, platform_name, raw_result, fallback_cover_url=fallback_url)
            return
        
        # Preview column: only the ≡/▶ column (not the whole row) for play/expand
        is_over_preview_column = (PREVIEW_COLUMN_START < event.x <= PREVIEW_COLUMN_START + PREVIEW_COLUMN_WIDTH)
        if not is_over_preview_column:
            return
        # Only reject header clicks; accept any row region (ttk can report "cell", "tree", or empty for child rows)
        if region == "heading":
            return
        
        # Preview column click: label/artist → show releases/albums (or tracks); album/playlist → show tracks
        if (item_data.get('type') or '').lower() == 'label':
            _fetch_and_show_artist_albums(item_iid, item_data)
            return
        if item_data.get('is_artist'):
            _fetch_and_show_artist_albums(item_iid, item_data)
            return
        if item_data.get('is_album_playlist'):
            _fetch_and_expand_album_playlist(item_iid, item_data)
            return
        # Track row (root or child): YouTube open in browser or play preview
        current_platform = item_data.get('platform', '').lower() if item_data.get('platform') else ''
        if current_platform == 'youtube':
            video_id = item_data.get('id')
            if video_id:
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                try:
                    webbrowser.open(youtube_url)
                    if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                        print(f"[YouTube] Opened video in browser: {youtube_url}")
                except Exception as e:
                    if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                        print(f"[YouTube] Error opening browser: {e}")
            return
        preview_url = item_data.get('preview_url')
        if preview_url:
            toggle_preview_playback(item_iid, preview_url)
        else:
            _try_lazy_load_preview(item_iid, item_data)
    except Exception as e:
        print(f"[Preview] Error handling tree click: {e}")

def _collapse_album_playlist(parent_iid):
    """Remove child track rows from an expanded album/playlist and update parent icon."""
    global tree, search_results_data, _expanded_album_playlist_iids
    try:
        if 'tree' not in globals() or not tree or not tree.winfo_exists():
            return
        children = list(tree.get_children(parent_iid))
        for child_iid in children:
            tree.delete(child_iid)
            search_results_data[:] = [d for d in search_results_data if str(d.get('tree_iid')) != str(child_iid)]
        _expanded_album_playlist_iids.discard(parent_iid)
        current_values = list(tree.item(parent_iid, 'values'))
        if current_values:
            current_values[0] = PREVIEW_EXPAND_COLLAPSED
            tree.item(parent_iid, values=tuple(current_values))
    except Exception as e:
        if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
            print(f"[Expand] Error collapsing album/playlist: {e}")

def _track_to_result_entry(track, index, parent_data, parent_iid, platform_str):
    """Convert a track (TrackInfo, dict, or plain ID) to a search result entry dict for display."""
    # Some modules (e.g. Deezer) return tracks as list of IDs; others return TrackInfo/dict with name, artists, etc.
    is_plain_id = isinstance(track, (str, int)) or (isinstance(track, dict) and not track.get('name') and not track.get('title'))
    if is_plain_id:
        tid = str(track) if isinstance(track, (str, int)) else str(track.get('id', ''))
        name = f"Track {index}"
        artist_str = (parent_data.get('artist') or parent_data.get('title') or '').strip() or ''
        duration_str = year_str = ''
        explicit_str = ''
        cover_url = ''
        preview_url = None
        raw = track
    else:
        tid = getattr(track, 'id', None) or (track.get('id') if isinstance(track, dict) else None) or ''
        name = getattr(track, 'name', None) or (track.get('name') if isinstance(track, dict) else None) or (track.get('title') if isinstance(track, dict) else None) or ''
        artists = getattr(track, 'artists', None) or (track.get('artists') if isinstance(track, dict) else []) or []
        artist_str = ', '.join([str(a) for a in artists]) if artists else ''
        dur = getattr(track, 'duration', None) or (track.get('duration') if isinstance(track, dict) else None)
        duration_str = beauty_format_seconds(dur) if dur is not None else ''
        year = getattr(track, 'release_year', None) or (track.get('release_year') if isinstance(track, dict) else None)
        year_str = '' if year is None or str(year) == 'None' else str(year)
        explicit = getattr(track, 'explicit', False) or (track.get('explicit') if isinstance(track, dict) else False)
        explicit_str = '🅴' if explicit else ''
        cover_url = getattr(track, 'cover_url', None) or (track.get('cover_url') if isinstance(track, dict) else None) or ''
        preview_url = getattr(track, 'preview_url', None) if hasattr(track, 'preview_url') else (track.get('preview_url') if isinstance(track, dict) else None)
        raw = track if not isinstance(track, dict) else track
        # Fallback to parent when track has no title/artist (e.g. partial metadata)
        if not name:
            name = f"Track {index}"
        if not artist_str:
            artist_str = (parent_data.get('artist') or '').strip() or ''
    child_iid = f"{parent_iid}_t{index}"
    return {
        "id": str(tid), "number": str(index), "title": name, "artist": artist_str,
        "duration": duration_str, "year": year_str, "additional": "", "explicit": explicit_str,
        "platform": platform_str, "type": "track", "raw_result": raw, "tree_iid": child_iid,
        "preview_url": preview_url, "cover_url": cover_url, "parent_iid": parent_iid
    }

def _insert_album_playlist_children(parent_iid, parent_data, track_entries):
    """Insert track rows under an album/playlist parent (main thread)."""
    global tree, search_results_data, _expanded_album_playlist_iids, app
    try:
        if 'tree' not in globals() or not tree or not tree.winfo_exists():
            return
        platform_str = parent_data.get('platform', 'Unknown')
        # Same logic as display_results: show play icon when preview available or platform supports lazy-load
        # Normalize platform (e.g. "Apple Music" -> "applemusic") for comparison
        platforms_with_preview = ('qobuz', 'soundcloud', 'spotify', 'tidal', 'youtube', 'deezer', 'applemusic')
        platform_key = (platform_str or '').lower().replace(' ', '')
        for entry in track_entries:
            tree_iid = entry['tree_iid']
            has_preview = bool(entry.get('preview_url'))
            can_lazy = platform_key in platforms_with_preview
            is_yt = platform_key == 'youtube'
            preview_icon = PREVIEW_PLAY_ICON if (has_preview or can_lazy or is_yt) else PREVIEW_UNAVAILABLE
            values = (
                preview_icon, entry.get('number', ''),
                entry.get('title', ''), entry.get('artist', ''),
                entry.get('duration', ''), entry.get('year', ''), entry.get('additional', ''), entry.get('explicit', ''),
                entry.get('id', '')
            )
            row_tag = "oddrow" if (int(entry.get('number', 0) or 0) % 2 == 1) else "evenrow"
            tree.insert(parent_iid, "end", iid=tree_iid, values=values, tags=(row_tag,))
            search_results_data.append(entry)
        _expanded_album_playlist_iids.add(parent_iid)
        try:
            tree.item(parent_iid, open=True)  # Expand parent so child tracks are visible
        except tkinter.TclError:
            pass
        current_values = list(tree.item(parent_iid, 'values'))
        if current_values:
            current_values[0] = PREVIEW_EXPAND_EXPANDED
            tree.item(parent_iid, values=tuple(current_values))
    except Exception as e:
        if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
            print(f"[Expand] Error inserting tracks: {e}")

def _fetch_and_expand_album_playlist(parent_iid, item_data):
    """Fetch album/playlist tracks in a background thread and expand the row on the main thread."""
    global orpheus_instance, app, tree, _expanded_album_playlist_iids, _expand_long_loading_after_id
    try:
        if 'orpheus_instance' not in globals() or not orpheus_instance or 'app' not in globals() or not app or not app.winfo_exists():
            return
        platform_name = (item_data.get('platform') or '').lower()
        item_type = (item_data.get('type') or '').lower()
        res_id = item_data.get('id')
        # Allow album, playlist, or YouTube channel (channel expand shows uploads as tracks)
        if not platform_name or not res_id:
            return
        if item_type not in ('album', 'playlist') and not (platform_name == 'youtube' and item_type == 'channel'):
            return
        # Show animated loading dots while fetching (same as preview lazy-load)
        if tree and tree.winfo_exists() and tree.exists(parent_iid):
            current_values = list(tree.item(parent_iid, 'values'))
            if current_values:
                current_values[0] = LOADING_ANIMATION_FRAMES[0]
                tree.item(parent_iid, values=tuple(current_values))
            _start_loading_animation(parent_iid)
        # After 8s show "Fetching all data... (this can take up to ~1 minute)" with walking dots
        if app and app.winfo_exists():
            _expand_long_loading_after_id = app.after(8000, _show_expand_long_loading_message)
        def worker():
            track_entries = []
            try:
                module_instance = orpheus_instance.load_module(platform_name)
                # SoundCloud requires data dict (id -> entity) for get_album_info/get_playlist_info
                if platform_name == 'soundcloud':
                    raw = item_data.get('raw_result')
                    data = {str(res_id): raw} if isinstance(raw, dict) else {}
                    if item_type == 'album':
                        info = module_instance.get_album_info(res_id, data) if (hasattr(module_instance, 'get_album_info') and data) else None
                    else:
                        info = module_instance.get_playlist_info(res_id, data) if (hasattr(module_instance, 'get_playlist_info') and data) else None
                else:
                    # For playlist, pass extra_kwargs from search result (e.g. Beatport is_chart=True for charts)
                    playlist_kwargs = {}
                    raw = item_data.get('raw_result')
                    if item_type == 'playlist' and raw is not None:
                        if hasattr(raw, 'extra_kwargs') and isinstance(getattr(raw, 'extra_kwargs'), dict):
                            playlist_kwargs = {k: v for k, v in getattr(raw, 'extra_kwargs').items() if k != 'raw_result'}
                        elif isinstance(raw, dict) and isinstance(raw.get('extra_kwargs'), dict):
                            playlist_kwargs = {k: v for k, v in raw.get('extra_kwargs', {}).items() if k != 'raw_result'}
                    if item_type == 'album':
                        info = module_instance.get_album_info(res_id) if hasattr(module_instance, 'get_album_info') else None
                    else:
                        info = module_instance.get_playlist_info(res_id, **playlist_kwargs) if hasattr(module_instance, 'get_playlist_info') else None
                if not info or not getattr(info, 'tracks', None):
                    return
                tracks = info.tracks
                extra_kwargs = getattr(info, 'track_extra_kwargs', None) or {}
                # If module returns only track IDs (e.g. Deezer), resolve to full TrackInfo for real titles
                quality_tier = codec_options = None
                try:
                    from utils.models import QualityEnum, CodecOptions
                    g = current_settings.get("globals", {}).get("general", {})
                    q = (g.get("quality") or g.get("download_quality") or "high").upper()
                    quality_tier = getattr(QualityEnum, q, QualityEnum.HIGH)
                    c = current_settings.get("globals", {}).get("codecs", {})
                    codec_options = CodecOptions(proprietary_codecs=c.get("proprietary_codecs", False), spatial_codecs=c.get("spatial_codecs", True))
                except Exception:
                    pass
                resolved = []
                for idx, track in enumerate(tracks, start=1):
                    if quality_tier is not None and codec_options is not None and hasattr(module_instance, 'get_track_info') and isinstance(track, (str, int)):
                        try:
                            t = module_instance.get_track_info(str(track), quality_tier, codec_options, **extra_kwargs)
                            if t is not None:
                                track = t
                        except Exception:
                            pass
                    resolved.append(track)
                # Deezer: album/playlist tracks are resolved from IDs; attach preview URLs in bulk for tracklist playback
                if platform_name == 'deezer' and resolved and tracks:
                    try:
                        # Use original track IDs (Deezer returns IDs; TrackInfo may not have id set)
                        track_ids = [str(tracks[i]) for i in range(len(resolved)) if i < len(tracks) and isinstance(tracks[i], (str, int))]
                        if not track_ids:
                            track_ids = [str(getattr(t, 'id', None) or (t.get('id') if isinstance(t, dict) else None)) for t in resolved if getattr(t, 'id', None) or (isinstance(t, dict) and t.get('id'))]
                        if track_ids and hasattr(module_instance, 'session') and hasattr(module_instance.session, 'get_tracks_public_data'):
                            public = module_instance.session.get_tracks_public_data(track_ids)
                            for i, t in enumerate(resolved):
                                tid = str(tracks[i]) if i < len(tracks) and isinstance(tracks[i], (str, int)) else str(getattr(t, 'id', None) or (t.get('id') if isinstance(t, dict) else None) or '')
                                if tid in public and public[tid].get('preview'):
                                    url = public[tid]['preview']
                                    if isinstance(t, dict):
                                        t['preview_url'] = url
                                    elif not isinstance(t, (str, int)):
                                        setattr(t, 'preview_url', url)
                    except Exception:
                        pass
                # Qobuz: attach sample URLs for album/playlist tracklist so preview plays without lazy-load
                if platform_name == 'qobuz' and resolved:
                    try:
                        get_sample = getattr(module_instance.session, 'get_sample_url', None) if hasattr(module_instance, 'session') else None
                        if get_sample:
                            for t in resolved:
                                tid = getattr(t, 'id', None) or (t.get('id') if isinstance(t, dict) else None)
                                if tid:
                                    url = get_sample(str(tid))
                                    if url:
                                        if isinstance(t, dict):
                                            t['preview_url'] = url
                                        else:
                                            setattr(t, 'preview_url', url)
                    except Exception:
                        pass
                for idx, track in enumerate(resolved, start=1):
                    entry = _track_to_result_entry(track, idx, item_data, parent_iid, platform_name)
                    # Hide entries with no duration (e.g. YouTube live streams)
                    if not entry.get('duration') and not entry.get('duration_seconds'):
                        continue
                    track_entries.append(entry)
            except Exception as e:
                if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                    print(f"[Expand] Error fetching album/playlist tracks: {e}")
                track_entries = []
            def on_done():
                _clear_expand_long_loading_message()
                _stop_loading_animation()
                if track_entries:
                    _show_album_track_list_view(item_data, track_entries)
                elif tree and tree.winfo_exists() and tree.exists(parent_iid):
                    current_values = list(tree.item(parent_iid, 'values'))
                    if current_values:
                        current_values[0] = PREVIEW_EXPAND_COLLAPSED
                        tree.item(parent_iid, values=tuple(current_values))
            try:
                if app and app.winfo_exists():
                    app.after(0, on_done)
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()
    except Exception as e:
        if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
            print(f"[Expand] Error starting expand: {e}")

def _fetch_and_show_artist_albums(parent_iid, item_data):
    """Fetch artist's albums and show them in the list view (like album track list). One get_artist_info call when module returns full album data."""
    global orpheus_instance, app, tree, _expand_long_loading_after_id
    try:
        if 'orpheus_instance' not in globals() or not orpheus_instance or 'app' not in globals() or not app or not app.winfo_exists():
            return
        platform_name = (item_data.get('platform') or '').lower()
        res_id = item_data.get('id')
        if not platform_name or not res_id:
            return
        if tree and tree.winfo_exists() and tree.exists(parent_iid):
            current_values = list(tree.item(parent_iid, 'values'))
            if current_values:
                current_values[0] = LOADING_ANIMATION_FRAMES[0]
                tree.item(parent_iid, values=tuple(current_values))
            _start_loading_animation(parent_iid)
        if app and app.winfo_exists():
            _expand_long_loading_after_id = app.after(8000, _show_expand_long_loading_message)
        def worker():
            album_entries = []
            context_kind = "Label" if (item_data.get('type') or '').lower() == 'label' else "Artist"
            def on_done():
                _clear_expand_long_loading_message()
                _stop_loading_animation()
                if album_entries:
                    _show_artist_albums_view(item_data, album_entries, context_kind)
                else:
                    if tree and tree.winfo_exists() and tree.exists(parent_iid):
                        current_values = list(tree.item(parent_iid, 'values'))
                        if current_values:
                            current_values[0] = PREVIEW_EXPAND_COLLAPSED
                            tree.item(parent_iid, values=tuple(current_values))
                    if platform_name == 'soundcloud':
                        try:
                            if app and app.winfo_exists() and 'show_centered_messagebox' in globals():
                                app.after(0, lambda: show_centered_messagebox("SoundCloud Artist", "No albums or tracks could be loaded for this artist. The API may not return content for this user, or the link may need to be opened from SoundCloud (e.g. soundcloud.com/username/albums).", dialog_type="info"))
                        except Exception:
                            pass
            def schedule_done():
                if app and app.winfo_exists():
                    try:
                        app.after(0, on_done)
                    except Exception:
                        pass
            try:
                module_instance = orpheus_instance.load_module(platform_name)
                # Label (Beatport/Beatsource): get_label_info -> releases + tracks
                if item_data.get('type') == 'label':
                    if not hasattr(module_instance, 'get_label_info'):
                        schedule_done()
                        return
                    try:
                        info = module_instance.get_label_info(res_id, **{})
                    except Exception as e:
                        if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                            print(f"[Label] Error get_label_info: {e}")
                        schedule_done()
                        return
                    if not info:
                        schedule_done()
                        return
                    albums = getattr(info, 'albums', None) or []
                    tracks = getattr(info, 'tracks', None) or []
                    label_name = getattr(info, 'name', '') or item_data.get('title') or item_data.get('artist') or 'Label'
                    album_extra = getattr(info, 'album_extra_kwargs', None) or {}
                    track_extra = getattr(info, 'track_extra_kwargs', None) or {}
                    album_data_dict = album_extra.get('data') if isinstance(album_extra, dict) else {}
                    track_data_dict = track_extra.get('data') if isinstance(track_extra, dict) else {}
                    platform_str = item_data.get('platform', 'Unknown')
                    if not albums and tracks and track_data_dict:
                        try:
                            quality_tier = codec_options = None
                            try:
                                from utils.models import QualityEnum, CodecOptions
                                g = current_settings.get("globals", {}).get("general", {})
                                q = (g.get("quality") or g.get("download_quality") or "high").upper()
                                quality_tier = getattr(QualityEnum, q, QualityEnum.HIGH)
                                c = current_settings.get("globals", {}).get("codecs", {})
                                codec_options = CodecOptions(proprietary_codecs=c.get("proprietary_codecs", False), spatial_codecs=c.get("spatial_codecs", True))
                            except Exception:
                                pass
                            resolved = []
                            for i, t in enumerate(tracks):
                                tid = str(t) if isinstance(t, (str, int)) else str(t.get('id', '')) if isinstance(t, dict) else ''
                                track_dict = track_data_dict.get(t) or track_data_dict.get(str(t)) or (track_data_dict.get(int(t)) if isinstance(t, str) and t.isdigit() else None)
                                if quality_tier and codec_options and hasattr(module_instance, 'get_track_info') and tid:
                                    try:
                                        tr = module_instance.get_track_info(tid, quality_tier, codec_options, **{'data': track_data_dict})
                                        resolved.append(tr if tr is not None else track_dict or t)
                                    except Exception:
                                        resolved.append(track_dict or t)
                                else:
                                    resolved.append(track_dict or t)
                            synthetic_label = dict(item_data)
                            synthetic_label['title'] = label_name
                            synthetic_label['type'] = 'label'
                            track_entries = [_track_to_result_entry(track, idx, synthetic_label, parent_iid, platform_name) for idx, track in enumerate(resolved, start=1)]
                            def on_done_label_tracks():
                                _clear_expand_long_loading_message()
                                _stop_loading_animation()
                                if track_entries:
                                    _show_album_track_list_view(synthetic_label, track_entries)
                                elif tree and tree.winfo_exists() and tree.exists(parent_iid):
                                    current_values = list(tree.item(parent_iid, 'values'))
                                    if current_values:
                                        current_values[0] = PREVIEW_EXPAND_COLLAPSED
                                        tree.item(parent_iid, values=tuple(current_values))
                            if app and app.winfo_exists():
                                app.after(0, on_done_label_tracks)
                        except Exception as e:
                            if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                                print(f"[Label] Error showing label tracks: {e}")
                        return
                    if not albums:
                        schedule_done()
                        return
                    display_idx = 0
                    for album in albums:
                        album_dict = None
                        if isinstance(album, dict):
                            album_dict = album
                        else:
                            aid = album
                            album_dict = album_data_dict.get(aid) or album_data_dict.get(str(aid)) or (album_data_dict.get(int(aid)) if str(aid).isdigit() else None)
                        if album_dict and isinstance(album_dict, dict):
                            title = album_dict.get('title') or album_dict.get('name', 'Unknown Release')
                            artist_raw = (album_dict.get('artists') or [{}])[0] if album_dict.get('artists') else {}
                            artist = artist_raw.get('name', 'Unknown') if isinstance(artist_raw, dict) else str(artist_raw)
                            cover_uri = (album_dict.get('image') or {}).get('dynamic_uri') if isinstance(album_dict.get('image'), dict) else None
                            if cover_uri and platform_name == 'beatport':
                                from modules.beatport.interface import ModuleInterface as _BPI
                                cover_url = _BPI._generate_artwork_url(cover_uri, 56)
                            elif cover_uri and platform_name == 'beatsource':
                                from modules.beatsource.interface import ModuleInterface as _BSI
                                cover_url = _BSI._generate_artwork_url(cover_uri, 56)
                            else:
                                cover_url = item_data.get('cover_url') or ''
                            year = ''
                            if album_dict.get('publish_date') and len(str(album_dict.get('publish_date'))) >= 4:
                                year = str(album_dict.get('publish_date'))[:4]
                            # Skip releases with no track count (hide them from the list)
                            tc = album_dict.get('track_count') or album_dict.get('tracks_count')
                            if tc is None:
                                continue
                            display_idx += 1
                            # Additional: track count and (Beatport) catalog number, like Album search
                            additional_parts = []
                            additional_parts.append(f"1 track" if tc == 1 else f"{tc} tracks")
                            if platform_name and platform_name.lower() == 'beatport' and album_dict.get('catalog_number'):
                                additional_parts.append(f"Cat: {album_dict['catalog_number']}")
                            additional_str = ", ".join(additional_parts) if additional_parts else ""
                            # Duration if release has total length (seconds or ms); format like album search
                            duration_str = ""
                            sec = None
                            if album_dict.get('duration') is not None:
                                try:
                                    sec = int(album_dict.get('duration'))
                                except (TypeError, ValueError):
                                    pass
                            elif album_dict.get('length_ms') is not None:
                                try:
                                    sec = int(album_dict.get('length_ms')) // 1000
                                except (TypeError, ValueError):
                                    pass
                            if sec is not None and 'beauty_format_seconds' in globals() and callable(beauty_format_seconds):
                                duration_str = beauty_format_seconds(sec)
                            elif sec is not None:
                                duration_str = str(sec)
                            entry = {
                                "tree_iid": f"label_release_{display_idx}",
                                "title": title,
                                "artist": artist,
                                "cover_url": cover_url,
                                "id": str(album_dict.get('id', album)),
                                "platform": platform_str,
                                "type": "album",
                                "is_album_playlist": True,
                                "number": str(display_idx),
                                "year": year,
                                "duration": duration_str,
                                "additional": additional_str,
                                "explicit": "",
                                "parent_iid": None,
                                "raw_result": album_dict,
                            }
                            album_entries.append(entry)
                    context_kind = "Label"
                    schedule_done()
                    return
                if not hasattr(module_instance, 'get_artist_info'):
                    schedule_done()
                    return
                # SoundCloud requires data dict (id -> entity) for get_artist_info
                if platform_name == 'soundcloud':
                    raw = item_data.get('raw_result')
                    # If raw_result is the SearchResult object (e.g. formatting fallback), get entity from extra_kwargs['data']
                    if not isinstance(raw, dict) and hasattr(raw, 'extra_kwargs'):
                        ek = getattr(raw, 'extra_kwargs', {}) or {}
                        if isinstance(ek, dict) and isinstance(ek.get('data'), dict):
                            d = ek['data']
                            raw = d.get(res_id) or d.get(str(res_id)) or (d.get(int(res_id)) if str(res_id).isdigit() else None) or (next(iter(d.values())) if d else None)
                    data = {}
                    if isinstance(raw, dict):
                        data[str(res_id)] = raw
                        if str(res_id).isdigit():
                            data[int(res_id)] = raw
                    # Module now handles empty data (fetches user name from API)
                    info = module_instance.get_artist_info(res_id, True, data)
                else:
                    info = module_instance.get_artist_info(res_id, get_credited_albums=True, **{})
                if not info:
                    schedule_done()
                    return
                albums = getattr(info, 'albums', None) or []
                tracks = getattr(info, 'tracks', None) or []
                platform_str = item_data.get('platform', 'Unknown')
                artist_name = item_data.get('artist') or getattr(info, 'name', '') or 'Artist'
                album_extra = getattr(info, 'album_extra_kwargs', None) or {}
                track_extra = getattr(info, 'track_extra_kwargs', None) or {}
                album_data_dict = album_extra.get('data') if isinstance(album_extra, dict) else {}
                track_data_dict = track_extra.get('data') if isinstance(track_extra, dict) else {}
                # No albums but has tracks: show tracks in tracklist view (e.g. SoundCloud artist, Beatport artist)
                if not albums and tracks and track_data_dict:
                    try:
                        quality_tier = codec_options = None
                        try:
                            from utils.models import QualityEnum, CodecOptions
                            g = current_settings.get("globals", {}).get("general", {})
                            q = (g.get("quality") or g.get("download_quality") or "high").upper()
                            quality_tier = getattr(QualityEnum, q, QualityEnum.HIGH)
                            c = current_settings.get("globals", {}).get("codecs", {})
                            codec_options = CodecOptions(proprietary_codecs=c.get("proprietary_codecs", False), spatial_codecs=c.get("spatial_codecs", True))
                        except Exception:
                            pass
                        resolved = []
                        total = len(tracks)
                        for i, t in enumerate(tracks):
                            if total > 20 and (i + 1) % 50 == 0 and i + 1 < total:
                                print(f"[Artist] Resolving tracks {i + 1}/{total}...", flush=True)
                            tid = str(t) if isinstance(t, (str, int)) else str(t.get('id', '')) if isinstance(t, dict) else ''
                            track_dict = track_data_dict.get(t) or track_data_dict.get(str(t)) or (track_data_dict.get(int(t)) if isinstance(t, str) and t.isdigit() else None)
                            if quality_tier and codec_options and hasattr(module_instance, 'get_track_info') and tid:
                                try:
                                    tr = module_instance.get_track_info(tid, quality_tier, codec_options, **{'data': track_data_dict})
                                    resolved.append(tr if tr is not None else track_dict or t)
                                except Exception:
                                    resolved.append(track_dict or t)
                            else:
                                resolved.append(track_dict or t)
                        synthetic_album = dict(item_data)
                        synthetic_album['title'] = artist_name
                        synthetic_album['type'] = 'artist'
                        track_entries = []
                        for idx, track in enumerate(resolved, start=1):
                            track_entries.append(_track_to_result_entry(track, idx, synthetic_album, parent_iid, platform_name))
                        def on_done_tracks():
                            _clear_expand_long_loading_message()
                            _stop_loading_animation()
                            if track_entries:
                                _show_album_track_list_view(synthetic_album, track_entries)
                            elif tree and tree.winfo_exists() and tree.exists(parent_iid):
                                current_values = list(tree.item(parent_iid, 'values'))
                                if current_values:
                                    current_values[0] = PREVIEW_EXPAND_COLLAPSED
                                    tree.item(parent_iid, values=tuple(current_values))
                        if app and app.winfo_exists():
                            app.after(0, on_done_tracks)
                    except Exception as e:
                        if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                            print(f"[Artist] Error showing artist tracks: {e}")
                        schedule_done()
                    return
                if not albums:
                    schedule_done()
                    return
                for idx, album in enumerate(albums, start=1):
                    # Resolve full album dict when we only have an id (e.g. SoundCloud returns list of ids; album_extra_kwargs['data'] has full dicts)
                    album_dict = None
                    if isinstance(album, dict):
                        album_dict = album
                    elif album_data_dict:
                        aid = album
                        album_dict = album_data_dict.get(aid) or album_data_dict.get(str(aid)) or (album_data_dict.get(int(aid)) if str(aid).isdigit() else None)
                    if album_dict and isinstance(album_dict, dict):
                        # Use full album metadata (SoundCloud: title, duration in ms, release_date/display_date/created_at; others: name, release_year, etc.)
                        dur = album_dict.get('duration')
                        duration_str = ''
                        if dur is not None:
                            try:
                                sec = int(dur)
                                if sec > 86400:  # > 1 day in seconds → assume milliseconds (e.g. SoundCloud)
                                    sec = sec // 1000
                                duration_str = beauty_format_seconds(sec)
                            except (TypeError, ValueError):
                                duration_str = str(dur)
                        title = album_dict.get('title') or album_dict.get('name', 'Unknown Album')
                        artist_raw = (album_dict.get('user') or {}).get('username') if isinstance(album_dict.get('user'), dict) else album_dict.get('artist', artist_name)
                        # Tidal/Qobuz etc. return artist as dict {'id', 'name', ...}; extract name
                        artist = (artist_raw.get('name') if isinstance(artist_raw, dict) else artist_raw) or artist_name
                        cover_url = album_dict.get('artwork_url') or album_dict.get('cover_url') or ''
                        # Tidal: cover is a UUID, not a URL; generate Tidal image URL
                        if not cover_url and platform_str.lower().replace(' ', '') == 'tidal':
                            cover_id = album_dict.get('cover')
                            if cover_id:
                                cover_url = f'https://resources.tidal.com/images/{str(cover_id).replace("-", "/")}/750x750.jpg'
                        if cover_url and '-large' in cover_url:
                            cover_url = cover_url.replace('-large', '-t200x200')
                        year = ''
                        for key in ('release_date', 'display_date', 'created_at', 'releaseDate', 'streamStartDate'):
                            val = album_dict.get(key)
                            if val and isinstance(val, str) and len(val) >= 4:
                                year = val[:4]
                                break
                        if not year and album_dict.get('release_year'):
                            year = str(album_dict.get('release_year'))
                        entry = {
                            "tree_iid": f"artist_album_{idx}",
                            "title": title,
                            "artist": artist,
                            "cover_url": cover_url,
                            "id": str(album_dict.get('id', album) if album_dict.get('id') is not None else album),
                            "platform": platform_str,
                            "type": "album",
                            "is_album_playlist": True,
                            "number": str(idx),
                            "year": year,
                            "duration": duration_str,
                            "additional": album_dict.get('additional') or album_dict.get('genre') or '',
                            "explicit": "",
                            "parent_iid": None,
                            "raw_result": album_dict,
                        }
                    else:
                        entry = {
                            "tree_iid": f"artist_album_{idx}",
                            "title": "Album",
                            "artist": artist_name,
                            "cover_url": "",
                            "id": str(album),
                            "platform": platform_str,
                            "type": "album",
                            "is_album_playlist": True,
                            "number": str(idx),
                            "year": "",
                            "duration": "",
                            "additional": "",
                            "explicit": "",
                            "parent_iid": None,
                        }
                        if album_data_dict:
                            aid = entry['id']
                            entry['raw_result'] = album_data_dict.get(aid) or album_data_dict.get(int(aid)) if str(aid).isdigit() else album_data_dict.get(aid)
                    album_entries.append(entry)
            except Exception as e:
                if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                    print(f"[Artist] Error fetching artist albums: {e}")
                album_entries = []
            schedule_done()
        threading.Thread(target=worker, daemon=True).start()
    except Exception as e:
        if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
            print(f"[Artist] Error starting artist albums fetch: {e}")

def _show_artist_albums_view(artist_item_data, album_entries, context_kind="Artist"):
    """Show an artist's or label's albums/releases in the results list. context_kind is 'Artist' or 'Label'. Call on main thread."""
    global search_results_data, tree, app, _album_track_list_context, results_label, _back_to_search_button, _expanded_album_playlist_iids
    try:
        if 'tree' not in globals() or not tree or not tree.winfo_exists():
            return
        # Stack: each level stores saved_data to restore and the header title when we back to that level (RESULTS for search list)
        _album_track_list_context = [{"saved_data": list(search_results_data), "title": "RESULTS"}]
        name = artist_item_data.get('artist') or artist_item_data.get('title') or (context_kind if context_kind == "Label" else "Artist")
        artist_view_title = f"{context_kind}: {name}"
        platform_str = artist_item_data.get('platform', 'Unknown')
        _expanded_album_playlist_iids.clear()
        clear_treeview()
        search_results_data = album_entries
        for idx, item_data in enumerate(album_entries):
            tree_iid = item_data["tree_iid"]
            values = (
                PREVIEW_EXPAND_COLLAPSED,
                item_data.get('number', ''),
                item_data.get('title', ''),
                item_data.get('artist', ''),
                item_data.get('duration', ''),
                item_data.get('year', ''),
                item_data.get('additional', ''),
                item_data.get('explicit', ''),
                item_data.get('id', '')
            )
            row_tag = "oddrow" if (idx % 2 == 1) else "evenrow"
            tree.insert("", "end", iid=tree_iid, values=values, tags=(row_tag,))
        # When showing albums list (artist or label), 4th column is Artist; ensure heading says "Artist"
        try:
            if 'tree' in globals() and tree and tree.winfo_exists():
                tree.heading("Artist", text="Artist")
        except (tkinter.TclError, Exception):
            pass
        _update_preview_column_heading(True)  # ≡ for artist albums list
        if '_back_to_search_button' in globals() and _back_to_search_button and _back_to_search_button.winfo_exists():
            if results_label and results_label.winfo_exists():
                results_label.pack_forget()
            _back_to_search_button.pack(side="left", anchor="w", padx=(6, 12), pady=0)
            _update_results_header_context(artist_view_title)
            if results_label and results_label.winfo_exists():
                results_label.pack(side="left", anchor="w", padx=6, pady=0)
        elif 'results_label' in globals() and results_label and results_label.winfo_exists():
            results_label.configure(text=artist_view_title)
        if 'app' in globals() and app and app.winfo_exists():
            app.after(100, lazy_load_visible_covers)
            app.after(50, lambda: _check_and_toggle_scrollbar(tree, scrollbar) if 'tree' in globals() and tree and tree.winfo_exists() and 'scrollbar' in globals() and scrollbar and scrollbar.winfo_exists() else None)
    except Exception as e:
        if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
            print(f"[Artist] Error showing artist albums: {e}")

def _show_album_track_list_view(album_item_data, track_entries):
    """Show an album/playlist's tracks in the results list (flat, with previews) instead of inline expand. Call on main thread."""
    global search_results_data, tree, app, _album_track_list_context, results_label, _back_to_search_button, _expanded_album_playlist_iids, _currently_playing_preview_iid
    try:
        if 'tree' not in globals() or not tree or not tree.winfo_exists():
            return
        # Clear playback state so the new tracklist doesn't inherit "playing" for same iids (e.g. album_track_3)
        if _currently_playing_preview_iid:
            stop_audio()
            _currently_playing_preview_iid = None
            hide_volume_control()
        # Stack: push current view (artist albums) so Back restores it with correct header (badge + name)
        parent_title = (_current_results_header_title or "") if '_current_results_header_title' in globals() else ""
        if not isinstance(_album_track_list_context, list):
            _album_track_list_context = [_album_track_list_context] if _album_track_list_context else []
        _album_track_list_context.append({
            "saved_data": list(search_results_data),
            "title": parent_title
        })
        item_type = (album_item_data.get('type') or '').lower()
        platform_key = (album_item_data.get('platform') or '').lower()
        if platform_key == 'youtube' and item_type == 'channel':
            kind = "Channel"
            title = album_item_data.get('artist') or album_item_data.get('title') or album_item_data.get('name') or 'Channel'
        else:
            title = album_item_data.get('title') or album_item_data.get('name') or 'Album'
            if item_type == 'artist':
                kind = "Artist"
            elif item_type == 'label':
                kind = "Label"
            elif item_type == 'playlist':
                kind = "Playlist"
            else:
                kind = "Album"
        album_view_title = f"{kind}: {title}"
        platform_str = album_item_data.get('platform', 'Unknown')
        album_cover_url = album_item_data.get('cover_url') or ''
        platforms_with_preview = ('qobuz', 'soundcloud', 'spotify', 'tidal', 'youtube', 'deezer', 'applemusic')
        platform_key = (platform_str or '').lower().replace(' ', '')
        # Use distinct tree_iids (album_track_1, ...) so we don't overwrite cover cache for original search (item_1, ...)
        flat = []
        for idx, entry in enumerate(track_entries, start=1):
            copy = dict(entry)
            copy["tree_iid"] = f"album_track_{idx}"
            copy["parent_iid"] = None
            copy["number"] = str(idx)
            # Use album/playlist cover for all rows so display and click-to-popup use the same URL
            copy["cover_url"] = album_cover_url or copy.get("cover_url")
            copy["platform"] = copy.get("platform") or platform_str  # ensure platform set for preview/lazy-load
            flat.append(copy)
        _expanded_album_playlist_iids.clear()
        clear_treeview()
        search_results_data = flat
        # Insert rows like track search: preview icon, values, tags
        for idx, item_data in enumerate(flat):
            tree_iid = item_data["tree_iid"]
            has_preview = bool(item_data.get('preview_url'))
            can_lazy = platform_key in platforms_with_preview
            is_yt = platform_key == 'youtube'
            preview_icon = (PREVIEW_PLAY_ICON if (has_preview or can_lazy or is_yt) else PREVIEW_UNAVAILABLE)
            values = (
                preview_icon,
                item_data.get('number', ''),
                item_data.get('title', ''),
                item_data.get('artist', ''),
                item_data.get('duration', ''),
                item_data.get('year', ''),
                item_data.get('additional', ''),
                item_data.get('explicit', ''),
                item_data.get('id', '')
            )
            row_tag = "oddrow" if (idx % 2 == 1) else "evenrow"
            tree.insert("", "end", iid=tree_iid, values=values, tags=(row_tag,))
        # Load album cover once and apply to all rows (already loaded from search, so fast)
        if album_cover_url and flat:
            global _cover_load_requested
            all_iids = [e["tree_iid"] for e in flat]
            for iid in all_iids:
                _cover_load_requested.add(iid)
            load_cover_from_url(album_cover_url, size=COVER_SIZE, item_iid=flat[0]["tree_iid"], apply_to_iids=all_iids)
        _update_preview_column_heading(False)  # ▶ for track list
        try:
            if 'tree' in globals() and tree and tree.winfo_exists():
                tree.heading("Artist", text="Artist")  # Track list always shows Artist, not Channel
        except (NameError, tkinter.TclError, Exception):
            pass
        if '_back_to_search_button' in globals() and _back_to_search_button and _back_to_search_button.winfo_exists():
            if results_label and results_label.winfo_exists():
                results_label.pack_forget()
            _back_to_search_button.pack(side="left", anchor="w", padx=(6, 12), pady=0)
            _update_results_header_context(album_view_title)
            if results_label and results_label.winfo_exists():
                results_label.pack(side="left", anchor="w", padx=6, pady=0)
        elif 'results_label' in globals() and results_label and results_label.winfo_exists():
            results_label.configure(text=album_view_title)
        if 'app' in globals() and app and app.winfo_exists():
            app.after(100, lazy_load_visible_covers)
            app.after(50, lambda: _check_and_toggle_scrollbar(tree, scrollbar) if 'tree' in globals() and tree and tree.winfo_exists() and 'scrollbar' in globals() and scrollbar and scrollbar.winfo_exists() else None)
    except Exception as e:
        if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
            print(f"[Album list] Error showing album track list: {e}")

def _update_results_header_context(full_title):
    """Update results header with optional content-type badge (Album/Playlist/Artist) and title. full_title=None means normal RESULTS view."""
    global results_label, _content_type_badge, _content_type_badge_label, _current_results_header_title
    _current_results_header_title = full_title
    if full_title is None:
        if '_content_type_badge' in globals() and _content_type_badge and _content_type_badge.winfo_exists():
            _content_type_badge.pack_forget()
        if 'results_label' in globals() and results_label and results_label.winfo_exists():
            results_label.configure(text="RESULTS")
        return
    type_str = None
    rest = full_title
    if full_title.startswith("Album: "):
        type_str = "album"
        rest = full_title[7:]
    elif full_title.startswith("Playlist: "):
        type_str = "playlist"
        rest = full_title[10:]
    elif full_title.startswith("Artist: "):
        type_str = "artist"
        rest = full_title[8:]
    elif full_title.startswith("Label: "):
        type_str = "label"
        rest = full_title[7:]
    elif full_title.startswith("Channel: "):
        type_str = "channel"
        rest = full_title[9:]
    if type_str and '_content_type_badge' in globals() and _content_type_badge and _content_type_badge_label and _content_type_badge_label.winfo_exists():
        _content_type_badge_label.configure(text=type_str)
        # Slightly wider badge for "Channel"; on macOS "Playlist" also needs 60 (same as channel) to avoid truncation
        badge_width = 60 if type_str == "channel" or (platform.system() == "Darwin" and type_str == "playlist") else 50
        _content_type_badge.configure(width=badge_width)
        _content_type_badge.pack(side="left", anchor="w", padx=(0, 8), pady=0)
    if 'results_label' in globals() and results_label and results_label.winfo_exists():
        results_label.configure(text=rest)

def _back_to_search_results():
    """Restore the previous search results view (after viewing an album/playlist track list)."""
    global search_results_data, tree, _album_track_list_context, results_label, _back_to_search_button, _expanded_album_playlist_iids
    global _currently_playing_preview_iid, _cover_hover_cache, _cover_image_cache, _cover_load_requested, _content_type_badge
    try:
        if _album_track_list_context is None:
            return
        # Support both stack (list) and legacy single dict
        if isinstance(_album_track_list_context, dict):
            _album_track_list_context = [_album_track_list_context]
        if not _album_track_list_context:
            return
        context = _album_track_list_context.pop()
        saved = context.get("saved_data") or []
        restore_title = context.get("title")
        _expanded_album_playlist_iids.clear()
        # Restoring to artist albums view? Then keep artist_album_* in caches so their covers still show.
        restoring_to_artist_albums = any(
            str(item.get('tree_iid', '')).startswith('artist_album_') for item in saved
        )
        # Remove album track list entries from cover caches (we're leaving tracklist view). Only remove artist_album_* if we're not restoring to artist albums view.
        for iid in list(_cover_image_cache.keys()):
            if not isinstance(iid, str):
                continue
            if iid.startswith("album_track_"):
                del _cover_image_cache[iid]
            elif iid.startswith("artist_album_") and not restoring_to_artist_albums:
                del _cover_image_cache[iid]
        for iid in list(_cover_hover_cache.keys()):
            if not isinstance(iid, str):
                continue
            if iid.startswith("album_track_"):
                del _cover_hover_cache[iid]
            elif iid.startswith("artist_album_") and not restoring_to_artist_albums:
                del _cover_hover_cache[iid]
        _cover_load_requested -= {iid for iid in _cover_load_requested if isinstance(iid, str) and iid.startswith("album_track_")}
        if not restoring_to_artist_albums:
            _cover_load_requested -= {iid for iid in _cover_load_requested if isinstance(iid, str) and iid.startswith("artist_album_")}
        clear_treeview()
        search_results_data = saved
        # Repopulate tree from saved_data (root-level only; same logic as sort_results)
        for idx, item_data in enumerate(saved):
            try:
                if 'tree' not in globals() or not tree or not tree.winfo_exists():
                    break
                tree_iid = item_data.get('tree_iid', item_data.get('id', ''))
                parent_iid = item_data.get('parent_iid') or ""
                preview_url = item_data.get('preview_url')
                platform_str = item_data.get('platform', 'Unknown')
                search_type_str = item_data.get('type', 'track')
                is_track_search = search_type_str.lower() == "track"
                can_lazy_load_preview = (platform_str.lower().replace(' ', '') in ('qobuz', 'soundcloud', 'spotify', 'tidal', 'deezer', 'applemusic')) and is_track_search
                is_youtube_track = (platform_str.lower().replace(' ', '') == 'youtube') and is_track_search
                is_album_playlist = item_data.get('is_album_playlist')
                is_artist = item_data.get('is_artist')
                if is_album_playlist or is_artist:
                    preview_icon = PREVIEW_EXPAND_COLLAPSED
                elif preview_url or can_lazy_load_preview or is_youtube_track:
                    preview_icon = PREVIEW_STOP_ICON if (_currently_playing_preview_iid == tree_iid) else PREVIEW_PLAY_ICON
                else:
                    preview_icon = PREVIEW_UNAVAILABLE
                values = (preview_icon, item_data.get('number', ''), item_data.get('title', ''), item_data.get('artist', ''), item_data.get('duration', ''), item_data.get('year', ''), item_data.get('additional', ''), item_data.get('explicit', ''), item_data.get('id', ''))
                row_tag = "oddrow" if (idx % 2 == 0) else "evenrow"
                is_playing = _currently_playing_preview_iid == tree_iid
                tags = (row_tag, "playing") if (is_playing and preview_url) else (row_tag,)
                # Use normal cover (not hover/darkened) when restoring so rows don't all look hovered
                cover_image = _cover_image_cache.get(tree_iid) or _cover_hover_cache.get(tree_iid)
                if cover_image:
                    tree.insert(parent_iid, "end", iid=tree_iid, values=values, image=cover_image, tags=tags)
                else:
                    tree.insert(parent_iid, "end", iid=tree_iid, values=values, tags=tags)
            except (tkinter.TclError, Exception):
                pass
        show_expand_in_header = restoring_to_artist_albums or any(
            item.get('is_artist') or item.get('is_album_playlist') for item in saved
        )
        _update_preview_column_heading(show_expand_in_header)
        # Restore column header to "Label" when going back to label search results
        try:
            if saved and len(saved) > 0 and (saved[0].get('type') or '').lower() == 'label' and 'tree' in globals() and tree and tree.winfo_exists():
                tree.heading("Artist", text="Label")
        except (tkinter.TclError, Exception):
            pass
        # Restore header for this level (e.g. "Artist: Name" when going back from album tracks)
        _update_results_header_context(restore_title if (restore_title and restore_title != "RESULTS") else None)
        if not _album_track_list_context:
            _update_results_header_context(None)
            if '_back_to_search_button' in globals() and _back_to_search_button and _back_to_search_button.winfo_exists():
                _back_to_search_button.pack_forget()
        if 'app' in globals() and app and app.winfo_exists() and 'tree' in globals() and tree and tree.winfo_exists() and 'scrollbar' in globals() and scrollbar and scrollbar.winfo_exists():
            app.after(50, lambda: _check_and_toggle_scrollbar(tree, scrollbar))
    except Exception as e:
        if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
            print(f"[Back] Error restoring search results: {e}")

def _try_lazy_load_preview(item_iid, item_data):
    """Try to lazy-load a preview URL for services that don't include them in search results (e.g., Qobuz, SoundCloud, Spotify)."""
    global platform_var, orpheus_instance, tree, search_results_data, app, _lazy_loading_preview_iid, _currently_playing_preview_iid
    
    try:
        # Check if we have the necessary globals
        if 'orpheus_instance' not in globals() or not orpheus_instance:
            return
        # Use row's platform (so child tracks use correct platform); fallback to search dropdown
        current_platform = (item_data.get('platform') or (platform_var.get() if 'platform_var' in globals() and platform_var else '')).lower().replace(' ', '')
        if not current_platform:
            return
        # Services that support lazy-loading of preview URLs (for search and expanded album/playlist child tracks)
        lazy_load_services = ['qobuz', 'soundcloud', 'spotify', 'tidal', 'deezer', 'applemusic']
        if current_platform not in lazy_load_services:
            return
        
        # Get the track ID from the item data (works for root tracks and child tracks from expanded album/playlist)
        track_id = item_data.get('id')
        if not track_id:
            return
        
        # Stop any currently playing preview BEFORE starting lazy load
        if _currently_playing_preview_iid:
            stop_audio()
            old_iid = _currently_playing_preview_iid
            _currently_playing_preview_iid = None
            if 'tree' in globals() and tree and tree.winfo_exists():
                update_preview_icon(old_iid, playing=False)
            # Hide volume control
            hide_volume_control()
        
        # Track which item is being loaded
        _lazy_loading_preview_iid = item_iid
        
        # Show loading indicator
        if 'tree' in globals() and tree and tree.winfo_exists():
            try:
                current_values = list(tree.item(item_iid, 'values'))
                if current_values:
                    current_values[0] = PREVIEW_LOADING_ICON
                    tree.item(item_iid, values=tuple(current_values))
                    # Start walking dots animation
                    _start_loading_animation(item_iid)
            except Exception:
                pass
        
        # Capture target_iid to check later
        target_iid = item_iid
        
        # Fetch preview URL in background thread
        def fetch_preview_url():
            global _lazy_loading_preview_iid
            preview_url = None
            try:
                # Check if user clicked on another item while we were loading
                if _lazy_loading_preview_iid != target_iid:
                    print(f"[Preview] Lazy load cancelled for {target_iid}")
                    return
                
                module_instance = orpheus_instance.load_module(current_platform)
                
                if current_platform == 'qobuz':
                    # Qobuz: use get_sample_url method
                    if hasattr(module_instance, 'session') and hasattr(module_instance.session, 'get_sample_url'):
                        preview_url = module_instance.session.get_sample_url(track_id)
                
                elif current_platform == 'soundcloud':
                    # SoundCloud: use get_preview_stream_url (pass track_authorization from album/playlist track if available)
                    if hasattr(module_instance, 'websession') and hasattr(module_instance.websession, 'get_preview_stream_url'):
                        track_auth = None
                        raw = item_data.get('raw_result')
                        if hasattr(raw, 'download_extra_kwargs') and isinstance(getattr(raw, 'download_extra_kwargs'), dict):
                            track_auth = raw.download_extra_kwargs.get('track_authorization')
                        elif isinstance(raw, dict) and isinstance(raw.get('download_extra_kwargs'), dict):
                            track_auth = raw['download_extra_kwargs'].get('track_authorization')
                        preview_url = module_instance.websession.get_preview_stream_url(track_id, track_auth)
                
                elif current_platform == 'spotify':
                    # Spotify: preview_url is deprecated in API, scrape from embed page
                    # See: https://community.spotify.com/t5/Spotify-for-Developers/Preview-URLs-Deprecated/td-p/6791368
                    if hasattr(module_instance, 'spotify_api') and hasattr(module_instance.spotify_api, 'get_preview_url_from_embed'):
                        preview_url = module_instance.spotify_api.get_preview_url_from_embed(track_id)
                        if preview_url:
                            print(f"[Preview] Spotify preview URL found: {preview_url[:80]}...")
                        else:
                            print(f"[Preview] No Spotify preview found for track {track_id}")
                
                elif current_platform == 'tidal':
                    # Tidal: preview URLs are not included in search results, fetch using LOW quality stream
                    if hasattr(module_instance, 'get_preview_stream_url'):
                        preview_url = module_instance.get_preview_stream_url(track_id)
                        if preview_url:
                            print(f"[Preview] Tidal preview URL found: {preview_url[:80]}...")
                        else:
                            print(f"[Preview] No Tidal preview found for track {track_id}")
                
                elif current_platform == 'deezer':
                    # Deezer: 30s preview from public API (works for search and expanded album/playlist tracks)
                    if hasattr(module_instance, 'session') and hasattr(module_instance.session, 'get_track_preview_url'):
                        preview_url = module_instance.session.get_track_preview_url(track_id)
                        if preview_url and current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                            print(f"[Preview] Deezer preview URL found for track {track_id}")
                
                elif current_platform == 'applemusic':
                    # Apple Music: 30s preview from get_song attributes.previews (search and expanded album/playlist child tracks)
                    if hasattr(module_instance, 'apple_music_api') and hasattr(module_instance.apple_music_api, 'get_song'):
                        try:
                            track_data = module_instance.apple_music_api.get_song(track_id)
                            if track_data and isinstance(track_data, dict) and 'attributes' in track_data:
                                attrs = track_data.get('attributes', {})
                                previews = attrs.get('previews', [])
                                if previews and len(previews) > 0:
                                    preview_url = previews[0].get('url')
                        except Exception:
                            pass
                
                # Check again before updating UI
                if _lazy_loading_preview_iid != target_iid:
                    print(f"[Preview] Lazy load cancelled for {target_iid}")
                    return
                
                # Update UI on main thread
                if 'app' in globals() and app and app.winfo_exists():
                    app.after(0, lambda: _on_preview_url_fetched(target_iid, item_data, preview_url))
                    
            except Exception as e:
                print(f"[Preview] Error fetching preview URL for {current_platform} track {track_id}: {e}")
                # Restore unavailable icon on error
                if 'app' in globals() and app and app.winfo_exists():
                    app.after(0, lambda: _on_preview_url_fetched(target_iid, item_data, None))
        
        # Start background thread
        threading.Thread(target=fetch_preview_url, daemon=True).start()
        
    except Exception as e:
        print(f"[Preview] Error in lazy load: {e}")

def _on_preview_url_fetched(item_iid, item_data, preview_url):
    """Called when a lazy-loaded preview URL has been fetched."""
    global tree, search_results_data, _lazy_loading_preview_iid
    
    try:
        # Stop loading animation
        _stop_loading_animation()
        
        # Check if this item is still the one being loaded (user might have clicked elsewhere)
        if _lazy_loading_preview_iid != item_iid:
            # User clicked on another item or stopped - just update the data but don't play
            if preview_url:
                item_data['preview_url'] = preview_url
            return
        
        # Clear the loading state
        _lazy_loading_preview_iid = None
        
        if preview_url:
            # Update the cached preview URL in search_results_data
            item_data['preview_url'] = preview_url
            
            # Update the icon to play icon
            if 'tree' in globals() and tree and tree.winfo_exists():
                try:
                    current_values = list(tree.item(item_iid, 'values'))
                    if current_values:
                        current_values[0] = PREVIEW_PLAY_ICON
                        tree.item(item_iid, values=tuple(current_values))
                except Exception:
                    pass
            
            # Start playing the preview
            toggle_preview_playback(item_iid, preview_url)
        else:
            # No preview URL available, restore unavailable icon (platform-specific message)
            platform_str = (item_data.get('platform') or '').lower().replace(' ', '')
            if platform_str == 'spotify':
                print(f"[Preview] No preview available for this track (Spotify embed had no preview)")
            elif platform_str == 'soundcloud':
                print(f"[Preview] No preview available for this track (SoundCloud). The track may be restricted in your region or not streamable.")
            elif platform_str:
                print(f"[Preview] No preview available for this track ({platform_str})")
            else:
                print(f"[Preview] No preview available for this track")
            if 'tree' in globals() and tree and tree.winfo_exists():
                try:
                    current_values = list(tree.item(item_iid, 'values'))
                    if current_values:
                        current_values[0] = PREVIEW_UNAVAILABLE
                        tree.item(item_iid, values=tuple(current_values))
                except Exception:
                    pass
            # Show user-friendly message in GUI for SoundCloud when preview unavailable (e.g. geo-restricted)
            if platform_str == 'soundcloud' and 'show_centered_messagebox' in globals():
                try:
                    if app and app.winfo_exists():
                        app.after(0, lambda: show_centered_messagebox("Preview unavailable", "This track has no preview (it may be restricted in your region or not streamable on SoundCloud).", dialog_type="info"))
                except Exception:
                    pass
    except Exception as e:
        print(f"[Preview] Error updating preview URL: {e}")

def clear_preview_state():
    """Clear the preview playback state when search results are cleared."""
    global _currently_playing_preview_iid, _cover_image_cache, _cover_hover_cache, _cover_hover_iid, _preview_hover_iid, _cover_load_requested, _lazy_loading_preview_iid
    
    # Run stop_audio in a daemon thread to avoid blocking main thread (can cause deadlock on macOS
    # when main thread blocks while Tk background threads wait for it)
    def _stop_audio_async():
        try:
            stop_audio()
        except Exception:
            pass
    threading.Thread(target=_stop_audio_async, daemon=True).start()
    
    _stop_pulse_animation()  # Stop pulsing animation
    _stop_loading_animation()  # Stop loading animation
    _currently_playing_preview_iid = None
    _preview_hover_iid = None
    _lazy_loading_preview_iid = None  # Cancel any pending lazy loads
    _cover_image_cache.clear()
    _cover_hover_cache.clear()
    global _cover_hover_iid
    _cover_hover_iid = None
    _cover_load_requested.clear()  # Clear lazy loading state
    # Hide volume control
    hide_volume_control()

def show_volume_control():
    """Show the volume control slider when audio is playing. Only on Windows (macOS/Linux cannot regulate volume from GUI)."""
    global _volume_frame
    if platform.system() != "Windows":
        return
    try:
        if _volume_frame and _volume_frame.winfo_exists():
            _volume_frame.pack(side="right", padx=(10, 12))
    except:
        pass

def hide_volume_control():
    """Hide the volume control slider when audio stops."""
    global _volume_frame
    try:
        if _volume_frame and _volume_frame.winfo_exists():
            _volume_frame.pack_forget()
    except:
        pass

def on_volume_change(value):
    """Handle volume slider changes."""
    global _current_volume
    _current_volume = int(float(value))
    set_audio_volume(_current_volume)

def set_audio_volume(volume):
    """Set the audio playback volume (0-100)."""
    system = platform.system()
    try:
        if system == "Windows":
            # Use waveOutSetVolume - controls wave output mixer, works with winsound
            # Volume is 0xFFFF for max, packed as (right << 16) | left for stereo
            wave_volume = int((volume / 100) * 0xFFFF)
            stereo_volume = (wave_volume << 16) | wave_volume  # Same volume for left and right
            ctypes.windll.winmm.waveOutSetVolume(0, stereo_volume)
            
        # Note: macOS afplay doesn't support runtime volume change easily
        # Linux xdg-open also doesn't support it
    except Exception as e:
        if _audio_debug():
            print(f"[Audio] Error setting volume: {e}")
# ============================================================================
if platform.system() == "Windows":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(2) 
        print("[DPI] Set Per Monitor V2 DPI Awareness (2)")
    except Exception as e1:
        try:
            windll.user32.SetProcessDpiAware()
            print("[DPI] Set System DPI Awareness (Legacy) - Fallback")
        except Exception as e2:
            print(f"[DPI] Warning: Could not set DPI awareness ({e1} / {e2})")

    # Create named mutex for installer detection
    try:
        from ctypes import windll
        # Create a named mutex. The handle must be kept alive for the process lifetime.
        # We use a Local mutex (no "Global\" prefix) to avoid permission issues.
        # This allows the installer (running in the same session) to detect the app.
        _mutex_handle = windll.kernel32.CreateMutexW(None, False, "OrpheusDL-GUI-Mutex")
        if windll.kernel32.GetLastError() == 183: # ERROR_ALREADY_EXISTS
            print("[Mutex] AppMutex already exists (another instance is likely running)")
        else:
            print("[Mutex] Created AppMutex: OrpheusDL-GUI-Mutex")
    except Exception as e:
        print(f"[Mutex] Failed to create AppMutex: {e}")

def get_script_directory():
    """Gets the directory containing the script/executable, handling bundled apps."""
    if getattr(sys, 'frozen', False):
        abs_executable_path = os.path.abspath(sys.executable)
        
        if platform.system() == "Darwin":
            if ".app/Contents/MacOS" in abs_executable_path:
                dir_of_executable = os.path.dirname(abs_executable_path)
                app_bundle_contents_dir = os.path.dirname(dir_of_executable)
                app_bundle_itself_path = os.path.dirname(app_bundle_contents_dir)
                return os.path.dirname(app_bundle_itself_path)
            else:
                return os.path.dirname(abs_executable_path)
        else:
            return os.path.dirname(abs_executable_path)
    else:
        try:
            script_path = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            try:
                script_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
            except AttributeError:
                script_path = os.path.abspath(os.path.dirname(sys.argv[0]))
        return script_path

def get_data_directory():
    """Gets the directory for user data (config, modules, extensions).
    
    On macOS bundled apps, uses ~/Library/Application Support/OrpheusDL GUI/
    since apps in /Applications cannot write to their own directory.
    Otherwise, uses the script directory.
    """
    is_frozen = getattr(sys, 'frozen', False)
    has_meipass = hasattr(sys, '_MEIPASS')
    is_macos = platform.system() == "Darwin"
    abs_executable_path = os.path.abspath(sys.executable)
    initial_cwd = os.getcwd()
    
    # Write debug info to a file in home directory for debugging compiled apps
    debug_log_path = os.path.expanduser("~/orpheusdl_gui_debug.log")
    try:
        with open(debug_log_path, 'a') as f:
            f.write(f"\n=== get_data_directory() called at {__import__('datetime').datetime.now()} ===\n")
            f.write(f"sys.frozen: {is_frozen}\n")
            f.write(f"sys._MEIPASS exists: {has_meipass}\n")
            f.write(f"sys._MEIPASS value: {getattr(sys, '_MEIPASS', 'N/A')}\n")
            f.write(f"platform.system(): {platform.system()}\n")
            f.write(f"sys.executable: {sys.executable}\n")
            f.write(f"abs_executable_path: {abs_executable_path}\n")
            f.write(f"initial CWD: {initial_cwd}\n")
            f.write(f"__file__ (if exists): {globals().get('__file__', 'N/A')}\n")
    except Exception as e:
        print(f"[DEBUG] Could not write debug log: {e}")
    
    # Multiple detection methods for macOS .app bundles
    is_macos_app_bundle = False
    detection_reason = ""
    
    if is_macos:
        # Method 1: Check if executable path contains .app/Contents/MacOS
        if ".app/Contents/MacOS" in abs_executable_path:
            is_macos_app_bundle = True
            detection_reason = "found .app/Contents/MacOS in executable path"
        # Method 2: Check if _MEIPASS contains .app
        elif has_meipass and ".app" in getattr(sys, '_MEIPASS', ''):
            is_macos_app_bundle = True
            detection_reason = "found .app in _MEIPASS"
        # Method 3: Check if CWD is in /Applications or contains .app
        elif "/Applications" in initial_cwd or ".app" in initial_cwd:
            is_macos_app_bundle = True
            detection_reason = "CWD suggests app bundle (/Applications or .app in path)"
        # Method 4: Check if frozen and running on macOS (conservative fallback)
        elif is_frozen and has_meipass:
            is_macos_app_bundle = True
            detection_reason = "frozen PyInstaller app on macOS"
            
    # Windows Program Files check (install for all users = read-only, cannot write config/temp)
    if is_frozen and platform.system() == "Windows":
        exe_dir_lower = abs_executable_path.lower()
        if "program files" in exe_dir_lower or "program files (x86)" in exe_dir_lower:
            # Use LOCALAPPDATA (e.g. C:\Users\<user>\AppData\Local\OrpheusDL-GUI)
            local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
            app_data_dir = os.path.join(local_app_data, "OrpheusDL-GUI")
            try:
                os.makedirs(app_data_dir, exist_ok=True)
                print(f"[Windows] Executable in Program Files - using writable data dir: {app_data_dir}")
                try:
                    with open(debug_log_path, 'a') as f:
                        f.write(f"RESULT: Windows Program Files detected, using: {app_data_dir}\n")
                except:
                    pass
                return app_data_dir
            except Exception as e:
                print(f"[Windows] ERROR: Could not create data directory {app_data_dir}: {e}")
                # Fallback to script dir (may fail on write, but better than nothing)
                pass
    
    # Linux installation check
    print(f"[get_data_directory] Checking Linux: frozen={is_frozen}, platform={platform.system()}")
    if is_frozen and platform.system().lower() == "linux":
        print("[get_data_directory] Linux detected")
        # Use ~/.config/OrpheusDL-GUI for installed Linux apps
        config_dir = os.path.expanduser("~/.config/OrpheusDL-GUI")
        try:
            os.makedirs(config_dir, exist_ok=True)
            print(f"[Linux] Using config directory: {config_dir}")
            return config_dir
        except Exception as e:
            print(f"[Linux] ERROR: Could not create config directory: {e}")
            # Fallback to tmp
            return os.path.join("/tmp", "OrpheusDL-GUI")
    
    print(f"[get_data_directory] frozen={is_frozen}, has_meipass={has_meipass}, platform={platform.system()}, is_app_bundle={is_macos_app_bundle}")
    print(f"[get_data_directory] Executable path: {abs_executable_path}")
    print(f"[get_data_directory] Initial CWD: {initial_cwd}")
    if is_macos_app_bundle:
        print(f"[get_data_directory] Detection reason: {detection_reason}")
    
    # Write detection result to debug log
    try:
        with open(debug_log_path, 'a') as f:
            f.write(f"is_macos_app_bundle: {is_macos_app_bundle}\n")
            f.write(f"detection_reason: {detection_reason}\n")
    except:
        pass
    
    if is_macos_app_bundle:
        script_dir = get_script_directory()
        print(f"[get_data_directory] Script dir for bundled app: {script_dir}")
        
        # For bundled macOS apps, always use Application Support
        # This is the correct macOS convention and avoids permission issues
        app_support = os.path.expanduser("~/Library/Application Support/OrpheusDL GUI")
        try:
            os.makedirs(app_support, exist_ok=True)
            print(f"[macOS] Using Application Support directory: {app_support}")
            # Write final result to debug log
            try:
                with open(debug_log_path, 'a') as f:
                    f.write(f"RESULT: Using Application Support: {app_support}\n")
            except:
                pass
            return app_support
        except Exception as e:
            print(f"[macOS] ERROR: Could not create Application Support directory: {e}")
            import traceback
            traceback.print_exc()
            # Last resort fallback
            try:
                with open(debug_log_path, 'a') as f:
                    f.write(f"ERROR: Could not create Application Support: {e}\n")
                    f.write(f"FALLBACK: Using script_dir: {script_dir}\n")
            except:
                pass
            return script_dir
    
    # Default: use the script directory (development mode or non-macOS)
    result = get_script_directory()
    try:
        with open(debug_log_path, 'a') as f:
            f.write(f"RESULT: Using script directory: {result}\n")
    except:
        pass
    return result
    
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        try:
             base_path = os.path.dirname(os.path.abspath(__file__))
        except NameError:
             base_path = os.path.abspath(".")
        if not os.path.isdir(base_path):
             base_path = get_script_directory()

    final_path = os.path.join(base_path, relative_path)
    
    # Fallback: if the file doesn't exist at the calculated path, check the current working directory
    if not os.path.exists(final_path):
        cwd_path = os.path.join(os.getcwd(), relative_path)
        if os.path.exists(cwd_path):
            return cwd_path
            
    return final_path

def find_system_ffmpeg():
    """
    Find FFmpeg on macOS or Linux. Returns (found: bool, path: str).
    Checks common locations first, then system PATH.
    """
    import subprocess
    
    # Common FFmpeg locations by platform
    if platform.system() == 'Darwin':
        # macOS - Homebrew locations
        common_paths = [
            '/opt/homebrew/bin/ffmpeg',   # Apple Silicon
            '/usr/local/bin/ffmpeg',      # Intel
        ]
        
        # Add local app directories for manual installation (fallback)
        try:
            common_paths.append(os.path.join(get_data_directory(), 'ffmpeg'))
            common_paths.append(os.path.join(get_script_directory(), 'ffmpeg'))
        except Exception:
            pass
    elif platform.system() == 'Linux':
        # Linux - common package manager locations
        common_paths = [
            '/usr/bin/ffmpeg',            # apt, dnf, pacman
            '/usr/local/bin/ffmpeg',      # manual install
            '/snap/bin/ffmpeg',           # snap
        ]
    else:
        common_paths = []
    
    for path in common_paths:
        if os.path.isfile(path):
            try:
                result = subprocess.run([path, '-version'], capture_output=True, timeout=3)
                if result.returncode == 0:
                    return True, path
            except:
                pass
    
    # Try system PATH using 'which' (works on both macOS and Linux)
    try:
        result = subprocess.run(['which', 'ffmpeg'], capture_output=True, timeout=3)
        if result.returncode == 0:
            ffmpeg_path = result.stdout.decode().strip()
            if ffmpeg_path:
                return True, ffmpeg_path
    except:
        pass
    
    return False, None


def find_system_deno():
    """
    Find Deno on macOS/Linux (not bundled there). Returns (found: bool, path: str or None).
    Checks PATH and common locations. Only runs on Darwin/Linux; Windows may bundle deno.
    """
    system = platform.system()
    if system not in ('Darwin', 'Linux'):
        return True, None  # Only check on macOS/Linux; Windows may bundle deno
    import subprocess
    common_paths = []
    if system == 'Darwin':
        common_paths = ['/opt/homebrew/bin/deno', '/usr/local/bin/deno']
        try:
            common_paths.append(os.path.expanduser('~/.deno/bin/deno'))  # curl install
        except Exception:
            pass
    else:
        # Linux
        common_paths = ['/usr/bin/deno', '/usr/local/bin/deno']
        try:
            common_paths.append(os.path.expanduser('~/.deno/bin/deno'))
        except Exception:
            pass
    try:
        common_paths.append(os.path.join(get_data_directory(), 'deno'))
        common_paths.append(os.path.join(get_script_directory(), 'deno'))
    except Exception:
        pass
    for path in common_paths:
        if os.path.isfile(path):
            try:
                result = subprocess.run([path, '--version'], capture_output=True, timeout=3)
                if result.returncode == 0:
                    _ensure_deno_dir_in_path(path)
                    return True, path
            except Exception:
                pass
    try:
        result = subprocess.run(['which', 'deno'], capture_output=True, timeout=3)
        if result.returncode == 0:
            deno_path = result.stdout.decode().strip()
            if deno_path:
                _ensure_deno_dir_in_path(deno_path)
                return True, deno_path
    except Exception:
        pass
    return False, None


def _ensure_deno_dir_in_path(deno_path):
    """Prepend the directory containing deno to PATH so yt-dlp (and subprocesses) can find it.
    Needed on macOS when the app is launched from Finder and PATH does not include ~/.deno/bin."""
    if not deno_path or not os.path.isfile(deno_path):
        return
    deno_dir = os.path.dirname(os.path.abspath(deno_path))
    if not deno_dir:
        return
    path_sep = os.path.pathsep
    current = os.environ.get('PATH', '')
    if deno_dir in current.split(path_sep):
        return
    os.environ['PATH'] = deno_dir + path_sep + current


def _show_deno_install_message():
    """Show a pop-up with Deno install instructions (macOS/Linux; Deno is not bundled). Shown when user tries to download from YouTube."""
    system = platform.system()
    if system not in ('Darwin', 'Linux'):
        return
    try:
        if 'app' not in globals() or not app or not app.winfo_exists():
            return
    except Exception:
        return
    dialog = customtkinter.CTkToplevel(app)
    dialog.title("Deno Not Found")
    dialog.resizable(False, False)
    dialog.attributes("-topmost", True)
    dialog.transient(app)

    def copy_command(cmd, button):
        try:
            if not _copy_to_system_clipboard(cmd):
                app.clipboard_clear()
                app.clipboard_append(cmd)
                app.update()
            original_text = button.cget("text")
            button.configure(text="✓")
            button.after(1500, lambda: button.configure(text=original_text))
        except Exception as e:
            print(f"Error copying to clipboard: {e}")

    main_frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    title_label = customtkinter.CTkLabel(
        main_frame,
        text="⚠️  Deno Not Found",
        font=("", 18, "bold")
    )
    title_label.pack(pady=(0, 10))

    desc_label = customtkinter.CTkLabel(
        main_frame,
        text="Deno is required for YouTube downloads on macOS and Linux.\nInstall it to continue.",
        justify="center"
    )
    desc_label.pack(pady=(0, 15))

    # Step 1: Install via terminal (works on both macOS and Linux)
    step1_frame = customtkinter.CTkFrame(main_frame, fg_color="#2B2B2B", corner_radius=8)
    step1_frame.pack(fill="x", pady=5)
    step1_label = customtkinter.CTkLabel(step1_frame, text="1. Install via terminal:", anchor="w")
    step1_label.pack(fill="x", padx=10, pady=(8, 2))
    deno_curl_cmd = "curl -fsSL https://deno.land/install.sh | sh"
    cmd1_frame = customtkinter.CTkFrame(step1_frame, fg_color="#1E1E1E", corner_radius=5)
    cmd1_frame.pack(fill="x", padx=10, pady=(2, 8))
    cmd1_label = customtkinter.CTkLabel(cmd1_frame, text=deno_curl_cmd, font=("Segoe UI", 10), anchor="w", text_color="#98C379")
    cmd1_label.pack(side="left", fill="x", expand=True, padx=10, pady=8)
    copy1_btn = customtkinter.CTkButton(
        cmd1_frame, text="⧉", width=24, height=24,
        font=("Segoe UI", 14),
        fg_color="#2B2B2B", hover_color="#3B3B3B",
        text_color="#999999", corner_radius=3,
        command=lambda: copy_command(deno_curl_cmd, copy1_btn)
    )
    copy1_btn.pack(side="right", padx=8, pady=5)

    if system == 'Darwin':
        dialog.geometry("580x420")
        # Step 2: Or via Homebrew (macOS)
        step2_frame = customtkinter.CTkFrame(main_frame, fg_color="#2B2B2B", corner_radius=8)
        step2_frame.pack(fill="x", pady=5)
        step2_label = customtkinter.CTkLabel(step2_frame, text="2. Or via Homebrew (macOS):", anchor="w")
        step2_label.pack(fill="x", padx=10, pady=(8, 2))
        deno_brew_cmd = "brew install deno"
        cmd2_frame = customtkinter.CTkFrame(step2_frame, fg_color="#1E1E1E", corner_radius=5)
        cmd2_frame.pack(fill="x", padx=10, pady=(2, 8))
        cmd2_label = customtkinter.CTkLabel(cmd2_frame, text=deno_brew_cmd, font=("Segoe UI", 11), anchor="w", text_color="#98C379")
        cmd2_label.pack(side="left", fill="x", expand=True, padx=10, pady=8)
        copy2_btn = customtkinter.CTkButton(
            cmd2_frame, text="⧉", width=24, height=24,
            font=("Segoe UI", 14),
            fg_color="#2B2B2B", hover_color="#3B3B3B",
            text_color="#999999", corner_radius=3,
            command=lambda: copy_command(deno_brew_cmd, copy2_btn)
        )
        copy2_btn.pack(side="right", padx=8, pady=5)
    else:
        # Linux: package manager options
        dialog.geometry("580x520")
        step2_frame = customtkinter.CTkFrame(main_frame, fg_color="#2B2B2B", corner_radius=8)
        step2_frame.pack(fill="x", pady=5)
        step2_label = customtkinter.CTkLabel(step2_frame, text="2. Or via package manager:", anchor="w")
        step2_label.pack(fill="x", padx=10, pady=(8, 2))
        linux_deno_commands = [
            ("Ubuntu / Debian:", "curl -fsSL https://deno.land/install.sh | sh  # then add ~/.deno/bin to PATH"),
            ("Fedora:", "sudo dnf install deno"),
            ("Arch Linux:", "sudo pacman -S deno"),
        ]
        for distro, cmd in linux_deno_commands:
            cmd_frame = customtkinter.CTkFrame(step2_frame, fg_color="#1E1E1E", corner_radius=5)
            cmd_frame.pack(fill="x", padx=10, pady=3)
            cmd_label = customtkinter.CTkLabel(cmd_frame, text=cmd, font=("Segoe UI", 10), anchor="w", text_color="#98C379")
            cmd_label.pack(side="left", fill="x", expand=True, padx=10, pady=6)
            copy_btn = customtkinter.CTkButton(
                cmd_frame, text="⧉", width=24, height=24,
                font=("Segoe UI", 14),
                fg_color="#2B2B2B", hover_color="#3B3B3B",
                text_color="#999999", corner_radius=3,
                command=lambda: None
            )
            copy_btn.pack(side="right", padx=8, pady=4)
            copy_btn.configure(command=lambda c=cmd, b=copy_btn: copy_command(c, b))

    note_label = customtkinter.CTkLabel(
        main_frame,
        text="Ensure deno is in your system PATH, or symlink it to the OrpheusDL root folder.",
        font=("", 11),
        text_color="#898c8d",
        justify="left",
        wraplength=520
    )
    note_label.pack(fill="x", pady=(10, 5))

    ok_btn = customtkinter.CTkButton(main_frame, text="OK", command=dialog.destroy, width=100)
    ok_btn.pack(pady=(10, 0))

    dialog.update_idletasks()
    dw = dialog.winfo_width()
    dh = dialog.winfo_height()
    if app.winfo_exists():
        x = app.winfo_rootx() + (app.winfo_width() - dw) // 2
        y = app.winfo_rooty() + (app.winfo_height() - dh) // 2
        dialog.geometry(f"+{x}+{y}")


# Keep old function name for backward compatibility
def find_macos_ffmpeg():
    """Alias for find_system_ffmpeg for backward compatibility."""
    return find_system_ffmpeg()


def copy_bundled_resources_to_data_dir(data_dir):
    """
    Copy bundled resources (modules, ffmpeg) from the PyInstaller bundle to the data directory.
    This is needed on macOS where the app bundle is read-only but we need writable data locations.
    On macOS, FFmpeg is NOT bundled - users should install via Homebrew to avoid Gatekeeper issues.
    """
    import shutil
    
    if not getattr(sys, 'frozen', False) or not hasattr(sys, '_MEIPASS'):
        return  # Only run for frozen PyInstaller apps
    
    bundle_path = sys._MEIPASS
    print(f"[Resource Copy] Checking bundled resources in: {bundle_path}")
    
    # Copy modules if bundled and destination is empty
    bundled_modules = os.path.join(bundle_path, 'modules')
    dest_modules = os.path.join(data_dir, 'modules')
    
    if os.path.isdir(bundled_modules):
        bundled_module_list = [d for d in os.listdir(bundled_modules) if os.path.isdir(os.path.join(bundled_modules, d))]
        if bundled_module_list:
            os.makedirs(dest_modules, exist_ok=True)
            # Copy each bundled module that is missing in destination (first run or app update with new modules e.g. youtube)
            for module_name in bundled_module_list:
                src = os.path.join(bundled_modules, module_name)
                dst = os.path.join(dest_modules, module_name)
                if not os.path.exists(dst):
                    try:
                        shutil.copytree(src, dst)
                        print(f"[Resource Copy] Copied module: {module_name}")
                    except Exception as e:
                        print(f"[Resource Copy] Failed to copy module {module_name}: {e}")
    else:
        print(f"[Resource Copy] No bundled modules found at {bundled_modules}")
    
    # Handle FFmpeg based on platform
    if platform.system() == 'Windows':
        # On Windows, copy bundled ffmpeg
        ffmpeg_name = 'ffmpeg.exe'
        bundled_ffmpeg = os.path.join(bundle_path, ffmpeg_name)
        dest_ffmpeg = os.path.join(data_dir, ffmpeg_name)
        
        if os.path.isfile(bundled_ffmpeg) and not os.path.isfile(dest_ffmpeg):
            try:
                shutil.copy2(bundled_ffmpeg, dest_ffmpeg)
                print(f"[Resource Copy] Copied ffmpeg to {dest_ffmpeg}")
            except Exception as e:
                print(f"[Resource Copy] Failed to copy ffmpeg: {e}")
        elif os.path.isfile(dest_ffmpeg):
            print(f"[Resource Copy] ffmpeg already exists at {dest_ffmpeg}")
        else:
            print(f"[Resource Copy] No bundled ffmpeg found at {bundled_ffmpeg}")
        # On Windows, prepend app dir to PATH so bundled deno.exe is findable by yt-dlp
        app_dir = get_script_directory()
        if app_dir and app_dir not in os.environ.get('PATH', '').split(os.pathsep):
            os.environ['PATH'] = app_dir + os.pathsep + os.environ.get('PATH', '')
            print(f"[Resource Copy] Prepended app dir to PATH for Deno: {app_dir}")
    elif platform.system() == 'Darwin':
        # On macOS, don't bundle FFmpeg - check for Homebrew installation instead
        print(f"[FFmpeg] macOS detected - using system FFmpeg (Homebrew recommended)")
        ffmpeg_found, ffmpeg_path = find_system_ffmpeg()
        if ffmpeg_found:
            print(f"[FFmpeg] Found FFmpeg at: {ffmpeg_path}")
            # Add FFmpeg directory to PATH so subprocess calls (like in ffmpeg-python) can find it
            ffmpeg_dir = os.path.dirname(ffmpeg_path)
            if ffmpeg_dir not in os.environ["PATH"]:
                os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]
                print(f"[FFmpeg] Prepended {ffmpeg_dir} to PATH")
        else:
            print(f"[FFmpeg] FFmpeg not found. Audio conversion will not work.")
            print(f"[FFmpeg] Install via Homebrew: brew install ffmpeg")
    elif platform.system() == 'Linux':
        # On Linux, don't bundle FFmpeg - use system package manager
        print(f"[FFmpeg] Linux detected - using system FFmpeg")
        ffmpeg_found, ffmpeg_path = find_system_ffmpeg()
        if ffmpeg_found:
            print(f"[FFmpeg] Found FFmpeg at: {ffmpeg_path}")
        else:
            print(f"[FFmpeg] FFmpeg not found. Audio conversion will not work.")
            print(f"[FFmpeg] Install via package manager: sudo apt install ffmpeg")
_app_dir = get_script_directory()
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

# Global placeholders for lazy loading
Orpheus = None
MediaIdentification = None
ManualEnum = None
ModuleModes = None
Downloader = None
ImageFileTypeEnum = None
CoverCompressionEnum = None
Oprinter = None
DownloadTypeEnum = None
ORPHEUS_AVAILABLE = False
_original_resource_path = None

def beauty_format_seconds(s): return str(s) # Default simple implementation

def _import_orpheus_modules():
    global Orpheus, MediaIdentification, ManualEnum, ModuleModes, Downloader
    global ImageFileTypeEnum, CoverCompressionEnum, Oprinter, DownloadTypeEnum
    global ORPHEUS_AVAILABLE, beauty_format_seconds, _original_resource_path
    
    try:
        # Import orpheus.core first to patch resource_path
        import orpheus.core
        
        # Patch resource_path
        if hasattr(orpheus.core, 'resource_path'):
            _original_resource_path = orpheus.core.resource_path
            print("[Patch] Stored original orpheus.core.resource_path")

            def patched_resource_path(relative_path):
                """ Patched version to always return path relative to executable dir """
                executable_dir = get_script_directory()
                patched_path = os.path.join(executable_dir, relative_path)
                return patched_path

            orpheus.core.resource_path = patched_resource_path
            print("[Patch] Patched orpheus.core.resource_path")
        else:
            print("[Patch] WARNING: orpheus.core.resource_path not found for patching.")

        # Import components
        from orpheus.core import Orpheus as _Orpheus, MediaIdentification as _MediaIdentification, ManualEnum as _ManualEnum, ModuleModes as _ModuleModes
        from orpheus.music_downloader import beauty_format_seconds as _beauty_format_seconds, Downloader as _Downloader
        from utils.models import (ImageFileTypeEnum as _ImageFileTypeEnum, CoverCompressionEnum as _CoverCompressionEnum, Oprinter as _Oprinter, DownloadTypeEnum as _DownloadTypeEnum)
        
        Orpheus = _Orpheus
        MediaIdentification = _MediaIdentification
        ManualEnum = _ManualEnum
        ModuleModes = _ModuleModes
        beauty_format_seconds = _beauty_format_seconds
        Downloader = _Downloader
        ImageFileTypeEnum = _ImageFileTypeEnum
        CoverCompressionEnum = _CoverCompressionEnum
        Oprinter = _Oprinter
        DownloadTypeEnum = _DownloadTypeEnum
        
        ORPHEUS_AVAILABLE = True
        print("[Import] Orpheus modules imported successfully.")
        
    except (ImportError, AttributeError) as e:
        print(f"ERROR: Failed to import Orpheus library components: {e}. Core functionality will be unavailable.")
        # Define dummy classes if import fails
        class Orpheus: pass
        class MediaIdentification: pass
        class ManualEnum: manual = 1
        class ModuleModes: lyrics=1; covers=2; credits=3
        class Downloader: pass
        class ImageFileTypeEnum(enum.Enum): pass
        class CoverCompressionEnum(enum.Enum): pass
        class Oprinter: pass
        class DownloadTypeEnum(enum.Enum): track="track"; artist="artist"; playlist="playlist"; album="album"
        ORPHEUS_AVAILABLE = False
_original_get_terminal_size = os.get_terminal_size

def _patched_get_terminal_size(fd=None):
    """Patched os.get_terminal_size to prevent 'bad file descriptor' under pythonw.exe."""
    try:
        if fd is not None:
            return _original_get_terminal_size(fd)
        else:
            return _original_get_terminal_size()
    except (OSError, ValueError) as e:
        is_bad_fd_error = isinstance(e, ValueError) and 'bad file descriptor' in str(e)
        is_pythonw = sys.executable and sys.executable.lower().endswith("pythonw.exe")
        if is_bad_fd_error or is_pythonw:
            try: pass
            except Exception: pass
            return os.terminal_size((80, 24))
        else:
            raise e

os.get_terminal_size = _patched_get_terminal_size
try:
    print("[Patch] Applied os.get_terminal_size monkey-patch.", file=sys.stderr)
except Exception: pass
if platform.system() == "Windows":
    import subprocess
    _original_popen = subprocess.Popen
    
    class _PatchedPopen(_original_popen):
        """Patched subprocess.Popen class to suppress console windows on Windows."""
        def __init__(self, *args, **kwargs):
            try:
                if 'creationflags' not in kwargs:
                    kwargs['creationflags'] = 0
                kwargs['creationflags'] |= subprocess.CREATE_NO_WINDOW
                if 'startupinfo' not in kwargs:
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                    kwargs['startupinfo'] = startupinfo
                    
            except Exception as e:
                print(f"[Patch Warning] Could not set subprocess flags to hide console: {e}", file=sys.__stderr__)
            
            super().__init__(*args, **kwargs)
    
    subprocess.Popen = _PatchedPopen
    try:
        print("[Patch] Applied subprocess.Popen patch to suppress console windows on Windows.", file=sys.__stdout__)
    except Exception: pass

try:
    from customtkinter.windows.widgets import CTkEntry, CTkCheckBox, CTkComboBox
    import tkinter

    print("[Patch] Attempting to patch CTkEntry, CTkCheckBox, and CTkComboBox _draw methods...")
    _original_ctkentry_draw = CTkEntry._draw

    def _patched_ctkentry_draw(self, *args, **kwargs):
        try:
            return _original_ctkentry_draw(self, *args, **kwargs)
        except tkinter.TclError as e:
            if "invalid command name" in str(e):
                pass
            else:
                raise e
        except Exception as e:
            print(f"[Patch Error] Unexpected error in CTkEntry._draw for {self}: {type(e).__name__}: {e}")
            raise e

    CTkEntry._draw = _patched_ctkentry_draw
    print("[Patch] Patched CTkEntry._draw method.")
    _original_ctkcheckbox_draw = CTkCheckBox._draw

    def _patched_ctkcheckbox_draw(self, *args, **kwargs):
        try:
            return _original_ctkcheckbox_draw(self, *args, **kwargs)
        except tkinter.TclError as e:
            if "invalid command name" in str(e):
                pass
            else:
                raise e
        except Exception as e:
            print(f"[Patch Error] Unexpected error in CTkCheckBox._draw for {self}: {type(e).__name__}: {e}")
            raise e

    CTkCheckBox._draw = _patched_ctkcheckbox_draw
    print("[Patch] Patched CTkCheckBox._draw method.")
    _original_ctkcombobox_draw = CTkComboBox._draw
                                                                                  
    def _patched_ctkcombobox_draw(self, *args, **kwargs):
        try:
            return _original_ctkcombobox_draw(self, *args, **kwargs)
        except tkinter.TclError as e:
            if "invalid command name" in str(e):
                pass
            else:
                raise e
        except Exception as e:
            print(f"[Patch Error] Unexpected error in CTkComboBox._draw for {self}: {type(e).__name__}: {e}")
            raise e
                                                                                  
    CTkComboBox._draw = _patched_ctkcombobox_draw
    print("[Patch] Patched CTkComboBox._draw method.")

except ImportError:
    print("[Patch Warning] Could not import CTkEntry, CTkCheckBox, or CTkComboBox for patching _draw methods.")
except Exception as e:
    print(f"[Patch Error] Failed to apply CustomTkinter _draw patches: {e}")

# CTkToolTip is treated as a window by customtkinter's scaling_tracker but lacks these methods.
try:
    if not hasattr(CTkToolTip, 'block_update_dimensions_event'):
        CTkToolTip.block_update_dimensions_event = lambda self: None
        print("[Patch] Patched CTkToolTip.block_update_dimensions_event (no-op).")
    if not hasattr(CTkToolTip, 'unblock_update_dimensions_event'):
        CTkToolTip.unblock_update_dimensions_event = lambda self: None
        print("[Patch] Patched CTkToolTip.unblock_update_dimensions_event (no-op).")
except Exception as e:
    print(f"[Patch Warning] Could not patch CTkToolTip for scaling tracker: {e}")

class OrpheusdlError(Exception): pass
class AuthenticationError(OrpheusdlError): pass
class DownloadError(OrpheusdlError): pass
class NetworkError(OrpheusdlError): pass

class DownloadCancelledError(Exception):
    """Locally defined placeholder for missing exception."""
    pass

class QualityEnum(enum.Enum):
    HIFI = 1
    HIGH = 2
    LOW = 3

def deep_merge(dict1, dict2, keys_to_overwrite_if_dicts=None):
    """Deep merge two dictionaries.
    
    Args:
        dict1: The dictionary to merge into.
        dict2: The dictionary to merge from.
        keys_to_overwrite_if_dicts: A list of keys for which, if both dict1[key]
                                     and dict2[key] are dictionaries, dict1[key]
                                     will be replaced by dict2[key] instead of
                                     their contents being recursively merged.
    """
    if keys_to_overwrite_if_dicts is None:
        keys_to_overwrite_if_dicts = []

    for key, value2 in dict2.items():
        if key in dict1:
            value1 = dict1[key]
            if isinstance(value1, dict) and isinstance(value2, dict):
                if key in keys_to_overwrite_if_dicts:
                    dict1[key] = value2
                else:
                    deep_merge(value1, value2, keys_to_overwrite_if_dicts) 
            else:
                dict1[key] = value2
        else:
            dict1[key] = value2
    return dict1

def load_settings():
    """Loads settings directly from ./config/settings.json."""
    global current_settings, CONFIG_FILE_PATH, DEFAULT_SETTINGS

    settings = {
        "globals": copy.deepcopy(DEFAULT_SETTINGS["globals"]),
        "credentials": {},
        "modules": {}
    }

    if not os.path.exists(CONFIG_FILE_PATH):
        # Create default settings file on first run
        print(f"Configuration file not found at '{CONFIG_FILE_PATH}'. Creating default settings...")
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE_PATH), exist_ok=True)
            
            # Auto-detect FFmpeg for default settings
            default_ffmpeg_path = "ffmpeg"
            
            if platform.system() == "Darwin":
                # On macOS, use Homebrew FFmpeg (avoids Gatekeeper issues)
                ffmpeg_found, ffmpeg_path = find_system_ffmpeg()
                if ffmpeg_found:
                    default_ffmpeg_path = ffmpeg_path
                    print(f"[FFmpeg] Using Homebrew FFmpeg: {ffmpeg_path}")
                else:
                    default_ffmpeg_path = "ffmpeg"  # Will use PATH, show error if not found
                    print(f"[FFmpeg] Homebrew FFmpeg not found - install with: brew install ffmpeg")
            elif platform.system() == "Linux":
                # On Linux, use system FFmpeg
                ffmpeg_found, ffmpeg_path = find_system_ffmpeg()
                if ffmpeg_found:
                    default_ffmpeg_path = ffmpeg_path
                    print(f"[FFmpeg] Using system FFmpeg: {ffmpeg_path}")
                else:
                    default_ffmpeg_path = "ffmpeg"  # Will use PATH, show error if not found
                    print(f"[FFmpeg] FFmpeg not found - install with: sudo apt install ffmpeg")
            else:
                # On Windows, check for bundled ffmpeg
                ffmpeg_name = "ffmpeg.exe"
                search_paths = []
                data_dir = get_data_directory()
                if data_dir:
                    search_paths.append(os.path.join(data_dir, ffmpeg_name))
                app_dir = get_script_directory()
                if app_dir:
                    search_paths.append(os.path.join(app_dir, ffmpeg_name))
                if hasattr(sys, '_MEIPASS'):
                    search_paths.append(os.path.join(sys._MEIPASS, ffmpeg_name))
                search_paths.append(os.path.join(os.getcwd(), ffmpeg_name))
                
                for ffmpeg_path in search_paths:
                    if os.path.isfile(ffmpeg_path):
                        default_ffmpeg_path = ffmpeg_path
                        print(f"[FFmpeg] Using bundled FFmpeg for default settings: {ffmpeg_path}")
                        break
            
            # Create default settings structure for Orpheus format
            default_orpheus_settings = {
                "global": {
                    "general": {
                        "download_path": "./downloads",
                        "download_quality": "hifi",
                        "disable_subscription_check": False
                    },
                    "formatting": {
                        "album_format": "{artist}/{name}",
                        "playlist_format": "{name}",
                        "track_filename_format": "{artist} - {name}",
                        "single_full_path_format": "{artist} - {name}",
                        "enable_zfill": True,
                        "force_album_format": False,
                        "truncate_length": 40
                    },
                    "codecs": {
                        "proprietary_codecs": False,
                        "spatial_codecs": True
                    },
                    "advanced": {
                        "download_mode": "ytdlp",
                        "download_youtube_videos": False,
                        "save_album_info": False,
                        "save_credits": False,
                        "embed_branding": False,
                        "lyrics_embed": False,
                        "lyrics_file": False,
                        "covers_embed": True,
                        "covers_size": 1400,
                        "covers_format": "jpg",
                        "template_folder_album": "{artist}/{name}",
                        "template_folder_compilation": "Compilations/{name}",
                        "template_file_single_disc": "{track_number}. {artist} - {name}",
                        "template_file_multi_disc": "{disc_number}-{track_number}. {artist} - {name}",
                        "template_folder_no_album": "{artist}/Unknown Album",
                        "template_file_no_album": "{artist} - {name}",
                        "template_date": "%Y-%m-%dT%H:%M:%SZ",
                        "exclude_tags": "",
                        "truncate": 40,
                        "debug_mode": False,
                        "codec_conversions": {
                            "alac": "flac",
                            "wav": "flac",
                            "vorbis": "vorbis"
                        },
                        "conversion_flags": {
                            "flac": {
                                "compression_level": 5
                            },
                            "mp3": {
                                "qscale:a": "0"
                            },
                            "aac": {
                                "audio_bitrate": "256k"
                            }
                        },
                        "conversion_keep_original": False,
                        "ffmpeg_path": default_ffmpeg_path,
                        "cover_variance_threshold": 8,
                        "disable_subscription_checks": False,
                        "enable_undesirable_conversions": False,
                        "ignore_existing_files": False,
                        "ignore_different_artists": True,
                        "hide_ffmpeg_warning": False
                    }
                },
                "modules": {
                    "deezer": {
                        "client_id": "447462",
                        "client_secret": "a83bf7f38ad2f137e444727cfc3775cf",
                        "bf_secret": "g4el58wc0zvf9na1"
                    },
                    "qobuz": {
                        "app_id": "798273057",
                        "app_secret": "abb21364945c0583309667d13ca3d93a"
                    },
                    "tidal": {
                        "tv_atmos_token": "4N3n6Q1x95LL5K7p",
                        "tv_atmos_secret": "oKOXfJW371cX6xaZ0PyhgGNBdNLlBZd4AKKYougMjik=",
                        "mobile_atmos_hires_token": "km8T1xS355y7dd3H",
                        "mobile_hires_token": "6BDSRdpK9hqEBTgU"
                    },
                    "youtube": {
                        "cookies_path": "./config/youtube-cookies.txt",
                        "download_pause_seconds": 5,
                        "download_mode": "sequential"
                    }
                }
            }
            
            with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(default_orpheus_settings, f, indent=4)
            
            print(f"Default settings file created at '{CONFIG_FILE_PATH}'")
        except Exception as e:
            error_message = f"CRITICAL ERROR: Could not create default configuration file at '{CONFIG_FILE_PATH}': {e}"
            print(error_message)
            raise FileNotFoundError(error_message)

    try:
        if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
            print(f"Directly reading settings from {CONFIG_FILE_PATH}...")
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
            file_settings = json.load(f)
        if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
            print("File read successfully.")
        if "global" in file_settings:
            orpheus_global_from_file = file_settings["global"]
            if "general" in orpheus_global_from_file:
                orpheus_general = orpheus_global_from_file["general"]
                if "general" not in settings["globals"]: settings["globals"]["general"] = {}
                if "download_path" in orpheus_general: settings["globals"]["general"]["output_path"] = orpheus_general["download_path"]
                if "download_quality" in orpheus_general: settings["globals"]["general"]["quality"] = orpheus_general["download_quality"]
                if "search_limit" in orpheus_general: settings["globals"]["general"]["search_limit"] = orpheus_general["search_limit"]
                if "concurrent_downloads" in orpheus_general: settings["globals"]["general"]["concurrent_downloads"] = orpheus_general["concurrent_downloads"]
                if "play_sound_on_finish" in orpheus_general: settings["globals"]["general"]["play_sound_on_finish"] = orpheus_general["play_sound_on_finish"]
            for section_key, section_data in orpheus_global_from_file.items():
                 if section_key != "general" and section_key in settings["globals"]:
                     if isinstance(section_data, dict) and isinstance(settings["globals"].get(section_key), dict):
                         if section_key == "advanced" and "codec_conversions" in section_data:
                             for key, value in section_data.items():
                                if key == "codec_conversions":
                                    settings["globals"][section_key][key] = copy.deepcopy(value)
                                elif key == "conversion_flags":
                                    # Special handling for conversion_flags: prevent overwriting nested dicts with strings
                                    default_flags = settings["globals"][section_key].get(key)
                                    if isinstance(default_flags, dict) and isinstance(value, dict):
                                        for sub_key, sub_val in value.items():
                                            if sub_key in default_flags and isinstance(default_flags[sub_key], dict) and not isinstance(sub_val, dict):
                                                if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                                                    print(f"Warning: Ignoring invalid conversion flag '{sub_key}': expected dict, got {type(sub_val)}")
                                                continue 
                                            
                                            if sub_key in default_flags and isinstance(default_flags[sub_key], dict) and isinstance(sub_val, dict):
                                                deep_merge(default_flags[sub_key], sub_val)
                                            else:
                                                default_flags[sub_key] = sub_val
                                    elif isinstance(default_flags, dict) and not isinstance(value, dict):
                                         pass # Ignore if trying to overwrite flags dict with non-dict
                                    else:
                                         settings["globals"][section_key][key] = copy.deepcopy(value)
                                else:
                                    # Generic protection for other keys
                                    default_val = settings["globals"][section_key].get(key)
                                    if isinstance(default_val, dict) and not isinstance(value, dict):
                                        continue

                                    if key in settings["globals"][section_key] and isinstance(settings["globals"][section_key][key], dict) and isinstance(value, dict):
                                        deep_merge(settings["globals"][section_key][key], value)
                                    else:
                                        settings["globals"][section_key][key] = copy.deepcopy(value)
                         else:
                             deep_merge(settings["globals"][section_key], section_data)
        if "modules" in file_settings:
            settings["modules"] = copy.deepcopy(file_settings["modules"])
            platform_map_from_orpheus = { "bugs": "BugsMusic", "nugs": "Nugs", "soundcloud": "SoundCloud", "tidal": "Tidal", "qobuz": "Qobuz", "deezer": "Deezer", "idagio": "Idagio", "kkbox": "KKBOX", "napster": "Napster", "beatport": "Beatport", "beatsource": "Beatsource", "musixmatch": "Musixmatch", "spotify": "Spotify", "applemusic": "AppleMusic", "youtube": "YouTube" }
            for orpheus_platform, creds_from_file in file_settings["modules"].items():
                gui_platform = platform_map_from_orpheus.get(orpheus_platform)
                if gui_platform and gui_platform in DEFAULT_SETTINGS["credentials"]:
                    platform_defaults = copy.deepcopy(DEFAULT_SETTINGS["credentials"][gui_platform])
                    deep_merge(platform_defaults, creds_from_file)
                    settings["credentials"][gui_platform] = platform_defaults
            
            # Ensure YouTube cookies path has a default if missing or empty
            if "YouTube" in settings["credentials"]:
                yt_creds = settings["credentials"]["YouTube"]
                if not yt_creds.get("cookies_path"):
                    yt_creds["cookies_path"] = "./config/youtube-cookies.txt"
        if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
            print(f"Settings loaded and mapped from {CONFIG_FILE_PATH}")

    except (json.JSONDecodeError, IOError, TypeError, KeyError) as e:
        print(f"Error loading/mapping '{CONFIG_FILE_NAME}': {e}")
        print("Using default settings ONLY for globals. Credentials will be empty.")
        settings = {
            "globals": copy.deepcopy(DEFAULT_SETTINGS["globals"]),
            "credentials": {},
            "modules": {}
        }

    # Auto-detect bundled FFmpeg if ffmpeg_path is default "ffmpeg"
    ffmpeg_path_setting = settings.get("globals", {}).get("advanced", {}).get("ffmpeg_path", "ffmpeg")
    if ffmpeg_path_setting and ffmpeg_path_setting.lower() == "ffmpeg":
        ffmpeg_name = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
        found_ffmpeg = None
        
        # Check multiple locations for ffmpeg
        search_paths = []
        
        # 1. Data directory (where we copy ffmpeg on macOS)
        data_dir = get_data_directory()
        if data_dir:
            search_paths.append(os.path.join(data_dir, ffmpeg_name))
        
        # 2. Script/app directory
        app_dir = get_script_directory()
        if app_dir:
            search_paths.append(os.path.join(app_dir, ffmpeg_name))
        
        # 3. PyInstaller bundle directory
        if hasattr(sys, '_MEIPASS'):
            search_paths.append(os.path.join(sys._MEIPASS, ffmpeg_name))
        
        # 4. Current working directory
        search_paths.append(os.path.join(os.getcwd(), ffmpeg_name))
        
        for ffmpeg_path in search_paths:
            if os.path.isfile(ffmpeg_path):
                found_ffmpeg = ffmpeg_path
                break
        
        if found_ffmpeg:
            print(f"[FFmpeg] Found bundled FFmpeg at: {found_ffmpeg}")
            if "advanced" not in settings["globals"]:
                settings["globals"]["advanced"] = {}
            settings["globals"]["advanced"]["ffmpeg_path"] = found_ffmpeg
        else:
            print(f"[FFmpeg] No bundled FFmpeg found. Searched: {search_paths}")

    current_settings = settings
    return settings

def initialize_orpheus():
    """Attempts to initialize the global Orpheus instance."""
    global orpheus_instance, app, download_button, search_button, DATA_DIR, _SCRIPT_DIR, _DATA_DIR
    
    # Lazy load modules if not already loaded
    if not ORPHEUS_AVAILABLE:
        _import_orpheus_modules()

    if not ORPHEUS_AVAILABLE:
        print("Orpheus library not available. Skipping initialization.")
        try:
            if 'app' in globals() and app and app.winfo_exists():
                app.after(100, lambda: show_centered_messagebox("Initialization Error", "Orpheus library components are missing or failed to load. Core features will be disabled.", dialog_type="error"))
            if 'download_button' in globals() and download_button and download_button.winfo_exists(): download_button.configure(state="disabled")
            if 'search_button' in globals() and search_button and search_button.winfo_exists(): search_button.configure(state="disabled")
        except Exception as gui_e: print(f"Error showing Orpheus unavailable message in GUI: {gui_e}")
        return False

    # Use _DATA_DIR for working directory (writable location)
    target_dir = _DATA_DIR if _DATA_DIR else _SCRIPT_DIR
    
    if target_dir is None:
        error_message = "FATAL ERROR: Application data path is not set. Cannot reliably initialize Orpheus. The application may be in an inconsistent state or not launched correctly."
        print(error_message)
        try:
            if 'app' in globals() and app and app.winfo_exists():
                app.after(100, lambda: show_centered_messagebox("Critical Application Error", error_message, dialog_type="error"))
        except Exception as gui_e: print(f"Error showing critical path error in GUI: {gui_e}")
        return False
    elif not os.path.isdir(target_dir):
        error_message = f"FATAL ERROR: Application data path '{target_dir}' is not a valid directory. Cannot initialize Orpheus."
        print(error_message)
        try:
            if 'app' in globals() and app and app.winfo_exists():
                app.after(100, lambda: show_centered_messagebox("Critical Application Error", error_message, dialog_type="error"))
        except Exception as gui_e: print(f"Error showing critical directory error in GUI: {gui_e}")
        return False
    original_cwd = os.getcwd()
    normalized_original_cwd = os.path.normpath(original_cwd)
    normalized_target_dir = os.path.normpath(target_dir)

    if normalized_original_cwd != normalized_target_dir:
        print(f"[Initialize Orpheus] Current CWD is '{original_cwd}'. Target data directory is '{target_dir}'. Attempting to change CWD.")
        try:
            os.chdir(target_dir)
            new_cwd = os.getcwd()
            print(f"[Initialize Orpheus] CWD successfully changed to '{new_cwd}'.")
            if os.path.normpath(new_cwd) != normalized_target_dir:
                print(f"[Initialize Orpheus] WARNING: CWD changed to '{new_cwd}', but it does not match the normalized target '{normalized_target_dir}'. This might indicate issues.")
        except Exception as e_chdir:
            error_detail = f"Type: {type(e_chdir).__name__}, Message: {e_chdir}"
            tb_str_chdir = traceback.format_exc()
            error_message_chdir = f"CRITICAL ERROR: Failed to change CWD to data directory '{target_dir}' needed for Orpheus initialization.\nError: {error_detail}\nFull Traceback:\n{tb_str_chdir}\nOrpheus will likely fail to initialize or function correctly."
            print(error_message_chdir)
            try:
                if 'app' in globals() and app and app.winfo_exists():
                    user_error_msg = f"A critical error occurred while setting up the application's working directory: {e_chdir}. The application might not work correctly. Please check logs or try restarting."
                    app.after(100, lambda: show_centered_messagebox("Critical Setup Error", user_error_msg, dialog_type="error"))
            except Exception as gui_e: print(f"Error showing CWD change critical error in GUI: {gui_e}")
            return False
    global current_settings
    ffmpeg_path_setting = current_settings.get("globals", {}).get("advanced", {}).get("ffmpeg_path", "ffmpeg").strip()
    if ffmpeg_path_setting and ffmpeg_path_setting.lower() != "ffmpeg":
        if os.path.isfile(ffmpeg_path_setting):
            ffmpeg_dir = os.path.dirname(ffmpeg_path_setting)
            if ffmpeg_dir:
                current_path = os.environ.get("PATH", "")
                if ffmpeg_dir not in current_path.split(os.pathsep):
                    os.environ["PATH"] = ffmpeg_dir + os.pathsep + current_path

    if orpheus_instance is None:
        try:
            print(f"[Orpheus Init] Initializing Orpheus engine (CWD: {os.getcwd()})...")
            
            orpheus_instance = Orpheus()
            
            print("[Orpheus Init] Orpheus engine initialized successfully.")
            return True
        except SystemExit as e:
            # Orpheus calls exit() when no modules are installed
            print("\n" + "="*60)
            print("ORPHEUS INITIALIZATION FAILED")
            print("="*60)
            print("The Orpheus engine could not start. Common causes:")
            print("  1. No download modules installed in 'modules' folder")
            print("  2. The 'modules' folder only contains 'example'")
            print("  3. Module files are missing or corrupted")
            print("")
            print("Solution: Install at least one download module")
            print("  (e.g., tidal, qobuz, deezer, spotify, etc.)")
            print("="*60 + "\n")
            try:
                if 'app' in globals() and app and app.winfo_exists():
                    app.after(100, lambda: show_centered_messagebox("Initialization Error", 
                        "No download modules are installed.\n\nPlease install at least one module in the 'modules' folder.", 
                        dialog_type="error"))
                if 'download_button' in globals() and download_button and download_button.winfo_exists():
                    download_button.configure(state="disabled")
                if 'search_button' in globals() and search_button and search_button.winfo_exists():
                    search_button.configure(state="disabled")
            except NameError: pass
            except Exception as gui_e: print(f"Error showing Orpheus init error in GUI: {gui_e}")
            return False
        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            print("\n" + "="*60)
            print("ORPHEUS INITIALIZATION FAILED")
            print("="*60)
            print(f"Error Type: {type(e).__name__}")
            print(f"Error: {e}")
            print(f"CWD: {os.getcwd()}")
            print("-"*60)
            print("Traceback:")
            print(tb_str)
            print("="*60 + "\n")
            try:
                if 'app' in globals() and app and app.winfo_exists():
                    user_error_msg_init = f"Failed to start the Orpheus download engine: {e}. Please check your settings and ensure all components are correctly placed. If the problem persists, check the console output for more details."
                    app.after(100, lambda: show_centered_messagebox("Initialization Error", user_error_msg_init, dialog_type="error"))
                if 'download_button' in globals() and download_button and download_button.winfo_exists():
                    download_button.configure(state="disabled")
                if 'search_button' in globals() and search_button and search_button.winfo_exists():
                    search_button.configure(state="disabled")
            except NameError: pass
            except Exception as gui_e: print(f"Error showing Orpheus init error in GUI: {gui_e}")
            return False
    return True

def save_settings(show_confirmation: bool = True):
    """Loads existing settings, merges UI changes, validates, maps, and saves back to settings.json.

    Args:
        show_confirmation: If True, displays a success message box.

    Returns:
        True if save was successful, False otherwise.
    """
    global settings_vars, current_settings, DEFAULT_SETTINGS, CONFIG_FILE_PATH, orpheus_instance, download_process_active
    existing_settings = {}
    try:
        if os.path.exists(CONFIG_FILE_PATH):
            with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f: existing_settings = json.load(f)
        else:
            existing_settings = { "global": {"general": {},"formatting": {},"codecs": {},"covers": {},"playlist": {},"advanced": {},"module_defaults": {},"artist_downloading": {},"lyrics": {}}, "modules": {} }
    except (json.JSONDecodeError, IOError) as e:
        error_message = f"Error loading existing settings file '{CONFIG_FILE_PATH}':\\n{type(e).__name__}: {e}. Cannot proceed with save."
        show_centered_messagebox("Settings Error", error_message, dialog_type="error")
        return False
    updated_gui_settings = {"globals": {}, "credentials": {}}
    parse_errors = []
    collected_conversion_flags = {}
    aac_var_key = "advanced.conversion_flags.aac.audio_bitrate"
    aac_var = settings_vars.get("globals", {}).get(aac_var_key)
    if isinstance(aac_var, tkinter.StringVar):
        collected_conversion_flags["aac"] = {"audio_bitrate": aac_var.get()}
    else:
        parse_errors.append(f"AAC bitrate var not found or invalid type for key '{aac_var_key}'. Using default.")
        collected_conversion_flags["aac"] = DEFAULT_SETTINGS["globals"]["advanced"]["conversion_flags"]["aac"].copy()
    flac_var_key = "advanced.conversion_flags.flac.compression_level"
    flac_var = settings_vars.get("globals", {}).get(flac_var_key)
    if isinstance(flac_var, tkinter.StringVar):
        try:
            collected_conversion_flags["flac"] = {"compression_level": int(flac_var.get())}
        except ValueError:
            parse_errors.append(f"Invalid integer for FLAC compression from var '{flac_var_key}': '{flac_var.get()}'. Using default.")
            collected_conversion_flags["flac"] = DEFAULT_SETTINGS["globals"]["advanced"]["conversion_flags"]["flac"].copy()
    else:
        parse_errors.append(f"FLAC compression var not found or invalid type for key '{flac_var_key}'. Using default.")
        collected_conversion_flags["flac"] = DEFAULT_SETTINGS["globals"]["advanced"]["conversion_flags"]["flac"].copy()
    mp3_var_key = "advanced.conversion_flags.mp3.setting"
    mp3_var = settings_vars.get("globals", {}).get(mp3_var_key)
    if isinstance(mp3_var, tkinter.StringVar):
        raw_selected_mp3_option = mp3_var.get()
        selected_mp3_option = raw_selected_mp3_option.strip()
        
        if selected_mp3_option == "MP3 VBR (Max Quality)":
            selected_mp3_option = "VBR -V0"

        if selected_mp3_option == "VBR -V0":
            collected_conversion_flags["mp3"] = {"qscale:a": "0"}
        elif selected_mp3_option.endswith("k"):
            collected_conversion_flags["mp3"] = {"audio_bitrate": selected_mp3_option}
        else:
            parse_errors.append(f"Invalid MP3 setting selected from var '{mp3_var_key}': '{raw_selected_mp3_option}'. Using default.")
            collected_conversion_flags["mp3"] = DEFAULT_SETTINGS["globals"]["advanced"]["conversion_flags"]["mp3"].copy()
    else:
        parse_errors.append(f"MP3 setting var not found or invalid type for key '{mp3_var_key}'. Using default.")
        collected_conversion_flags["mp3"] = DEFAULT_SETTINGS["globals"]["advanced"]["conversion_flags"]["mp3"].copy()
    if "globals" not in updated_gui_settings: updated_gui_settings["globals"] = {}
    if "advanced" not in updated_gui_settings["globals"]: updated_gui_settings["globals"]["advanced"] = {}
    updated_gui_settings["globals"]["advanced"]["conversion_flags"] = collected_conversion_flags
    slider_handled_conversion_flag_keys = [
        "advanced.conversion_flags.aac.audio_bitrate",
        "advanced.conversion_flags.flac.compression_level",
        "advanced.conversion_flags.mp3.setting"
    ]

    # Ensure hide_ffmpeg_warning is preserved even if the Global settings tab hasn't been opened yet
    hide_ffmpeg_key = "advanced.hide_ffmpeg_warning"
    if hide_ffmpeg_key not in settings_vars.get("globals", {}):
        current_val = current_settings.get("globals", {}).get("advanced", {}).get("hide_ffmpeg_warning")
        if current_val is not None:
            if "globals" not in settings_vars: settings_vars["globals"] = {}
            settings_vars["globals"][hide_ffmpeg_key] = tkinter.BooleanVar(value=bool(current_val))

    for key_path_str, var in settings_vars.get("globals", {}).items():
        if key_path_str in slider_handled_conversion_flag_keys:
            continue

        if key_path_str == "advanced.codec_conversions":
            if isinstance(var, dict):
                keys = key_path_str.split('.')
                temp_dict = updated_gui_settings["globals"]
                for k_idx, k_part in enumerate(keys[:-1]):
                    if k_part not in temp_dict: temp_dict[k_part] = {}
                    temp_dict = temp_dict[k_part]
                
                final_dict_key = keys[-1]
                codec_conversions_to_save = {}
                grouped_vars = {}

                for inner_key, tkinter_var_instance in var.items():
                    if not isinstance(tkinter_var_instance, tkinter.Variable):
                        continue
                    actual_value = tkinter_var_instance.get()
                    base_key = inner_key.replace('_source', '').replace('_target', '')
                    if base_key not in grouped_vars: grouped_vars[base_key] = {}

                    if inner_key.endswith('_source'):
                        grouped_vars[base_key]['source'] = actual_value
                    elif inner_key.endswith('_target'):
                        grouped_vars[base_key]['target'] = actual_value

                for base_key, pair_values in grouped_vars.items():
                    source_val = pair_values.get('source')
                    target_val = pair_values.get('target')
                    if source_val and target_val:
                        codec_conversions_to_save[source_val] = target_val
                
                temp_dict[final_dict_key] = codec_conversions_to_save
            else:
                pass
            continue
        
        if not isinstance(var, tkinter.Variable):
            continue
        raw_value = var.get(); keys = key_path_str.split('.')
        try:
            current_data = updated_gui_settings["globals"]; original_value_scope = DEFAULT_SETTINGS["globals"]; valid_default_path = True
            for i, key in enumerate(keys[:-1]):
                if key not in current_data or not isinstance(current_data.get(key), dict): current_data[key] = {}
                current_data = current_data[key]
                if isinstance(original_value_scope, dict): original_value_scope = original_value_scope.get(key)
                else: valid_default_path = False; break
            setting_key = keys[-1]; original_value = None
            if valid_default_path and isinstance(original_value_scope, dict): original_value = original_value_scope.get(setting_key)
            elif valid_default_path and not isinstance(original_value_scope, dict) and keys[-1] == setting_key: original_value = original_value_scope
            if original_value is None and key_path_str in DEFAULT_SETTINGS["globals"]: original_value = DEFAULT_SETTINGS["globals"].get(key_path_str)
            final_value = None
            if isinstance(original_value, bool): final_value = bool(raw_value)
            elif isinstance(original_value, int):
                 try: final_value = int(raw_value)
                 except (ValueError, TypeError): parse_errors.append(f"Invalid integer for '{key_path_str}': '{raw_value}'"); final_value = original_value
            elif isinstance(original_value, float):
                 try: final_value = float(raw_value)
                 except (ValueError, TypeError): parse_errors.append(f"Invalid float for '{key_path_str}': '{raw_value}'"); final_value = original_value
            elif isinstance(original_value, list):
                 try:
                     str_val = str(raw_value).strip()
                     if not str_val: final_value = []
                     else: final_value = [s.strip() for s in str_val.split(',') if s.strip()]
                 except Exception as e: parse_errors.append(f"Invalid list format for '{key_path_str}': '{raw_value}' ({e})"); final_value = original_value
            elif isinstance(original_value, dict): final_value = original_value
            elif original_value is None: final_value = str(raw_value)
            else: final_value = str(raw_value)
            current_data[setting_key] = final_value
        except Exception as e: error_msg = f"Error processing global setting '{key_path_str}': {e}"; parse_errors.append(error_msg)
    for platform_name, fields in settings_vars.get("credentials", {}).items():
         if platform_name not in updated_gui_settings["credentials"]: updated_gui_settings["credentials"][platform_name] = {}
         for field_key, var in fields.items():
              if not isinstance(var, tkinter.Variable): continue
              if field_key.startswith('_'): continue  # skip internal UI state
              updated_gui_settings["credentials"][platform_name][field_key] = str(var.get())
    if not validate_codec_conversions():
        return False

    if parse_errors:
         error_list = "\\n - ".join(parse_errors)
         show_centered_messagebox("Settings Error", f"Could not save due to invalid values:\\n - {error_list}", dialog_type="error")
         return False
    mapped_orpheus_updates = { "global": {"general": {},"formatting": {},"codecs": {},"covers": {},"playlist": {},"advanced": {},"module_defaults": {},"artist_downloading": {},"lyrics": {}}, "modules": {} }
    gui_globals = updated_gui_settings.get("globals", {})
    general_map_gui_to_orpheus = { "output_path": "download_path", "quality": "download_quality", "search_limit": "search_limit", "concurrent_downloads": "concurrent_downloads", "play_sound_on_finish": "play_sound_on_finish", "min_file_size_kb": "min_file_size_kb" }
    if "general" in gui_globals:
        gui_general_section = gui_globals["general"]
        if "general" not in mapped_orpheus_updates["global"]: mapped_orpheus_updates["global"]["general"] = {}
        for gui_key, orpheus_key in general_map_gui_to_orpheus.items():
            if gui_key in gui_general_section: mapped_orpheus_updates["global"]["general"][orpheus_key] = gui_general_section[gui_key]
    if "globals" in updated_gui_settings and "advanced" in updated_gui_settings["globals"] and "conversion_flags" in updated_gui_settings["globals"]["advanced"]:
        if "global" not in mapped_orpheus_updates: mapped_orpheus_updates["global"] = {}
        if "advanced" not in mapped_orpheus_updates["global"]: mapped_orpheus_updates["global"]["advanced"] = {}
        
        mapped_orpheus_updates["global"]["advanced"]["conversion_flags"] = copy.deepcopy(updated_gui_settings["globals"]["advanced"]["conversion_flags"])

    for section_key, section_data in gui_globals.items():
         if section_key != "general" and section_key in mapped_orpheus_updates["global"]:
             if isinstance(section_data, dict) and isinstance(mapped_orpheus_updates["global"].get(section_key), dict):
                  if section_key not in mapped_orpheus_updates["global"]: mapped_orpheus_updates["global"][section_key] = {}
                  for item_key, item_value in section_data.items():
                      if section_key == "advanced" and item_key == "conversion_flags":
                          continue
                      mapped_orpheus_updates["global"][section_key][item_key] = item_value
    platform_map_to_orpheus = { "BugsMusic": "bugs", "Nugs": "nugs", "SoundCloud": "soundcloud", "Tidal": "tidal", "Qobuz": "qobuz", "Deezer": "deezer", "Idagio": "idagio", "KKBOX": "kkbox", "Napster": "napster", "Beatport": "beatport", "Beatsource": "beatsource", "Musixmatch": "musixmatch", "Spotify": "spotify", "AppleMusic": "applemusic", "YouTube": "youtube" }
    for gui_platform, creds in updated_gui_settings.get("credentials", {}).items():
        orpheus_platform = platform_map_to_orpheus.get(gui_platform)
        if orpheus_platform:
            if orpheus_platform not in mapped_orpheus_updates["modules"]: mapped_orpheus_updates["modules"][orpheus_platform] = {}
            mapped_orpheus_updates["modules"][orpheus_platform] = creds.copy()
    # Persist creds for platforms whose tab was never opened (so use_id_token, use_arl, etc. are still written)
    for gui_platform, creds in current_settings.get("credentials", {}).items():
        orpheus_platform = platform_map_to_orpheus.get(gui_platform)
        if orpheus_platform and orpheus_platform not in mapped_orpheus_updates["modules"]:
            mapped_orpheus_updates["modules"][orpheus_platform] = copy.deepcopy(creds)

    # Preserve use_arl (Deezer) and use_id_token (Qobuz) from current_settings when the creds we're writing
    # don't already have them (e.g. auto-save before those tabs were opened, or UI vars omitted them)
    _deezer_creds = current_settings.get("credentials", {}).get("Deezer", {})
    if _deezer_creds and "deezer" in mapped_orpheus_updates["modules"]:
        if "use_arl" not in mapped_orpheus_updates["modules"]["deezer"] and "use_arl" in _deezer_creds:
            _val = _deezer_creds.get("use_arl")
            mapped_orpheus_updates["modules"]["deezer"]["use_arl"] = str(_val).lower() if _val is not None else "false"
    _qobuz_creds = current_settings.get("credentials", {}).get("Qobuz", {})
    if _qobuz_creds and "qobuz" in mapped_orpheus_updates["modules"]:
        if "use_id_token" not in mapped_orpheus_updates["modules"]["qobuz"] and "use_id_token" in _qobuz_creds:
            _val = _qobuz_creds.get("use_id_token")
            mapped_orpheus_updates["modules"]["qobuz"]["use_id_token"] = str(_val).lower() if _val is not None else "false"

    final_settings_to_save = deep_merge(existing_settings, mapped_orpheus_updates, keys_to_overwrite_if_dicts=["codec_conversions", "conversion_flags"])
    try:
        config_dir = os.path.dirname(CONFIG_FILE_PATH)
        if not os.path.exists(config_dir): os.makedirs(config_dir)
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f: json.dump(final_settings_to_save, f, indent=4, ensure_ascii=False, sort_keys=True)

        deep_merge(current_settings, updated_gui_settings, keys_to_overwrite_if_dicts=["codec_conversions", "conversion_flags"])
        if "globals" in updated_gui_settings and "advanced" in updated_gui_settings["globals"] and "conversion_flags" in updated_gui_settings["globals"]["advanced"]:
            clean_conversion_flags_from_ui = updated_gui_settings["globals"]["advanced"]["conversion_flags"]
            if "globals" not in current_settings: current_settings["globals"] = {}
            if "advanced" not in current_settings["globals"]: current_settings["globals"]["advanced"] = {}
            if "conversion_flags" not in current_settings["globals"]["advanced"]: current_settings["globals"]["advanced"]["conversion_flags"] = {}
            if "aac" in clean_conversion_flags_from_ui:
                current_settings["globals"]["advanced"]["conversion_flags"]["aac"] = clean_conversion_flags_from_ui["aac"].copy()
            if "flac" in clean_conversion_flags_from_ui:
                current_settings["globals"]["advanced"]["conversion_flags"]["flac"] = clean_conversion_flags_from_ui["flac"].copy()
            if "mp3" in clean_conversion_flags_from_ui:
                current_settings["globals"]["advanced"]["conversion_flags"]["mp3"] = clean_conversion_flags_from_ui["mp3"].copy()
        if orpheus_instance:
            try:
                orpheus_instance.settings = json.load(open(CONFIG_FILE_PATH, 'r', encoding='utf-8'))
                if hasattr(orpheus_instance, 'loaded_modules'):
                    orpheus_instance.loaded_modules.clear()
                
                if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                    print("Settings reloaded in existing Orpheus instance and module cache cleared")
            except Exception as reload_e:
                if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                    print(f"Warning: Could not reload settings in existing orpheus instance: {reload_e}")
                orpheus_instance = None
                initialize_orpheus()
        else:
            initialize_orpheus()
        if show_confirmation:
            show_centered_messagebox("Settings Saved", "Settings have been saved successfully.", dialog_type="info")

        return True

    except IOError as e:
        log_file_path = os.path.join(os.getcwd(), 'error_log.txt')
        error_message = f"Error writing settings file '{CONFIG_FILE_PATH}':\\n{type(e).__name__}: {e}"
        full_traceback = traceback.format_exc()
        try:
            with open(log_file_path, 'a', encoding='utf-8') as log_f:
                log_f.write(f"--- Error during settings save (IOError) ---\\n")
                log_f.write(f"{error_message}\\n")
                log_f.write(f"Full Traceback:\\n{full_traceback}\\n")
                log_f.write("---------------------------------------------\\n")
            error_message_for_dialog = f"{error_message}\\n\\nSee 'error_log.txt' in the application folder for details."
        except Exception as log_e:
            error_message_for_dialog = f"{error_message}\\n\\n(Failed to write details to error_log.txt)"
        show_centered_messagebox("Settings Error", error_message_for_dialog, dialog_type="error")
        return False
    except Exception as e:
        log_file_path = os.path.join(os.getcwd(), 'error_log.txt')
        error_message = f"Unexpected error saving settings:\\n{type(e).__name__}: {e}"
        full_traceback = traceback.format_exc()
        try:
            with open(log_file_path, 'a', encoding='utf-8') as log_f:
                log_f.write(f"--- Error during settings save (Exception) ---\\n")
                log_f.write(f"{error_message}\\n")
                log_f.write(f"Full Traceback:\\n{full_traceback}\\n")
                log_f.write("----------------------------------------------\\n")
            error_message_for_dialog = f"{error_message}\\n\\nSee 'error_log.txt' in the application folder for details."
        except Exception as log_e:
            error_message_for_dialog = f"{error_message}\\n\\n(Failed to write details to error_log.txt)"
        show_centered_messagebox("Settings Error", error_message_for_dialog, dialog_type="error")
        return False

def handle_save_settings():
    """Handles the save settings button click."""
    global save_status_var, save_status_label, app

    try:
        save_attempt_successful = save_settings(show_confirmation=True)
        
        # Re-run validation checks for credentials (e.g. YouTube cookies existence)
        try:
            if 'settings_vars' in globals() and 'credentials' in settings_vars:
                for platform_name, platform_vars in settings_vars['credentials'].items():
                    if '_check_cookies_func' in platform_vars and callable(platform_vars['_check_cookies_func']):
                        platform_vars['_check_cookies_func']()
        except Exception as e:
            print(f"Error running post-save validation: {e}")
        
        if 'app' in globals() and app and app.winfo_exists():
            app.after(50, _update_settings_tab_widgets)
        if save_attempt_successful:
            if 'save_status_var' in globals() and save_status_var:
                save_status_var.set("Settings saved.")
                if 'save_status_label' in globals() and save_status_label:
                    save_status_label.configure(text_color=("#00C851", "#00C851"))
            
            if 'update_search_platform_dropdown' in globals() and callable(update_search_platform_dropdown):
                app.after(100, update_search_platform_dropdown)
        else:
            if 'save_status_var' in globals() and save_status_var:
                save_status_var.set("Failed to save settings.")
                if 'save_status_label' in globals() and save_status_label:
                    save_status_label.configure(text_color=("#FF6B6B", "#FF6B6B"))

    except Exception as e:
        err_msg = f"Unexpected error during save handling:\\n{type(e).__name__}: {e}"
        if 'save_status_var' in globals() and save_status_var:
            save_status_var.set(f"Error handling save: {type(e).__name__}")
            if 'save_status_label' in globals() and save_status_label:
                save_status_label.configure(text_color=("#FF6B6B", "#FF6B6B"))
        show_centered_messagebox("Save Error", err_msg, dialog_type="error")
        import traceback
        traceback.print_exc(file=sys.__stderr__)
    finally:
        if 'app' in globals() and app and app.winfo_exists() and 'save_status_var' in globals() and save_status_var:
            app.after(4000, lambda: save_status_var.set("") if save_status_var else None)

def run_login_in_thread(orpheus, platform_name, gui_settings):
    """Target function for the login thread."""
    global output_queue, app
    is_frozen = getattr(sys, 'frozen', False)
    
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    queue_writer = QueueWriter(output_queue)
    dummy_stderr = DummyStderr()
    
    sys.stdout = queue_writer
    sys.stderr = dummy_stderr
    
    try:
        # Use auto-auth patcher for Tidal to handle TV login automatically
        if platform_name.lower() == 'tidal':
            with TidalAutoAuthPatcher(output_queue):
                module_instance = orpheus.load_module(platform_name)
        else:
            module_instance = orpheus.load_module(platform_name)
        if hasattr(module_instance, 'login'):
            if platform_name.lower() == 'beatport':
                string_io = io.StringIO()
                sys.stdout = string_io
                
                login_success = module_instance.login()
                sys.stdout = queue_writer
                
                captured_output = string_io.getvalue()
                if "Professional subscription detected" not in captured_output and captured_output:
                    output_queue.put(captured_output)
            else:
                 login_success = module_instance.login()

            if login_success:
                output_queue.put(f"{platform_name} login successful!\\n")
            else:
                output_queue.put(f"{platform_name} login failed. Check credentials or console for details.\\n")
        else:
            output_queue.put(f"The {platform_name} module does not have a login method.\\n")
            
    except Exception as e:
        output_queue.put(f"An error occurred during {platform_name} login: {e}\\n")
        if not is_frozen:
            traceback.print_exc(file=sys.__stderr__)
            
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        
        if 'app' in globals() and app.winfo_exists():
            app.after(0, lambda: _update_settings_tab_widgets())
            

def _clear_platform_session(platform_name):
    """Clear stored session for platforms that use loginstorage.bin or config/spotify. Use when switching accounts or after expired subscription.
    Next search/download will trigger fresh login with credentials from Settings."""
    from utils.utils import set_temporary_setting
    # Use data directory (e.g. ~/Library/Application Support/OrpheusDL GUI on macOS) not application_path
    data_dir = get_data_directory() or application_path
    try:
        if platform_name == "Spotify":
            spotify_dir = os.path.join(data_dir, 'config', 'spotify')
            if os.path.isdir(spotify_dir):
                if not show_centered_confirm("Confirm", "Are you sure you want to remove the Spotify session folder? This will delete all stored credentials."):
                    return
                try:
                    shutil.rmtree(spotify_dir)
                    show_centered_messagebox("Session Cleared", "Spotify stored session folder has been removed.\n\nNext search or download will log in with your credentials from above.", dialog_type="info")
                except OSError as e:
                    show_centered_messagebox("Error", f"Could not remove Spotify folder: {e}", dialog_type="error")
            else:
                show_centered_messagebox("No Session", "No stored Spotify credentials found. You can search or download to log in.", dialog_type="info")
            return
        if platform_name == "YouTube":
            cookies_path = (current_settings.get("credentials") or {}).get("YouTube", {}).get("cookies_path", "") or "./config/youtube-cookies.txt"
            if not os.path.isabs(cookies_path):
                cookies_path = os.path.normpath(os.path.join(data_dir, cookies_path.replace("./", "").replace(".\\", "")))
            else:
                cookies_path = os.path.normpath(cookies_path)
            if not os.path.isfile(cookies_path):
                show_centered_messagebox("No Session", "No youtube-cookies.txt found. You can export cookies to log in.", dialog_type="info")
                return
            if not show_centered_confirm("Confirm", "Are you sure you want to delete youtube-cookies.txt?"):
                return
            try:
                os.remove(cookies_path)
                show_centered_messagebox("Session Cleared", "youtube-cookies.txt has been deleted.\n\nNext search or download will require exporting cookies again.", dialog_type="info")
            except OSError as e:
                show_centered_messagebox("Error", f"Could not delete file: {e}", dialog_type="error")
            return
        if platform_name == "AppleMusic":
            cookies_path = (current_settings.get("credentials") or {}).get("AppleMusic", {}).get("cookies_path", "") or "./config/cookies.txt"
            if not os.path.isabs(cookies_path):
                cookies_path = os.path.normpath(os.path.join(data_dir, cookies_path.replace("./", "").replace(".\\", "")))
            else:
                cookies_path = os.path.normpath(cookies_path)
            if not os.path.isfile(cookies_path):
                show_centered_messagebox("No Session", "No cookies.txt found. You can export cookies to log in.", dialog_type="info")
                return
            if not show_centered_confirm("Confirm", "Are you sure you want to delete cookies.txt?"):
                return
            try:
                os.remove(cookies_path)
                show_centered_messagebox("Session Cleared", "cookies.txt has been deleted.\n\nNext search or download will require exporting cookies again.", dialog_type="info")
            except OSError as e:
                show_centered_messagebox("Error", f"Could not delete file: {e}", dialog_type="error")
            return
        if platform_name == "SoundCloud":
            if not show_centered_confirm("Confirm", "Are you sure you want to clear the SoundCloud token?"):
                return
            try:
                if "credentials" not in current_settings:
                    current_settings["credentials"] = {}
                if "SoundCloud" not in current_settings["credentials"]:
                    current_settings["credentials"]["SoundCloud"] = {}
                current_settings["credentials"]["SoundCloud"]["web_access_token"] = ""
                if "settings_vars" in globals() and settings_vars.get("credentials", {}).get("SoundCloud", {}).get("web_access_token"):
                    settings_vars["credentials"]["SoundCloud"]["web_access_token"].set("")
                save_settings(show_confirmation=False)
                show_centered_messagebox("Session Cleared", "SoundCloud token has been cleared.\n\nPaste a new token above to use a different account or refresh your session.", dialog_type="info")
            except Exception as e:
                show_centered_messagebox("Error", f"Could not clear token: {e}", dialog_type="error")
            return
        storage_path = os.path.join(data_dir, 'config', 'loginstorage.bin')
        module_key = platform_name.lower()
        if not os.path.isfile(storage_path):
            show_centered_messagebox("No Session", f"No stored session found for {platform_name}. You can search or download to log in.", dialog_type="info")
            return
        if platform_name in ("Beatport", "Beatsource"):
            set_temporary_setting(storage_path, module_key, 'custom_data', 'access_token', None)
            set_temporary_setting(storage_path, module_key, 'custom_data', 'refresh_token', None)
            set_temporary_setting(storage_path, module_key, 'custom_data', 'expires', None)
        elif platform_name == "Tidal":
            set_temporary_setting(storage_path, module_key, 'custom_data', 'sessions', {})
        elif platform_name == "Qobuz":
            set_temporary_setting(storage_path, module_key, 'custom_data', 'token', None)
        elif platform_name == "Deezer":
            set_temporary_setting(storage_path, module_key, 'custom_data', 'arl', None)
        if platform_name == "Tidal":
            show_centered_messagebox("Session Cleared", "Tidal stored session has been cleared.\n\nNext search or download will open a browser window where you can log in with your Tidal account to link device.", dialog_type="info")
        else:
            show_centered_messagebox("Session Cleared", f"{platform_name} stored session has been cleared.\n\nNext search or download will log in with your credentials from above.", dialog_type="info")
    except Exception as e:
        if "Module does not use" in str(e) or "does not exist" in str(e).lower():
            show_centered_messagebox("No Session", f"No stored session found for {platform_name}. You can search or download to log in.", dialog_type="info")
        else:
            show_centered_messagebox("Error", f"Could not clear session: {e}", dialog_type="error")

def _add_clear_session_icon(parent_frame, platform_name):
    """Add a trashcan 🗑 (clear session) button in bottom-right corner of parent_frame. Click clears stored session for platform."""
    _font_size = 10 if platform.system() == "Darwin" else 13
    clear_btn = customtkinter.CTkButton(
        parent_frame,
        text="🗑",
        width=24,
        height=24,
        font=("Segoe UI", _font_size),
        fg_color=BUTTON_COLOR if 'BUTTON_COLOR' in globals() else ("#E0E0E0", "#303030"),
        hover_color="#E53935",
        command=lambda p=platform_name: _clear_platform_session(p),
    )
    clear_btn.place(relx=1.0, rely=1.0, anchor="se", x=-15, y=-15)
    btn_bg = globals().get("BUTTON_COLOR", ("#E0E0E0", "#343638"))
    tooltip_bg = btn_bg[1] if isinstance(btn_bg, (tuple, list)) else btn_bg
    CTkToolTip(clear_btn, message="Clear stored session\n(use after switching accounts or expired subscription)", bg_color=tooltip_bg, text_color="#dddddd", x_offset=-162, y_offset=-55)

def start_login_thread(platform_name):
    """Starts the login process in a separate thread."""
    global orpheus_instance, current_settings, app
    
    if orpheus_instance:
        login_thread = threading.Thread(target=run_login_in_thread, args=(orpheus_instance, platform_name, current_settings), daemon=True)
        login_thread.start()
    else:
        if not getattr(sys, 'frozen', False):
            print(f"Orpheus instance not ready, cannot start login for {platform_name}")
            
def _auto_save_path_change(*args):
    """Callback triggered when path_var_main changes. Updates in-memory setting AND saves to file."""
    global current_settings, path_var_main, settings_vars, save_status_var, app
    try:
        if 'path_var_main' not in globals() or not path_var_main: return

        new_path = path_var_main.get()
        if not new_path:
            return

        current_path_in_memory = current_settings.get("globals", {}).get("general", {}).get("output_path")
        settings_tab_var = settings_vars.get("globals", {}).get("general.output_path")
        current_path_in_settings_tab = settings_tab_var.get() if settings_tab_var else None
        should_save = False
        if new_path != current_path_in_memory:
            should_save = True
        elif settings_tab_var and new_path != current_path_in_settings_tab:
            should_save = True
        elif not settings_tab_var:
            should_save = True 

        if should_save:
            if "globals" not in current_settings: current_settings["globals"] = {}
            if "general" not in current_settings["globals"]: current_settings["globals"]["general"] = {}
            current_settings["globals"]["general"]["output_path"] = new_path
            if settings_tab_var:
                settings_tab_var.set(new_path)
            save_successful = save_settings(show_confirmation=False)
            if 'save_status_var' in globals() and save_status_var:
                status_msg = "Path saved." if save_successful else "Auto-save failed!"
                save_status_var.set(status_msg)
                if 'app' in globals() and app and app.winfo_exists():
                    app.after(3000, lambda var=save_status_var, msg=status_msg: var.set("") if var and var.get() == msg else None)
    except Exception as e:
        log_file_path = os.path.join(os.getcwd(), 'error_log.txt')
        err_msg = f"Error during automatic path save handling:\\n{type(e).__name__}: {e}"
        full_traceback = traceback.format_exc()

        try:
            with open(log_file_path, 'a', encoding='utf-8') as log_f:
                log_f.write(f"--- Error during _auto_save_path_change ---\\n")
                log_f.write(f"{err_msg}\\n")
                log_f.write(f"Full Traceback:\\n{full_traceback}\\n")
                log_f.write("---------------------------------------------\\n")
            error_message_for_dialog = f"{err_msg}\\n\\nSee 'error_log.txt' in the application folder for details."
        except Exception as log_e:
            error_message_for_dialog = f"{err_msg}\\n\\n(Failed to write details to error_log.txt)"
        if 'save_status_var' in globals() and save_status_var:
            save_status_var.set("Error during auto-save!")
            if 'app' in globals() and app and app.winfo_exists():
                 app.after(4000, lambda var=save_status_var: var.set("") if var else None)
        dialog_title = "Initialization Error" if "Initialization" in str(e) else "Auto-Save Error"
        show_centered_messagebox(dialog_title, error_message_for_dialog, dialog_type="error")

def handle_focus_in(widget):
    try:
        if not hasattr(widget, '_original_fg_color_stored'):
            original_color = widget.cget("fg_color")
            widget._original_fg_color_stored = original_color
        widget.configure(fg_color="#2B2B2B")
    except Exception as e:
        print(f"Error in handle_focus_in for {widget}: {e}")

def handle_focus_out(widget):
    try:
        if hasattr(widget, '_original_fg_color_stored'):
            original_color = widget._original_fg_color_stored
            widget.configure(fg_color=original_color)
    except Exception as e:
        print(f"Error in handle_focus_out for {widget}: {e}")


def _masked_entry_focus_in(widget):
    """Unmask a password/secret entry on focus, then run normal focus-in handling."""
    try:
        widget.configure(show="")
    except Exception:
        pass
    handle_focus_in(widget)


def _masked_entry_focus_out(widget):
    """Re-mask a password/secret entry on blur, then run normal focus-out handling."""
    try:
        widget.configure(show="*")
    except Exception:
        pass
    handle_focus_out(widget)


def show_centered_messagebox(title, message, dialog_type="info", parent=None):
    """Creates and displays a centered CTkToplevel message box."""
    global app
    if parent is None:
        parent = app if 'app' in globals() and app else None
        if parent is None:
             print("ERROR: Cannot show messagebox, main app window not available.")
             return

    dialog = customtkinter.CTkToplevel(parent); dialog.title(title); dialog.geometry("450x150"); dialog.resizable(False, False); dialog.attributes("-topmost", True); dialog.transient(parent)
    dialog.update_idletasks()
    
    # NOTE: CTkToplevel does not support icon setting - this is a known CustomTkinter limitation.
    # The icon setting code below is kept for potential future CustomTkinter updates, but currently
    # dialogs will show the default icon. The main window icon works correctly.
    # 
    # If icon support is critical, consider using regular tkinter.Toplevel with CustomTkinter styling,
    # or wait for CustomTkinter to add icon support for CTkToplevel.
    #
    # Attempt to set icon (may not work due to CTkToplevel limitations):
    try:
        if platform.system() != "Darwin":
            # Try ICO first on Windows
            ico_path = resource_path("icon.ico")
            if ico_path and os.path.exists(ico_path):
                icon_path_str = str(os.path.abspath(ico_path))
                try:
                    # Method 1: Direct tk.call (most likely to work if any method does)
                    dialog.tk.call('wm', 'iconbitmap', dialog._w, icon_path_str)
                except Exception:
                    try:
                        # Method 2: iconbitmap method
                        dialog.iconbitmap(icon_path_str)
                    except Exception:
                        # Method 3: Try PNG with PhotoImage
                        png_path = resource_path("icon.png")
                        if png_path and os.path.exists(png_path):
                            from tkinter import PhotoImage
                            icon_image = PhotoImage(file=str(os.path.abspath(png_path)))
                            dialog.iconphoto(True, icon_image)
                            if not hasattr(dialog, '_icon_ref'):
                                dialog._icon_ref = icon_image
    except Exception:
        pass
    
    parent_width = parent.winfo_width(); parent_height = parent.winfo_height(); parent_x = parent.winfo_x(); parent_y = parent.winfo_y(); dialog_width = dialog.winfo_width(); dialog_height = dialog.winfo_height()
    center_x = parent_x + (parent_width // 2) - (dialog_width // 2); center_y = parent_y + (parent_height // 2) - (dialog_height // 2); dialog.geometry(f"+{center_x}+{center_y}")
    message_label = customtkinter.CTkLabel(dialog, text=message, wraplength=400, justify="left"); message_label.pack(pady=(20, 10), padx=20, expand=True, fill="both")
    ok_button = customtkinter.CTkButton(dialog, text="OK", command=dialog.destroy, width=100); ok_button.pack(pady=(0, 20)); ok_button.focus_set(); dialog.bind("<Return>", lambda event: ok_button.invoke())
    dialog.grab_set(); dialog.wait_window()

def show_centered_confirm(title, message, parent=None):
    """Creates and displays a centered CTkToplevel confirmation dialog with Yes/No. Returns True if Yes, False if No."""
    global app
    if parent is None:
        parent = app if 'app' in globals() and app else None
        if parent is None:
            print("ERROR: Cannot show confirm dialog, main app window not available.")
            return False
    result = [False]  # Use list to allow closure to mutate
    def on_yes():
        result[0] = True
        dialog.destroy()
    def on_no():
        result[0] = False
        dialog.destroy()
    dialog = customtkinter.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("450x150")
    dialog.resizable(False, False)
    dialog.attributes("-topmost", True)
    dialog.transient(parent)
    dialog.update_idletasks()
    try:
        if platform.system() != "Darwin":
            ico_path = resource_path("icon.ico")
            if ico_path and os.path.exists(ico_path):
                icon_path_str = str(os.path.abspath(ico_path))
                try:
                    dialog.tk.call('wm', 'iconbitmap', dialog._w, icon_path_str)
                except Exception:
                    try:
                        dialog.iconbitmap(icon_path_str)
                    except Exception:
                        png_path = resource_path("icon.png")
                        if png_path and os.path.exists(png_path):
                            from tkinter import PhotoImage
                            icon_image = PhotoImage(file=str(os.path.abspath(png_path)))
                            dialog.iconphoto(True, icon_image)
                            if not hasattr(dialog, '_icon_ref'):
                                dialog._icon_ref = icon_image
    except Exception:
        pass
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()
    parent_x = parent.winfo_x()
    parent_y = parent.winfo_y()
    dialog_width = dialog.winfo_width()
    dialog_height = dialog.winfo_height()
    center_x = parent_x + (parent_width // 2) - (dialog_width // 2)
    center_y = parent_y + (parent_height // 2) - (dialog_height // 2)
    dialog.geometry(f"+{center_x}+{center_y}")
    message_label = customtkinter.CTkLabel(dialog, text=message, wraplength=400, justify="left")
    message_label.pack(pady=(20, 10), padx=20, expand=True, fill="both")
    btn_frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(pady=(0, 20))
    yes_btn = customtkinter.CTkButton(btn_frame, text="Yes", command=on_yes, width=100, fg_color="#343638", hover_color="#1F6AA5")
    yes_btn.pack(side="left", padx=(0, 10))
    no_btn = customtkinter.CTkButton(btn_frame, text="No", command=on_no, width=100, fg_color="#343638", hover_color="#1F6AA5")
    no_btn.pack(side="left")
    yes_btn.focus_set()
    dialog.bind("<Return>", lambda e: on_yes())
    dialog.bind("<Escape>", lambda e: on_no())
    dialog.grab_set()
    dialog.wait_window()
    return result[0]

def show_log_viewer(title="Application Logs", parent=None):
    """Display captured logs in a scrollable dialog for debugging."""
    global app, _log_capture
    if parent is None:
        parent = app if 'app' in globals() and app else None
        if parent is None:
            print("ERROR: Cannot show log viewer, main app window not available.")
            return
    
    dialog = customtkinter.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("800x500")
    dialog.resizable(True, True)
    dialog.attributes("-topmost", True)
    dialog.transient(parent)
    dialog.update_idletasks()
    
    # Center on parent
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()
    parent_x = parent.winfo_x()
    parent_y = parent.winfo_y()
    dialog_width = 800
    dialog_height = 500
    center_x = parent_x + (parent_width // 2) - (dialog_width // 2)
    center_y = parent_y + (parent_height // 2) - (dialog_height // 2)
    dialog.geometry(f"{dialog_width}x{dialog_height}+{center_x}+{center_y}")
    
    # Header
    header_label = customtkinter.CTkLabel(
        dialog, 
        text="Console output captured during startup.\nThis can help diagnose initialization errors.",
        justify="left"
    )
    header_label.pack(pady=(10, 5), padx=10, anchor="w")
    
    # Log text area with scrollbar
    text_frame = customtkinter.CTkFrame(dialog)
    text_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    log_text = customtkinter.CTkTextbox(
        text_frame, 
        width=HELP_CONTENT_WIDTH, 
        height=380,
        font=("Segoe UI", 11),
        wrap="word"
    )
    log_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    # Get logs
    logs = _log_capture.get_logs() if _log_capture else "No logs captured."
    if not logs.strip():
        logs = "No logs were captured during startup."
    
    log_text.insert("1.0", logs)
    log_text.configure(state="disabled")  # Make read-only
    
    # Button frame
    button_frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
    button_frame.pack(fill="x", padx=10, pady=10)
    
    def copy_logs():
        dialog.clipboard_clear()
        dialog.clipboard_append(logs)
        copy_btn.configure(text="Copied!")
        dialog.after(1500, lambda: copy_btn.configure(text="Copy to Clipboard"))
    
    def save_logs():
        filepath = tkinter.filedialog.asksaveasfilename(
            parent=dialog,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="orpheusdl_gui_logs.txt"
        )
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(logs)
                show_centered_messagebox("Saved", f"Logs saved to:\n{filepath}", dialog_type="info", parent=dialog)
            except Exception as e:
                show_centered_messagebox("Error", f"Failed to save logs:\n{e}", dialog_type="error", parent=dialog)
    
    copy_btn = customtkinter.CTkButton(button_frame, text="Copy to Clipboard", command=copy_logs, width=140)
    copy_btn.pack(side="left", padx=5)
    
    save_btn = customtkinter.CTkButton(button_frame, text="Save to File", command=save_logs, width=120)
    save_btn.pack(side="left", padx=5)
    
    close_btn = customtkinter.CTkButton(button_frame, text="Close", command=dialog.destroy, width=100)
    close_btn.pack(side="right", padx=5)
    
    dialog.grab_set()

def _create_menu():
    global _context_menu, app, BUTTON_COLOR
    if _context_menu and _context_menu.winfo_exists(): return
    if 'app' not in globals() or not app: return
    # Match tooltip/menu background for consistency; border matches separator color (#2B2B2B)
    _context_menu = customtkinter.CTkFrame(app, border_width=1, border_color="#565B5E", fg_color=TOOLTIP_MENU_BG, width=CONTEXT_MENU_WIDTH)
    button_color = TOOLTIP_MENU_BG

    # Undo button (icon color = text color; disabled icon = disabled text color)
    undo_icon = _create_undo_icon(color=CONTEXT_MENU_TEXT_COLOR)
    undo_icon_disabled = _create_undo_icon(color=CONTEXT_MENU_TEXT_DISABLED)
    undo_button = customtkinter.CTkButton(
        _context_menu, 
        text="Undo", 
        image=undo_icon,
        compound="left",
        command=_undo_text, 
        width=100, 
        height=24, 
        font=("Segoe UI", 11),
        fg_color=button_color, 
        hover_color="#1F6AA5", 
        text_color=CONTEXT_MENU_TEXT_COLOR,
        text_color_disabled=CONTEXT_MENU_TEXT_DISABLED, 
        border_width=0,
        anchor="w"
    )
    undo_button.image = undo_icon
    undo_button.disabled_image = undo_icon_disabled
    undo_button.pack(pady=(2, 1), padx=2, fill="x")
    
    # Separator line (slightly lighter than menu bg so it's visible)
    separator = customtkinter.CTkFrame(_context_menu, width=50, height=2, fg_color="#2B2B2B")
    separator.pack(fill="x", padx=2, pady=2)
    
    # Copy button
    copy_icon = _create_copy_icon(color=CONTEXT_MENU_TEXT_COLOR)
    copy_icon_disabled = _create_copy_icon(color=CONTEXT_MENU_TEXT_DISABLED)
    copy_button = customtkinter.CTkButton(
        _context_menu, 
        text="Copy", 
        image=copy_icon,
        compound="left",
        command=copy_text, 
        width=100, 
        height=24, 
        font=("Segoe UI", 11),
        fg_color=button_color, 
        hover_color="#1F6AA5", 
        text_color=CONTEXT_MENU_TEXT_COLOR,
        text_color_disabled=CONTEXT_MENU_TEXT_DISABLED, 
        border_width=0,
        anchor="w"
    )
    copy_button.image = copy_icon
    copy_button.disabled_image = copy_icon_disabled
    copy_button.pack(pady=1, padx=2, fill="x")
    
    # Paste button
    paste_icon = _create_paste_icon(color=CONTEXT_MENU_TEXT_COLOR)
    paste_icon_disabled = _create_paste_icon(color=CONTEXT_MENU_TEXT_DISABLED)
    paste_button = customtkinter.CTkButton(
        _context_menu, 
        text="Paste", 
        image=paste_icon,
        compound="left",
        command=paste_text, 
        width=100, 
        height=24, 
        font=("Segoe UI", 11),
        fg_color=button_color, 
        hover_color="#1F6AA5", 
        text_color=CONTEXT_MENU_TEXT_COLOR,
        text_color_disabled=CONTEXT_MENU_TEXT_DISABLED, 
        border_width=0,
        anchor="w"
    )
    paste_button.image = paste_icon
    paste_button.disabled_image = paste_icon_disabled
    paste_button.pack(pady=(1, 2), padx=2, fill="x")
    
    _context_menu.pack_forget()

def show_context_menu(event):
    global _context_menu, _target_widget, _hide_menu_binding_id, app
    _create_menu();
    if not _context_menu: print("Context menu: Failed to create menu frame."); return
    hide_context_menu()
    if 'app' not in globals() or not app: return
    x_root, y_root = app.winfo_pointerxy()
    try: target_at_coords = app.winfo_containing(x_root, y_root);
    except Exception as e: print(f"Context menu: Error finding widget at coords: {e}"); return
    if not target_at_coords: return
    intended_ctk_widget = None; temp_widget = target_at_coords; max_levels = 10; current_level = 0
    while temp_widget and temp_widget != app and current_level < max_levels:
        if isinstance(temp_widget, customtkinter.CTkEntry): intended_ctk_widget = temp_widget; break
        try: temp_widget = temp_widget.master
        except AttributeError: break
        current_level += 1
    if not intended_ctk_widget: return
    _target_widget = intended_ctk_widget
    
    # Initialize undo tracking for this widget if not already present
    if _target_widget not in _undo_stacks:
        _undo_stacks[_target_widget] = []
        # Bind key events to track changes for undo
        def on_key(event):
            if event.keysym not in ("Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R"):
                _push_undo(_target_widget)
        _target_widget.bind("<KeyRelease>", on_key, add=True)
    
    can_copy = False; can_paste = False; has_selection = False; clipboard_has_text = False; can_undo = False
    clipboard_content = ""
    try: clipboard_content = app.clipboard_get();
    except tkinter.TclError: pass
    except Exception as e: print(f"Context menu: Error checking clipboard - {e}")
    if isinstance(clipboard_content, str) and clipboard_content: clipboard_has_text = True
    try:
        try:
            if _target_widget._entry.selection_present(): has_selection = True
        except (tkinter.TclError, AttributeError): has_selection = False
        can_copy = has_selection or bool(_target_widget.get())
        state = _target_widget.cget("state") if hasattr(_target_widget, 'cget') else 'disabled'
        can_paste = state == "normal" and clipboard_has_text
        
        # Check if undo is possible
        current_text = _target_widget.get()
        can_undo = state == "normal" and _target_widget in _undo_stacks and (
            len(_undo_stacks[_target_widget]) > 1 or 
            (len(_undo_stacks[_target_widget]) == 1 and _undo_stacks[_target_widget][0] != current_text)
        )
    except Exception as e: print(f"Context menu: Error checking widget state/content: {e}")
    try:
        children = _context_menu.winfo_children()
        # Find buttons among children (skip separator)
        buttons = [c for c in children if isinstance(c, customtkinter.CTkButton)]
        if len(buttons) >= 3:
            undo_btn = buttons[0]; copy_btn = buttons[1]; paste_btn = buttons[2]
            undo_btn.configure(state="normal" if can_undo else "disabled")
            undo_btn.configure(image=undo_btn.image if can_undo else getattr(undo_btn, "disabled_image", undo_btn.image))
            copy_btn.configure(state="normal" if can_copy else "disabled")
            copy_btn.configure(image=copy_btn.image if can_copy else getattr(copy_btn, "disabled_image", copy_btn.image))
            paste_btn.configure(state="normal" if can_paste else "disabled")
            paste_btn.configure(image=paste_btn.image if can_paste else getattr(paste_btn, "disabled_image", paste_btn.image))
        else: print("Context menu: Button widgets not found or invalid."); return
        menu_x = (x_root - app.winfo_rootx()) / app._get_window_scaling() + 2
        menu_y = (y_root - app.winfo_rooty()) / app._get_window_scaling() + 2
        _context_menu.place(x=menu_x, y=menu_y); _context_menu.lift()
        if _hide_menu_binding_id is None: _hide_menu_binding_id = app.bind("<Button-1>", hide_context_menu, add=True)
    except tkinter.TclError as e: print(f"Context menu: TclError configuring/placing menu: {e}")
    except Exception as e: print(f"Context menu: Error configuring/placing menu: {e}")

def hide_context_menu(event=None):
    global _context_menu, _target_widget, _hide_menu_binding_id, app
    if 'app' not in globals() or not app: return
    if event and _context_menu and _context_menu.winfo_exists():
         x_root, y_root = app.winfo_pointerxy()
         try: click_widget = app.winfo_containing(x_root, y_root);
         except tkinter.TclError: pass
         except Exception as e: print(f"Error checking click location in hide_context_menu: {e}")
         else:
             if click_widget == _context_menu or click_widget in _context_menu.winfo_children(): return
    if _context_menu and _context_menu.winfo_exists(): _context_menu.place_forget()
    if _hide_menu_binding_id:
         try: app.unbind("<Button-1>", _hide_menu_binding_id)
         except tkinter.TclError: pass
         except Exception as e: print(f"Error unbinding hide_context_menu: {e}")
         finally: _hide_menu_binding_id = None
    _target_widget = None

def _copy_to_system_clipboard(text):
    """
    Copy text to system clipboard in a persistent way.
    Unlike Tkinter's clipboard, this persists after the app closes.
    """
    if not text:
        return False
    
    try:
        if platform.system() == "Windows":
            # Use PowerShell's Set-Clipboard for persistent copy
            # This survives after the application closes
            process = subprocess.Popen(
                ['powershell', '-command', 'Set-Clipboard', '-Value', text],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            process.communicate(timeout=2)
            return process.returncode == 0
        elif platform.system() == "Darwin":  # macOS
            process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            process.communicate(text.encode('utf-8'), timeout=2)
            return process.returncode == 0
        else:  # Linux
            # Try xclip first, then xsel
            for cmd in [['xclip', '-selection', 'clipboard'], ['xsel', '--clipboard', '--input']]:
                try:
                    process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                    process.communicate(text.encode('utf-8'), timeout=2)
                    if process.returncode == 0:
                        return True
                except FileNotFoundError:
                    continue
            return False
    except Exception as e:
        print(f"System clipboard copy failed: {e}")
        return False

def _handle_ctrl_c_copy(event):
    """
    Handler for Ctrl+C that uses persistent system clipboard.
    Bound to entry widgets to ensure clipboard survives app close.
    """
    try:
        widget = event.widget
        # Get the underlying Tk entry widget if it's a CTkEntry
        tk_widget = widget._entry if hasattr(widget, '_entry') else widget
        
        # Get selected text
        text_to_copy = ""
        try:
            if tk_widget.selection_present():
                text_to_copy = tk_widget.selection_get()
        except tkinter.TclError:
            pass
        
        if text_to_copy:
            _copy_to_system_clipboard(text_to_copy)
            # Don't prevent default - let Tkinter also handle it for immediate use
    except Exception as e:
        pass  # Silently fail, let default Ctrl+C behavior continue
    
    # Return None to allow default binding to also execute
    return None

def copy_text():
    global _target_widget, app
    if not isinstance(_target_widget, customtkinter.CTkEntry): hide_context_menu(); return
    if 'app' not in globals() or not app: return
    text_to_copy = ""
    try:
        try: text_to_copy = _target_widget._entry.selection_get()
        except tkinter.TclError: text_to_copy = _target_widget.get()
        if text_to_copy:
            # Try persistent system clipboard first
            if not _copy_to_system_clipboard(text_to_copy):
                # Fall back to Tkinter clipboard if system clipboard fails
                app.clipboard_clear(); app.clipboard_append(text_to_copy); app.update()
    except tkinter.TclError as e: print(f"TclError during copy: {e}")
    except Exception as e: print(f"Error copying text: {e}")
    finally: hide_context_menu()

def paste_text():
    global _target_widget, app
    if not isinstance(_target_widget, customtkinter.CTkEntry): hide_context_menu(); return
    if 'app' not in globals() or not app: return
    try:
        state = 'disabled'
        try:
            if hasattr(_target_widget, 'cget') and callable(_target_widget.cget): state = _target_widget.cget("state")
        except Exception as e: print(f"Could not get widget state for paste check: {e}")
        if state != "normal": hide_context_menu(); return
        
        # Push current state to undo before pasting
        _push_undo(_target_widget)
        
        clipboard_text = app.clipboard_get(); tk_widget = _target_widget._entry
        try:
            if tk_widget.selection_present(): tk_widget.delete(tkinter.SEL_FIRST, tkinter.SEL_LAST)
        except tkinter.TclError: pass
        tk_widget.insert(tkinter.INSERT, clipboard_text)
    except tkinter.TclError as e:
        if "CLIPBOARD selection doesn't exist" not in str(e): print(f"TclError during paste: {e}")
    except Exception as e: print(f"Error pasting text: {e}", exc_info=True)
    finally: hide_context_menu()

def _clean_ansi_and_process_markers(text):
    """Clean ANSI color codes and process custom markers for GUI display"""
    import re
    platform_patterns = {
        r'Platform: \033\[96m(TIDAL)\033\[0m': 'tidal',
        r'Platform: \033\[91m(Apple Music)\033\[0m': 'apple music',
        r'Platform: \033\[92m(Beatport)\033\[0m': 'beatport',
        r'Platform: \033\[94m(Beatsource)\033\[0m': 'beatsource',
        r'Platform: \033\[94m(Napster)\033\[0m': 'napster',
        r'Platform: \033\[38;5;129m(Deezer)\033\[0m': 'deezer',
        r'Platform: \033\[34m(Qobuz)\033\[0m': 'qobuz',
        r'Platform: \033\[38;5;208m(SoundCloud)\033\[0m': 'soundcloud',
        r'Platform: \033\[32m(Spotify)\033\[0m': 'spotify',
        r'Platform: \033\[36m(KKBOX)\033\[0m': 'kkbox',
        r'Platform: \033\[35m(Idagio)\033\[0m': 'idagio',
        r'Platform: \033\[31m(Bugs)\033\[0m': 'bugs',
        r'Platform: \033\[31m(Nugs)\033\[0m': 'nugs',
    }
    for platform_pattern, platform_name in platform_patterns.items():
        display_name = SERVICE_DISPLAY_NAMES.get(platform_name, platform_name)
        text = re.sub(platform_pattern, rf'Platform: |PLATFORM_{platform_name.upper().replace(" ", "_")}|{display_name}|RESET|', text)
    
    gray_pattern = r'\033\[90m(.*?)\033\[0m'
    text = re.sub(gray_pattern, r'|GRAY|\1|RESET|', text)
    text = re.sub(r'(\d+/\d+\s+)(?:\033\[[0-9;]*m)?\+(?:\033\[[0-9;]*m)?(\s+)', r'\1✓\2', text)
    text = re.sub(r'(\d+/\d+\s+)(?:\033\[[0-9;]*m)?>(?:\033\[[0-9;]*m)?(\s+)', r'\1▶\2', text)
    text = re.sub(r'(\d+/\d+\s+)(\033\[91m)[xX](\033\[0m)(\s+)', r'\1❌\4', text)
    text = re.sub(r'(\033\[91m)X(\033\[0m)', r'❌', text)
    if '|ERROR_SYMBOL_SINGLE|' not in text:
        text = text.replace('✗', '|ERROR_SYMBOL_SINGLE|✗|ERROR_SYMBOL_END|')
    text = re.sub(r'❌([^|]*?)(\|GRAY\|[^|]*?\|RESET\|)', r'|ERROR_SYMBOL_SINGLE|✗|ERROR_SYMBOL_END|\1\2', text)
    text = text.replace('❌', '|ERROR_SYMBOL_SINGLE|✗|ERROR_SYMBOL_END|')
    
    # Colorize specific status text
    text = text.replace('(already exists)', '|YELLOW|(already exists)|RESET|')
    text = text.replace('(failed)', '|RED|(failed)|RESET|')



    yellow_pattern = r'\033\[33m(.*?)\033\[0m'
    def yellow_replacer(match):
        content = match.group(1)
        # If content already has our custom tags, don't wrap it again
        if "|YELLOW|" in content or "|RED|" in content or "|GRAY|" in content:
             return content
        if "Track skipped" in content or "▶" in content or content.strip() == ">":
            return content
        return f'|YELLOW|{content}|RESET|'
    
    text = re.sub(yellow_pattern, yellow_replacer, text)
    
    red_pattern = r'\033\[91m(.*?)\033\[0m'
    def red_replacer(match):
        content = match.group(1)
        # If content already has our custom tags, don't wrap it again
        if "|YELLOW|" in content or "|RED|" in content or "|GRAY|" in content:
             return content
        return f'|RED|{content}|RESET|'
        
    text = re.sub(red_pattern, red_replacer, text)
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)
    
    return text

def _insert_text_with_links_and_platforms(text_content, error):
    """Helper function to insert text with URL and platform styling"""
    try:
        # Clean up any leftover color markers that weren't consumed by regex
        text_content = text_content.replace('|RESET|', '')
        text_content = re.sub(r'\|(RED|YELLOW|GRAY)\|', '', text_content)
        
        url_regex = r'https?://\S+|www\.\S+'
        service_names = '|'.join(re.escape(s) for s in SERVICE_COLORS.keys())
        service_regex = f'Platform: ({service_names})'
        url_matches = list(re.finditer(url_regex, text_content, re.IGNORECASE))
        platform_matches = list(re.finditer(service_regex, text_content, re.IGNORECASE))
        all_matches = []
        for match in url_matches:
            all_matches.append((match.start(), match.end(), 'url', match.group()))
        for match in platform_matches:
            all_matches.append((match.start(), match.end(), 'platform', match.group()))
        all_matches.sort(key=lambda x: x[0])
        
        if all_matches:
            last_end = 0
            for start, end, match_type, matched_text in all_matches:
                if start > last_end:
                    text_before = text_content[last_end:start]
                    tag = "error" if error else "normal"
                    log_textbox.insert("end", text_before, (tag,))
                if match_type == 'url':
                    log_textbox.insert("end", matched_text, ("hyperlink",))
                elif match_type == 'platform':
                    prefix = "Platform: "
                    service_name = matched_text.replace(prefix, "")
                    service_tag = f"service_{service_name.lower().replace(' ', '_')}"
                    log_textbox.insert("end", prefix)
                    log_textbox.insert("end", service_name, (service_tag,))
                
                last_end = end
            if last_end < len(text_content):
                remaining_text = text_content[last_end:]
                tag = "error" if error else "normal"
                log_textbox.insert("end", remaining_text, (tag,))
        else:
            tag = "error" if error else "normal"
            log_textbox.insert("end", text_content, (tag,))
    except Exception as e:
        tag = "error" if error else "normal"
        log_textbox.insert("end", text_content, (tag,))

def _process_color_markers(text, error):
    """Helper function to process color markers in text"""
    import re
    try:
        parts = []
        current_pos = 0
        color_markers = re.finditer(r'\|(RED|YELLOW|GRAY|PLATFORM_[A-Z_]+)\|(.*?)(?:\|RESET\||(?=\|[A-Z_]+\|)|$)', text)
        
        for marker in color_markers:
            if marker.start() > current_pos:
                text_before = text[current_pos:marker.start()]
                if text_before:
                    _insert_text_with_links_and_platforms(text_before, error)
            
            color = marker.group(1).lower()
            marker_text = marker.group(2)
            if color == 'red':
                log_textbox.insert("end", marker_text, ("color_red",))
            elif color == 'yellow':
                log_textbox.insert("end", marker_text, ("color_yellow",))
            elif color == 'gray':
                log_textbox.insert("end", marker_text, ("color_gray",))
            elif color.startswith('platform_'):
                platform_tag = color
                log_textbox.insert("end", marker_text, (platform_tag,))
            current_pos = marker.end()
        
        if current_pos < len(text):
            remaining_text = text[current_pos:]
            if remaining_text:
                _insert_text_with_links_and_platforms(remaining_text, error)
    except:
        _insert_text_with_links_and_platforms(text, error)

def log_to_textbox(msg, error=False):
    """
    Simplified log function that relies on clean CLI output.
    Only handles basic styling: colors, emojis, hyperlinks, and platform coloring.
    """
    global _last_message_was_empty, log_textbox, log_scrollbar, app
    
    try:
        if 'log_textbox' not in globals() or not log_textbox or not log_textbox.winfo_exists(): 
            return
        if any(filter_text in msg for filter_text in [
            "Librespot:Session - Failed reading packet!",
            "Librespot authentication failed during session creation: BadCredentials",
            "Failed to create Librespot session from existing OAuth credentials",
            "Attempting token refresh...",
            "Token refresh failed",
            "Attempting login via",
            "Login successful, obtained session ID",
            "Attempting authorization via",
            "Authorization successful, obtained code",
            "Exchanging code for token via",
            "Token exchange successful",
            "Initializing async downloads...",
            "Set Windows ProactorEventLoopPolicy",
            "Starting async event loop...",
            "Creating aiohttp session...",
            "aiohttp session created successfully"
        ]) or any(pattern in msg for pattern in [
            "Download speed: ",
            "Download time: "
        ]):
            return

        content_to_insert = _clean_ansi_and_process_markers(msg)
        is_current_empty = not content_to_insert.strip()
        if is_current_empty and _last_message_was_empty: 
            return
        _last_message_was_empty = is_current_empty
        
        if not content_to_insert:
            return
            
        log_textbox.configure(state="normal")
        try:
            log_textbox.tag_configure("error", foreground="#FF4444")
            log_textbox.tag_configure("detail_text", foreground="#B1B6BD")
            log_textbox.tag_configure("normal", foreground="")
            log_textbox.tag_configure("hyperlink", foreground="royal blue", underline=True)
            log_textbox.tag_configure("emoji_success", foreground="#00C851")
            log_textbox.tag_configure("emoji_error", foreground="#FF4444")
            log_textbox.tag_configure("emoji_warning", foreground="#CCA700")
            log_textbox.tag_configure("color_red", foreground="#FF4444")
            log_textbox.tag_configure("color_yellow", foreground="#CCA700")
            log_textbox.tag_configure("color_gray", foreground="#B1B6BD")
            for service, color in SERVICE_COLORS.items():
                log_textbox.tag_configure(f"service_{service.replace(' ', '_')}", foreground=color)
                log_textbox.tag_configure(f"platform_{service.replace(' ', '_')}", foreground=color)
                
            log_textbox.tag_bind("hyperlink", "<Enter>", lambda e: log_textbox.config(cursor=HAND_CURSOR))
            log_textbox.tag_bind("hyperlink", "<Leave>", lambda e: log_textbox.config(cursor=""))
            log_textbox.tag_bind("hyperlink", "<Button-1>", _on_hyperlink_click)
        except: 
            pass
        if "|ERROR_SYMBOL_SINGLE|" in content_to_insert:
            parts = content_to_insert.split("|ERROR_SYMBOL_SINGLE|")
            for i, part in enumerate(parts):
                if i == 0:
                    if part:
                        if "|RED|" in part or "|YELLOW|" in part or "|GRAY|" in part or "|PLATFORM_" in part:
                            _process_color_markers(part, error)
                        else:
                            _insert_text_with_links_and_platforms(part, error)
                else:
                    if "|ERROR_SYMBOL_END|" in part:
                        symbol_and_rest = part.split("|ERROR_SYMBOL_END|", 1)
                        symbol_text = symbol_and_rest[0]
                        rest_text = symbol_and_rest[1] if len(symbol_and_rest) > 1 else ""
                        log_textbox.insert("end", symbol_text, ("emoji_error",))
                        if rest_text:
                            if "|RED|" in rest_text or "|YELLOW|" in rest_text or "|GRAY|" in rest_text or "|PLATFORM_" in rest_text:
                                _process_color_markers(rest_text, error)
                            else:
                                _insert_text_with_links_and_platforms(rest_text, error)
                    else:
                        _insert_text_with_links_and_platforms(part, error)
            return
        
        emoji_processed = False
        for emoji, tag in [("✅", "emoji_success"), ("❌", "emoji_error"), ("▶", "emoji_warning"), ("✓", "emoji_success")]:
            if emoji in content_to_insert:
                parts = content_to_insert.split(emoji)
                for i, part in enumerate(parts):
                    if part:
                        if "|RED|" in part or "|YELLOW|" in part or "|GRAY|" in part or "|PLATFORM_" in part:
                            import re
                            try:
                                color_parts = []
                                current_pos = 0
                                color_markers = re.finditer(r'\|(RED|YELLOW|GRAY|PLATFORM_[A-Z_]+)\|(.*?)(?:\|RESET\||(?=\|[A-Z_]+\|)|$)', part)
                                
                                for marker in color_markers:
                                    if marker.start() > current_pos:
                                        text_before = part[current_pos:marker.start()]
                                        if text_before:
                                            _insert_text_with_links_and_platforms(text_before, error)
                                    
                                    color = marker.group(1).lower()
                                    text = marker.group(2)
                                    if color == 'red':
                                        log_textbox.insert("end", text, ("color_red",))
                                    elif color == 'yellow':
                                        log_textbox.insert("end", text, ("color_yellow",))
                                    elif color == 'gray':
                                        log_textbox.insert("end", text, ("color_gray",))
                                    elif color.startswith('platform_'):
                                        platform_tag = color
                                        log_textbox.insert("end", text, (platform_tag,))
                                    current_pos = marker.end()
                                
                                if current_pos < len(part):
                                    remaining_text = part[current_pos:]
                                    if remaining_text:
                                        _insert_text_with_links_and_platforms(remaining_text, error)
                            except:
                                _insert_text_with_links_and_platforms(part, error)
                        else:
                            _insert_text_with_links_and_platforms(part, error)
                    
                    if i < len(parts) - 1:
                        log_textbox.insert("end", emoji, (tag,))
                
                emoji_processed = True
                break
        
        if not emoji_processed:
            if "=== + " in content_to_insert:
                parts = content_to_insert.split("=== + ")
                log_textbox.insert("end", parts[0] + "=== ")
                log_textbox.insert("end", "✅", ("emoji_success",))
                if len(parts) > 1:
                    log_textbox.insert("end", " " + parts[1])
            elif "=== X " in content_to_insert or "=== ✗ " in content_to_insert:
                if "=== X " in content_to_insert:
                    parts = content_to_insert.split("=== X ")
                    symbol = "❌"
                else:
                    parts = content_to_insert.split("=== ✗ ")
                    symbol = "❌"
                log_textbox.insert("end", parts[0] + "=== ")
                log_textbox.insert("end", symbol, ("emoji_error",))
                if len(parts) > 1:
                    log_textbox.insert("end", " " + parts[1])
            elif "=== > " in content_to_insert:
                parts = content_to_insert.split("=== > ")
                log_textbox.insert("end", parts[0] + "=== ")
                log_textbox.insert("end", "▶", ("emoji_warning",))
                if len(parts) > 1:
                    log_textbox.insert("end", " " + parts[1])
            else:
                import re
                try:
                    if "|RED|" in content_to_insert or "|YELLOW|" in content_to_insert or "|GRAY|" in content_to_insert or "|PLATFORM_" in content_to_insert:
                        parts = []
                        current_pos = 0
                        color_markers = re.finditer(r'\|(RED|YELLOW|GRAY|PLATFORM_[A-Z_]+)\|(.*?)(?:\|RESET\||(?=\|[A-Z_]+\|)|$)', content_to_insert)
                        
                        for marker in color_markers:
                            if marker.start() > current_pos:
                                parts.append(('text', content_to_insert[current_pos:marker.start()]))
                            color = marker.group(1).lower()
                            text = marker.group(2)
                            parts.append(('color', color, text))
                            current_pos = marker.end()
                        if current_pos < len(content_to_insert):
                            parts.append(('text', content_to_insert[current_pos:]))
                        for part in parts:
                            if part[0] == 'text':
                                _insert_text_with_links_and_platforms(part[1], error)
                                    
                            elif part[0] == 'color':
                                color = part[1]
                                text = part[2]
                                if color == 'red':
                                    log_textbox.insert("end", text, ("color_red",))
                                elif color == 'yellow':
                                    log_textbox.insert("end", text, ("color_yellow",))
                                elif color == 'gray':
                                    log_textbox.insert("end", text, ("color_gray",))

                                elif color.startswith('platform_'):
                                    platform_tag = color
                                    log_textbox.insert("end", text, (platform_tag,))
                                else:
                                    tag = "error" if error else "normal"
                                    log_textbox.insert("end", text, (tag,))
                    
                    else:
                        _insert_text_with_links_and_platforms(content_to_insert, error)
                            
                except re.error as regex_err:
                    print(f"[Debug] Regex error in log_to_textbox: {regex_err}")
                    tag = "error" if error else "normal"
                    log_textbox.insert("end", content_to_insert, (tag,))
            try:
                yview_info = log_textbox.yview()
                is_at_bottom = yview_info[1] >= 0.95
                
                if is_at_bottom:
                    log_textbox.yview_moveto(1.0)
                    log_textbox.update()
            except:
                pass
                
            log_textbox.configure(state="disabled")
            def delayed_scroll():
                try:
                    if log_textbox and log_textbox.winfo_exists():
                        yview_info = log_textbox.yview()
                        is_at_bottom = yview_info[1] >= 0.95
                        
                        if is_at_bottom:
                            log_textbox.yview_moveto(1.0)
                            log_textbox.update_idletasks()
                except:
                    pass
            
            if 'app' in globals() and app and app.winfo_exists():
                app.after(10, delayed_scroll)
        try:
            if 'app' in globals() and app and app.winfo_exists() and 'log_scrollbar' in globals() and log_scrollbar:
                app.after(0, lambda: _check_and_toggle_text_scrollbar(log_textbox, log_scrollbar))
        except: 
            pass
            
    except NameError: 
        print("[Debug] log_to_textbox: NameError (likely widget not ready)")
    except tkinter.TclError as e: 
        print(f"TclError in log_to_textbox (widget destroyed?): {e}")
    except Exception as e:
        print(f"Error in log_to_textbox: {e}")
        try:
            if 'log_textbox' in globals() and log_textbox and log_textbox.winfo_exists():
                log_textbox.configure(state="disabled")
        except: 
            pass

_has_shown_unavailable_warning = False

def update_log_area():
    global output_queue, app, _has_shown_unavailable_warning, _current_download_context
    try:
        messages_processed = 0
        max_messages_per_update = 5
        start_time = time.time()
        max_processing_time = 0.02
        
        while messages_processed < max_messages_per_update:
            try: 
                msg = output_queue.get_nowait()
                msg_strip = msg.strip()
                if msg_strip.startswith('[Apple Music]'):
                    continue
                # Filter redundant YouTube error messages (track failure already shows error status with X icon)
                if msg_strip.startswith('[YouTube Error]'):
                    continue
                if msg_strip.startswith('[YouTube] Download error:'):
                    continue
                if 'Professional subscription detected' in msg_strip or 'allowing high and lossless quality' in msg_strip:
                    continue
                if 'No tracks were deferred due to rate limiting' in msg_strip:
                    continue
                if 'Cover resized from' in msg_strip and 'MB to' in msg_strip and 'px)' in msg_strip:
                    continue
                if ('All ' in msg_strip and ' tracks available!' in msg_strip and
                    ('downloaded' in msg_strip or 'already existed' in msg_strip or 'failed' in msg_strip)):
                    continue
                if (' tracks processed!' in msg_strip and
                    ('downloaded' in msg_strip or 'already existed' in msg_strip or 'failed' in msg_strip)):
                    continue
                if msg_strip.startswith('=== Downloading track'):
                    _has_shown_unavailable_warning = False
                if 'This song is unavailable' in msg_strip:
                    if not _has_shown_unavailable_warning:
                        try:
                            recent_content = log_textbox.get("end-30l", "end")
                            if ("=== Downloading album" in recent_content and
                                "=== Downloading playlist" not in recent_content):
                                log_to_textbox("       This song is unavailable.\n")
                            else:
                                log_to_textbox("       This song is unavailable.\n")
                        except:
                            log_to_textbox("       This song is unavailable.\n")
                        _has_shown_unavailable_warning = True
                    continue
                if 'Failed after 3 attempts' in msg_strip and msg_strip.startswith('[ERROR]'):
                    log_to_textbox("[ERROR] Failed after 3 attempts.\n", error=True)
                    continue
                if 'Track is not from the correct artist, skipping' in msg_strip:
                    log_to_textbox("Track is not from the correct artist, skipping\n")
                    continue
                if 'Pausing for' in msg_strip and 'seconds before next download attempt' in msg_strip:
                    log_to_textbox(msg)
                    log_to_textbox("\n")
                    continue
                if '[CRITICAL]' in msg_strip and 'Librespot:Session' in msg_strip and 'Failed reading packet!' in msg_strip:
                    continue
                if ('Could not get track info for' in msg_strip or 'Could not get album info for' in msg_strip
                        or 'Could not get playlist info for' in msg_strip or 'Could not get artist info for' in msg_strip):
                    log_to_textbox(f"{msg_strip}\n", error=True)
                    continue
                if 'Download stop requested...' in msg_strip:
                    log_to_textbox("|GRAY|Download stop requested... Please wait.|RESET|\n")
                    continue
                if 'tracks in playlist... Please wait.' in msg_strip:
                    fixed_message = msg_strip.lstrip()
                    log_to_textbox(f"{fixed_message}\n")
                    continue
                if msg_strip.startswith('Fetching ') and 'Fetching data. Please wait...' in msg_strip:
                    parts = msg_strip.split('Fetching data. Please wait...')
                    if len(parts) >= 2:
                        log_to_textbox(f"Fetching data. Please wait...\n")
                        continue
                import re
                if re.search(r'Fetching \d+/\d+', msg_strip):
                    if '===' in msg_strip:
                        cleaned_msg = re.sub(r'Fetching \d+/\d+', '', msg_strip)
                        cleaned_msg = cleaned_msg.strip()
                        if cleaned_msg:
                            log_to_textbox(f"{cleaned_msg}\n")
                        continue
                    else:
                        continue
                if 'Processing' in msg_strip and 'standalone tracks...' in msg_strip and 'Artist Progress:' in msg_strip:
                    log_to_textbox(f"{msg}\n")
                    continue
                if 'Spotify authentication error during track download' in msg_strip or \
                   ('Download attempt' in msg_strip and 'failed. Retrying in' in msg_strip):
                    cleaned_message = msg_strip
                    if 'Spotify authentication error during track download' in msg_strip and 'Failed fetching audio key!' in msg_strip:
                        cleaned_message = msg_strip.split('Failed fetching audio key!')[0] + 'Failed fetching audio key!'
                    indented_message = f"       {cleaned_message}\n"
                    log_to_textbox(indented_message)
                    continue
                if '=== ✅ Track completed ===' in msg_strip:
                    log_to_textbox(msg)
                    continue
                if ('=== ✅ Album completed ===' in msg_strip or
                    '=== ✅ Track completed ===' in msg_strip or
                    '=== ✅ Playlist completed ===' in msg_strip or
                    '=== ✅ Artist completed ===' in msg_strip):
                    try:
                        next_msg = output_queue.get_nowait()
                        if next_msg.strip():
                            output_queue.put(next_msg)
                    except queue.Empty:
                        pass
                    continue
                is_error = msg_strip.startswith(('[WARNING]', '[ERROR]'))
                if is_error and (('Download attempt' in msg_strip and ('failed' in msg_strip or 'Retrying' in msg_strip)) or 
                                'Failed after 3 attempts' in msg_strip):
                    log_to_textbox(f"       {msg_strip}\n", error=is_error)
                else:
                    log_to_textbox(msg, error=is_error)

                messages_processed += 1
                if time.time() - start_time > max_processing_time:
                    break
            except queue.Empty: 
                break
            except Exception as e: 
                print(f"Error processing message from queue: {e}")
                break
        if 'app' in globals() and app and app.winfo_exists():
            app.update_idletasks()
            try:
                if 'log_textbox' in globals() and log_textbox and log_textbox.winfo_exists():
                    yview_info = log_textbox.yview()
                    is_at_bottom = yview_info[1] >= 0.95
                    
                    if is_at_bottom:
                        log_textbox.yview_moveto(1.0)
            except:
                pass
            
    except Exception as e: 
        print(f"[ERROR] Exception in update_log_area loop: {type(e).__name__}: {e}")
    finally:
        try:
            if 'app' in globals() and app and app.winfo_exists():
                queue_size = output_queue.qsize() if output_queue else 0
                update_interval = min(100, max(25, queue_size * 2))
                app.after(update_interval, update_log_area)
            else:
                print("[Debug] update_log_area: 'app' not found or destroyed, stopping log polling.")
        except NameError: 
            print("[Debug] update_log_area: NameError accessing 'app'.")
        except Exception as e_sched: 
            print(f"[Error] Could not reschedule update_log_area: {e_sched}")

def clear_output_log():
    global log_textbox
    try:
        if 'log_textbox' in globals() and log_textbox and log_textbox.winfo_exists():
            log_textbox.configure(state='normal'); log_textbox.delete('1.0', tkinter.END); log_textbox.configure(state='disabled')
    except NameError: pass
    except tkinter.TclError as e: print(f"TclError clearing log (widget destroyed?): {e}")
    except Exception as e: print(f"Error clearing log: {e}")

def browse_output_path(path_variable):
    directory = tkinter.filedialog.askdirectory(initialdir=path_variable.get())
    if directory: path_variable.set(directory)

def clear_url_entry():
    global url_entry
    try:
        if 'url_entry' in globals() and url_entry and url_entry.winfo_exists():
            url_entry.delete(0, tkinter.END)
    except NameError: pass
    except tkinter.TclError as e: print(f"TclError clearing URL entry (widget destroyed?): {e}")
    except Exception as e: print(f"Error clearing URL entry: {e}")

def open_download_path():
    global path_var_main
    try:
        if 'path_var_main' not in globals() or not path_var_main: return

        path_to_open = (path_var_main.get() or "").strip()
        if not path_to_open:
            show_centered_messagebox("Warning", "Output path is empty.", dialog_type="warning")
            return
        # Resolve to absolute path so Windows os.startfile() works (it can fail with relative paths like ./downloads/)
        path_abs = os.path.abspath(os.path.normpath(path_to_open))
        if not os.path.isdir(path_abs):
            try:
                os.makedirs(path_abs, exist_ok=True)
            except Exception as e:
                show_centered_messagebox("Error", f"Output path does not exist and could not be created: {e}", dialog_type="error")
                return
        try:
            if platform.system() == "Windows":
                os.startfile(path_abs)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", path_abs])
            else:
                subprocess.Popen(["xdg-open", path_abs])
        except Exception as e:
            show_centered_messagebox("Error", f"Could not open path: {e}", dialog_type="error")
    except NameError: pass
    except Exception as e: print(f"Error opening download path: {e}")

def clear_search_entry():
    global search_entry
    try:
        if 'search_entry' in globals() and search_entry and search_entry.winfo_exists():
            search_entry.delete(0, tkinter.END)
    except NameError: pass
    except tkinter.TclError as e: print(f"TclError clearing search entry (widget destroyed?): {e}")
    except Exception as e: print(f"Error clearing search entry: {e}")

def set_ui_state_downloading(is_downloading):
    global download_button, stop_button, progress_bar, app
    def _update_state():
        download_state = "disabled" if is_downloading else "normal"; stop_state = "normal" if is_downloading else "disabled"
        try:
            if 'download_button' in globals() and download_button and download_button.winfo_exists():
                 download_button.configure(state=download_state)
            if 'stop_button' in globals() and stop_button and stop_button.winfo_exists():
                 stop_button.configure(state=stop_state)
            if 'progress_bar' in globals() and progress_bar and progress_bar.winfo_exists():
                if is_downloading: progress_bar.configure(mode="indeterminate"); progress_bar.start()
                else: progress_bar.stop(); progress_bar.set(0); progress_bar.configure(mode="determinate")
        except NameError: print("[Debug] NameError setting download UI state.")
        except tkinter.TclError as e: print(f"TclError setting download UI state (widget destroyed?): {e}")
        except Exception as e: print(f"Error setting download UI state: {e}")
    try:
        if 'app' in globals() and app and app.winfo_exists():
            app.after(0, _update_state)
        else: print("[Debug] 'app' not found for download UI state update.")
    except NameError: print("[Debug] NameError accessing 'app' for download UI state update.")
    except Exception as e: print(f"Error scheduling download UI state update: {e}")

def set_ui_state_searching(is_searching):
    global search_button, clear_search_button, platform_combo, type_combo, search_entry, search_progress_bar, app
    def _update_state():
        state = "disabled" if is_searching else "normal"; combo_state = "disabled" if is_searching else "readonly"
        try:
            if 'search_button' in globals() and search_button and search_button.winfo_exists(): search_button.configure(state=state)
            if 'clear_search_button' in globals() and clear_search_button and clear_search_button.winfo_exists(): clear_search_button.configure(state=state)
            if 'platform_combo' in globals() and platform_combo and platform_combo.winfo_exists(): platform_combo.configure(state=combo_state)
            if 'type_combo' in globals() and type_combo and type_combo.winfo_exists(): type_combo.configure(state=combo_state)
            if 'search_entry' in globals() and search_entry and search_entry.winfo_exists(): search_entry.configure(state=state)
            if 'search_progress_bar' in globals() and search_progress_bar and search_progress_bar.winfo_exists():
                if is_searching: search_progress_bar.configure(mode="indeterminate"); search_progress_bar.start()
                else: search_progress_bar.stop(); search_progress_bar.set(0); search_progress_bar.configure(mode="determinate")
        except NameError: pass
        except tkinter.TclError as e: print(f"TclError setting search UI state (widget destroyed?): {e}")
        except Exception as e: print(f"Error setting search UI state: {e}")
    try:
        if 'app' in globals() and app and app.winfo_exists():
            app.after(0, _update_state)
        else: print("[Debug] 'app' not found for search UI state update.")
    except NameError: pass
    except Exception as e: print(f"Error scheduling search UI state update: {e}")

def _check_and_toggle_scrollbar(tree_widget, scrollbar_widget):
    if not tree_widget or not tree_widget.winfo_exists() or not scrollbar_widget or not scrollbar_widget.winfo_exists(): return
    try:
        tree_widget.update_idletasks(); yview_info = tree_widget.yview()
        if yview_info[1] < 1.0 and tree_widget.get_children():
            if not scrollbar_widget.winfo_ismapped(): scrollbar_widget.grid(row=0, column=1, sticky='ns', pady=3, padx=(0,5))
        else:
             if scrollbar_widget.winfo_ismapped(): scrollbar_widget.grid_remove()
    except Exception as e:
        if isinstance(e, tkinter.TclError): pass
        else: print(f"Error checking/toggling scrollbar: {e}")

def _check_and_toggle_text_scrollbar(text_widget, scrollbar_widget):
    """Check if text widget needs scrollbar and show/hide accordingly"""
    if not text_widget or not text_widget.winfo_exists() or not scrollbar_widget or not scrollbar_widget.winfo_exists():         
        return
    try:        
        text_widget.update_idletasks()
        first, last = text_widget.yview()
        is_content_fully_visible = (last - first) >= (1.0 - 1e-9)

        if not is_content_fully_visible:
            if not scrollbar_widget.winfo_ismapped():
                scrollbar_widget.grid(row=0, column=1, sticky='ns') 
                text_widget.update_idletasks()
        else:            
            if scrollbar_widget.winfo_ismapped():                 
                scrollbar_widget.grid_remove()
                text_widget.update_idletasks()
    except Exception as e:
        if isinstance(e, tkinter.TclError):             
            pass
        else: 
            print(f"Error checking/toggling text scrollbar: {e}")

class QueueWriter(io.TextIOBase):
    def __init__(self, queue_instance, media_type=None):
        self.queue = queue_instance
        self.buffer = ''
        self.media_type = media_type
        self.in_track_context = False
        self.completed_track_count = 0
        self.total_tracks = 0
        self.in_concurrent_download = False
        
        self.MESSAGES_TO_INDENT = [
            "Downloading encrypted stream...",
            "Getting decryption key...",
            "Processing with legacy remux...",
            "Applying Apple Music metadata...",
        ]

    def _is_progress_bar_line(self, line):
        """Check if a line is a tqdm progress bar that should be filtered out."""
        stripped = line.strip()
        if not stripped:
            return False
        import re
        if re.search(r'\d+%\|.*\|.*\[.*[KMGT]?B/s.*\]', stripped):
            return True
        if ('|' in stripped and
            re.search(r'\d+\.\d+[KMGT]?B/\d+\.\d+[KMGT]?B', stripped) and
            re.search(r'\[.*[KMGT]?B/s.*\]', stripped)):
            return True
        if re.match(r'^\s*\d+%\|[#\s\-\.]*\|', stripped):
            return True

        return False

    def write(self, msg):
        global current_settings
        
        if '\r' in msg:
            parts = msg.split('\r')
            filtered_parts = []
            for part in parts:
                if not self._is_progress_bar_line(part):
                    filtered_parts.append(part)
            if filtered_parts:
                msg = filtered_parts[-1]
            else:
                return len(msg)


        self.buffer += msg
        if '\n' in self.buffer:
            lines = self.buffer.split('\n')
            for line in lines[:-1]:
                if self._is_progress_bar_line(line):
                    continue
                is_debug_mode = current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False)
                if not is_debug_mode and "[gamdl AppleMusicApi DEBUG]" in line:
                    continue
                import re
                line = re.sub(r'(\d+/\d+\s+)\+(\s+)', r'\1✓\2', line)
                line = re.sub(r'(\d+/\d+\s+)>(\s+)', r'\1▶\2', line)
                line = re.sub(r'(\d+/\d+\s+)x(\s+)', r'\1✗\2', line)
                if "soundcloud --> HLS_UNEXPECTED_ERROR_IN_TRY_BLOCK" in line:
                    line = re.sub(r'.*soundcloud --> HLS_UNEXPECTED_ERROR_IN_TRY_BLOCK.*', 
                                  '       SoundCloud streaming error (FFmpeg required for HLS streams)', line)
                if "FFmpeg is not installed or working! Using fallback, may have errors" in line:
                    buffer_context = (self.buffer + msg).lower()
                    
                    should_show_warning = False
                    if 'platform: soundcloud' in buffer_context:
                        should_show_warning = True
                    if current_settings and current_settings.get('advanced', {}).get('codec_conversions', {}):
                        should_show_warning = True
                    if should_show_warning:
                        line = re.sub(r'^\s*FFmpeg is not installed or working! Using fallback, may have errors', 
                                      '       FFmpeg is not installed or working! Using fallback, may have errors', line)
                    else:
                        continue
                
                stripped_line = line.lstrip()
                if ("=== ✅" in line or "=== ❌" in line or
                    "Track completed" in line or "Track failed" in line or
                    "Album completed" in line or "Album failed" in line or "Album skipped" in line):
                    if "=== ✅" in line:
                        completion_msg = line[line.find("=== ✅"):]
                    elif "=== ❌" in line:
                        completion_msg = line[line.find("=== ❌"):]
                    elif "=== ▶" in line:
                        completion_msg = line[line.find("=== ▶"):]
                    else:
                        completion_msg = stripped_line
                    self.queue.put(completion_msg.strip() + '\n')
                    continue

                if ("=== ✅ Album completed ===" in stripped_line or 
                    "=== ✅ Playlist completed ===" in stripped_line or
                    "=== ✅ Artist completed ===" in stripped_line):
                    self.in_concurrent_download = False
                    self.completed_track_count = 0
                if (not self.media_type or self.media_type == DownloadTypeEnum.track) and (
                    stripped_line.startswith("Artists:") or
                    stripped_line.startswith("Release year:") or
                    stripped_line.startswith("Duration:") or
                    stripped_line.startswith("Platform:") or
                    stripped_line.startswith("Codec:") or
                    stripped_line.startswith("Downloading audio...") or
                    stripped_line.startswith("Downloading artwork...") or
                    stripped_line.startswith("Tagging file...") or
                    stripped_line.startswith("Spotify API error during track download:") or
                    stripped_line.startswith("[ERROR]") or
                    stripped_line.startswith("No download info available")):
                    self.queue.put("       " + stripped_line + '\n')
                    continue

                if self.media_type == DownloadTypeEnum.artist or self.media_type == DownloadTypeEnum.album or self.media_type == DownloadTypeEnum.playlist:
                    import re
                    if "=== ✅ Album completed ===" in line:
                        line = "=== ✅ Album completed ==="
                    elif re.match(r'^\s*\d+/\d+\s+[▶✓❌⚠]', line):
                        if self.media_type == DownloadTypeEnum.artist:
                            stripped_content = line.strip()
                            line = "       " + stripped_content
                        elif self.media_type == DownloadTypeEnum.album:
                            stripped_content = line.strip()
                            line = "       " + stripped_content
                        elif self.media_type == DownloadTypeEnum.playlist:
                            stripped_content = line.strip()
                            line = "       " + stripped_content
                        elif self.in_concurrent_download and self.total_tracks > 0:
                            self.completed_track_count += 1
                            match = re.match(r'^\s*\d+/\d+\s+([▶✓❌⚠])\s*(.*)', line)
                            if match:
                                status_symbol = match.group(1)
                                track_name = match.group(2)
                                total_digits = len(str(self.total_tracks))
                                formatted_line = f"{self.completed_track_count:0{total_digits}d}/{self.total_tracks} {status_symbol} {track_name}"
                                line = formatted_line
                            else:
                                line = stripped_line
                        else:
                            line = stripped_line
                    elif ("Processing album track" in stripped_line or
                        "-> Album Track" in stripped_line or
                        "Processing album" in stripped_line or
                        "Fetching SoundCloud album metadata" in stripped_line or
                        "Downloading album cover" in stripped_line or
                        ("=== Track" in stripped_line and ("downloaded ===" in stripped_line or "completed ===" in stripped_line)) or
                        ("=== Downloading album" in stripped_line) or
                        ("=== Downloading track" in stripped_line) or
                        ("=== ❌ Album" in stripped_line and "cancelled ===" in stripped_line)):
                        line = stripped_line
                    if self.media_type == DownloadTypeEnum.artist:
                        if "=== Downloading track" in stripped_line:
                            self.in_track_context = True
                        elif "=== Downloading album" in stripped_line:
                            self.in_track_context = False
                        elif "=== ✅ Track completed ===" in stripped_line:
                            self.in_track_context = False
                    if self.media_type == DownloadTypeEnum.artist and self.in_track_context and (
                        stripped_line.startswith("Artists:") or
                        stripped_line.startswith("Release year:") or
                        stripped_line.startswith("Duration:") or
                        stripped_line.startswith("Platform:") or
                        stripped_line.startswith("Codec:") or
                        stripped_line.startswith("Downloading audio...") or
                        stripped_line.startswith("Downloading artwork...") or
                        stripped_line.startswith("Tagging file...") or
                        stripped_line.startswith("Track file already exists") or
                        "This song is unavailable" in stripped_line or
                        stripped_line.startswith("Spotify API error during track download:") or
                        stripped_line.startswith("[ERROR]") or
                        stripped_line.startswith("No download info available") or
                        any(msg in stripped_line for msg in self.MESSAGES_TO_INDENT)):
                        line = "       " + stripped_line
                    elif self.media_type == DownloadTypeEnum.artist and not self.in_track_context and (
                        stripped_line.startswith("Artist:") or
                        stripped_line.startswith("Year:") or
                        stripped_line.startswith("Duration:") or
                        stripped_line.startswith("Number of tracks:") or
                        stripped_line.startswith("Platform:") or
                        stripped_line.startswith("Skipping unrecognized album item") or
                        (stripped_line.startswith("Using ") and "concurrent downloads" in stripped_line)):
                        line = "       " + stripped_line
                    elif self.media_type == DownloadTypeEnum.artist and not self.in_track_context and (
                        (stripped_line.startswith("Using ") and "sequential downloads" in stripped_line)):
                        line = "       " + stripped_line + "\n"
                    elif self.media_type == DownloadTypeEnum.artist and (
                        stripped_line.startswith("Track ") and ("Pass" in stripped_line)):
                        line = "       " + stripped_line
                    elif line.startswith('        ') and not line.startswith('         ') and not line.startswith('=== '):
                        if not (self.media_type == DownloadTypeEnum.artist and re.match(r'^\s*\d+/\d+\s+[▶✓❌⚠]', line)):
                            line = line[1:]
                elif self.media_type == DownloadTypeEnum.playlist:
                    stripped_line = line.lstrip()
                    if any(msg in stripped_line for msg in self.MESSAGES_TO_INDENT):
                        line = "        " + stripped_line
                    elif "=== Track" in stripped_line and ("downloaded ===" in stripped_line or "completed ===" in stripped_line):
                        line = stripped_line
                    elif (stripped_line.startswith("Using ") and ("sequential downloads" in stripped_line or "concurrent downloads" in stripped_line)):
                        line = "       " + stripped_line
                    elif (stripped_line.startswith("Track ") and ("Pass" in stripped_line)):
                        line = "       " + stripped_line
                    elif line.startswith('        ') and not line.startswith('         ') and not line.startswith('=== '):
                        contains_apple_music_msg = any(msg in line for msg in self.MESSAGES_TO_INDENT)
                        if not contains_apple_music_msg:
                            line = line[1:]
                elif self.media_type == DownloadTypeEnum.album:
                    stripped_line = line.lstrip()
                    import re
                    if re.match(r'^\d+/\d+\s+[▶✓❌⚠]', stripped_line):
                        line = "       " + stripped_line
                    elif "=== Downloading track" in stripped_line:
                        line = stripped_line
                    elif "=== Track" in stripped_line and ("downloaded ===" in stripped_line or "completed ===" in stripped_line):
                        line = stripped_line
                    elif "This song is unavailable" in stripped_line:
                        line = "       " + stripped_line
                    elif (stripped_line.startswith("Artists:") or
                          stripped_line.startswith("Release year:") or
                          stripped_line.startswith("Duration:") or
                          stripped_line.startswith("Platform:") or
                          stripped_line.startswith("Codec:") or
                          stripped_line.startswith("Downloading audio...") or
                          stripped_line.startswith("Downloading artwork...") or
                          stripped_line.startswith("Tagging file...") or
                          stripped_line.startswith("Spotify API error during track download:") or
                          stripped_line.startswith("[ERROR]") or
                          stripped_line.startswith("No download info available") or
                          (len(line) - len(line.lstrip()) >= 16 and any(detail in stripped_line for detail in [
                              "Artists:", "Release year:", "Duration:", "Platform:", "Codec:",
                              "Downloading audio...", "Downloading artwork...", "Tagging file..."
                          ]))):
                        if len(line) - len(line.lstrip()) >= 16:
                            line = line
                        else:
                            line = "       " + stripped_line
                    elif any(msg in stripped_line for msg in self.MESSAGES_TO_INDENT):
                        line = "       " + stripped_line
                    elif (stripped_line.startswith("Artist:") or
                          stripped_line.startswith("Year:") or
                          stripped_line.startswith("Number of tracks:")):
                        line = "       " + stripped_line
                    elif (stripped_line.startswith("Using ") and ("sequential downloads" in stripped_line or "concurrent downloads" in stripped_line)):
                        line = "       " + stripped_line
                    elif (stripped_line.startswith("Track ") and ("Pass" in stripped_line)):
                        line = "       " + stripped_line
                    elif line.startswith('        ') and not line.startswith('         ') and not line.startswith('=== '):
                        line = line[1:]
                elif self.media_type == DownloadTypeEnum.track:
                    stripped_line = line.lstrip()
                    if "=== Downloading track" in stripped_line:
                        line = stripped_line
                    elif "=== Track" in stripped_line and ("downloaded ===" in stripped_line or "completed ===" in stripped_line):
                        line = stripped_line
                    elif any(msg in stripped_line for msg in self.MESSAGES_TO_INDENT):
                        line = "       " + stripped_line
                    elif "This song is unavailable" in stripped_line:
                        line = "       " + stripped_line
                    elif (stripped_line.startswith("Artists:") or
                          stripped_line.startswith("Release year:") or
                          stripped_line.startswith("Duration:") or
                          stripped_line.startswith("Platform:") or
                          stripped_line.startswith("Codec:") or
                          stripped_line.startswith("Downloading audio...") or
                          stripped_line.startswith("Downloading artwork...") or
                          stripped_line.startswith("Tagging file...") or
                          stripped_line.startswith("Spotify API error during track download:") or
                          stripped_line.startswith("[ERROR]") or
                          stripped_line.startswith("No download info available")):
                        line = "       " + stripped_line
                    elif line.startswith('        ') and not line.startswith('         ') and not line.startswith('=== '):
                        line = line[1:]

                self.queue.put(line + '\n')
            self.buffer = lines[-1]
        return len(msg)

    def flush(self):
        if self.buffer:
            self.queue.put(self.buffer)
            self.buffer = ''

    def readable(self):
        return False

    def seekable(self):
        return False

    def writable(self):
        return True

def run_interruptible_download(download_func, stop_event, *args, **kwargs):
    """
    Runs a download function in a way that can be interrupted by checking stop_event.
    This approach uses a global cancellation flag and monkey-patching to make downloads more responsive to cancellation.
    """
    import threading
    import time
    global _download_cancelled
    _download_cancelled = False

    result = {'completed': False, 'exception': None, 'result': None}

    def download_worker():
        try:
            result['result'] = download_func(*args, **kwargs)
            result['completed'] = True
        except Exception as e:
            result['exception'] = e
            result['completed'] = True
    download_thread = threading.Thread(target=download_worker, daemon=True)
    download_thread.start()
    check_interval = 0.1
    cancellation_timeout = 3.0
    cancellation_start_time = None

    while download_thread.is_alive():
        if stop_event.is_set():
            _download_cancelled = True

            if cancellation_start_time is None:
                cancellation_start_time = time.time()
            download_thread.join(timeout=1.0)
            if time.time() - cancellation_start_time > cancellation_timeout:
                print("Download cancellation timeout reached. Forcing UI reset.")
                try:
                    if 'app' in globals() and app and app.winfo_exists():
                        app.after(0, lambda: set_ui_state_downloading(False))
                except:
                    pass
                raise DownloadCancelledError("Download cancelled by user (timeout)")

            if not download_thread.is_alive():
                raise DownloadCancelledError("Download cancelled by user")

        time.sleep(check_interval)
    _download_cancelled = False
    if result['exception']:
        raise result['exception']

    return result['result']

def patch_download_file_for_cancellation():
    """
    Monkey-patch the download_file function and concurrent download methods to check for cancellation during downloads.
    """
    try:
        import utils.utils as utils_module
        if not hasattr(utils_module, '_original_download_file'):
            utils_module._original_download_file = utils_module.download_file

        def cancellable_download_file(url, file_location, headers={}, enable_progress_bar=False, indent_level=0, artwork_settings=None):
            global _download_cancelled
            if _download_cancelled:
                raise DownloadCancelledError("Download cancelled before file download")
            import os
            from tqdm import tqdm

            if os.path.isfile(file_location):
                return None
            directory = os.path.dirname(file_location)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            r = utils_module.r_session.get(url, stream=True, headers=headers, verify=False)

            total = None
            if 'content-length' in r.headers:
                total = int(r.headers['content-length'])

            try:
                with open(file_location, 'wb') as f:
                    if enable_progress_bar and total:
                        import sys
                        from io import StringIO

                        class IndentedOutput:
                            def __init__(self, indent_level):
                                self.indent_level = indent_level

                            def write(self, text):
                                lines = text.split('\n')
                                indented_lines = []
                                for line in lines:
                                    if line.strip():
                                        indented_lines.append(' ' * self.indent_level + line)
                                    else:
                                        indented_lines.append(line)
                                sys.stdout.write('\n'.join(indented_lines))

                            def flush(self):
                                sys.stdout.flush()

                        bar = tqdm(
                            total=total,
                            unit='B',
                            unit_scale=True,
                            unit_divisor=1024,
                            initial=0,
                            miniters=1,
                            leave=False,
                            file=IndentedOutput(indent_level)
                        )
                        for chunk in r.iter_content(chunk_size=1024):
                            if _download_cancelled:
                                bar.close()
                                if os.path.isfile(file_location):
                                    os.remove(file_location)
                                raise DownloadCancelledError("Download cancelled during file transfer")

                            if chunk:
                                f.write(chunk)
                                bar.update(len(chunk))
                        bar.close()
                    else:
                        for chunk in r.iter_content(chunk_size=1024):
                            if _download_cancelled:
                                if os.path.isfile(file_location):
                                    os.remove(file_location)
                                raise DownloadCancelledError("Download cancelled during file transfer")

                            if chunk:
                                f.write(chunk)
                if artwork_settings and artwork_settings.get('should_resize', False):
                    if _download_cancelled:
                        if os.path.isfile(file_location):
                            os.remove(file_location)
                        raise DownloadCancelledError("Download cancelled during artwork processing")
                    new_resolution = artwork_settings.get('resolution', 1400)
                    new_format = artwork_settings.get('format', 'jpeg')
                    if new_format == 'jpg': new_format = 'jpeg'
                    new_compression = artwork_settings.get('compression', 'low')
                    if new_compression == 'low':
                        new_compression = 90
                    elif new_compression == 'high':
                        new_compression = 70
                    if new_format == 'png': new_compression = None

                    from PIL import Image
                    with Image.open(file_location) as im:
                        im = im.resize((new_resolution, new_resolution), Image.Resampling.BICUBIC)
                        im.save(file_location, new_format, quality=new_compression)

            except KeyboardInterrupt:
                if os.path.isfile(file_location):
                    print(f'\tDeleting partially downloaded file "{str(file_location)}"')
                    utils_module.silentremove(file_location)
                raise KeyboardInterrupt
            except DownloadCancelledError:
                if os.path.isfile(file_location):
                    print(f'\tDeleting partially downloaded file due to cancellation: "{str(file_location)}"')
                    try:
                        os.remove(file_location)
                    except:
                        pass
                raise
            return file_location
        utils_module.download_file = cancellable_download_file
        print("[Patch] Applied cancellable download_file patch.")
        try:
            from orpheus.music_downloader import Downloader
            if not hasattr(Downloader, '_original_concurrent_download_tracks'):
                Downloader._original_concurrent_download_tracks = Downloader._concurrent_download_tracks

            def cancellable_concurrent_download_tracks(self, track_list, download_args_list, concurrent_downloads, performance_summary_indent=0):
                """Patched version of _concurrent_download_tracks that respects cancellation"""
                global _download_cancelled
                should_indent_tracks = True

                if concurrent_downloads <= 1:
                    self.print("Using sequential downloads (sync)")
                    results = []
                    for i, (track_info, args) in enumerate(zip(track_list, download_args_list)):
                        if _download_cancelled:
                            print(f"Download cancelled during sequential track {i+1}")
                            break
                        try:
                            result = self.download_track(**args)
                            results.append((i, result, None))
                        except Exception as e:
                            results.append((i, None, e))
                        if _download_cancelled:
                            print(f"Download cancelled after sequential track {i+1}")
                            break
                    return results
                from concurrent.futures import ThreadPoolExecutor, as_completed
                import queue
                import threading
                total_tracks = len(track_list)
                self.print(f"Using {concurrent_downloads} concurrent downloads for {total_tracks} tracks", drop_level=performance_summary_indent)

                progress_queue = queue.Queue()

                def download_worker(index, args):
                    if _download_cancelled:
                        return (index, None, Exception("Download cancelled"))

                    try:
                        track_id = args.get('track_id', 'Unknown')
                        track_name = f"Track {track_id}"
                        track_info_failed = False
                        track_info_error = None
                        try:
                            if _download_cancelled:
                                return (index, None, Exception("Download cancelled"))
                                
                            from utils.models import QualityEnum, CodecOptions
                            quality_tier = QualityEnum[self.global_settings['general']['download_quality'].upper()]
                            codec_options = CodecOptions(
                                spatial_codecs=self.global_settings['codecs']['spatial_codecs'],
                                proprietary_codecs=self.global_settings['codecs']['proprietary_codecs'],
                            )
                            track_info = self.service.get_track_info(track_id, quality_tier, codec_options, **args.get('extra_kwargs', {}))
                            if track_info and hasattr(track_info, 'name') and track_info.name:
                                if hasattr(track_info, 'artists') and track_info.artists:
                                    artists_str = ', '.join(track_info.artists)
                                    track_name = f"{artists_str} - {track_info.name}"
                                else:
                                    track_name = track_info.name
                        except Exception as e:
                            track_info_failed = True
                            track_info_error = e
                        if track_info_failed:
                            progress_queue.put((index, track_name, track_info_error))
                            return (index, None, track_info_error)
                        if _download_cancelled:
                            return (index, None, Exception("Download cancelled"))
                        result = self.download_track(**args, verbose=False)
                        if _download_cancelled:
                            return (index, None, Exception("Download cancelled"))
                        if result == "SKIPPED":
                            progress_queue.put((index, track_name, "SKIPPED"))
                        elif result == "RATE_LIMITED":
                            progress_queue.put((index, track_name, "RATE_LIMITED"))
                        elif result is None:
                            progress_queue.put((index, track_name, Exception("Download failed")))
                        else:
                            progress_queue.put((index, track_name, None))

                        return (index, result, None)
                    except Exception as e:
                        error_track_name = track_name
                        if error_track_name.startswith("Track "):
                            try:
                                from utils.models import QualityEnum, CodecOptions
                                quality_tier = QualityEnum[self.global_settings['general']['download_quality'].upper()]
                                codec_options = CodecOptions(
                                    spatial_codecs=self.global_settings['codecs']['spatial_codecs'],
                                    proprietary_codecs=self.global_settings['codecs']['proprietary_codecs'],
                                )
                                track_info = self.service.get_track_info(track_id, quality_tier, codec_options, **args.get('extra_kwargs', {}))
                                if track_info and hasattr(track_info, 'name') and track_info.name:
                                    if hasattr(track_info, 'artists') and track_info.artists:
                                        artists_str = ', '.join(track_info.artists)
                                        error_track_name = f"{artists_str} - {track_info.name}"
                                    else:
                                        error_track_name = track_info.name
                            except Exception:
                                pass

                        progress_queue.put((index, error_track_name, e))
                        return (index, None, e)
                results = []
                completion_counter = 0
                with ThreadPoolExecutor(max_workers=concurrent_downloads) as executor:
                    future_to_index = {}
                    for i, args in enumerate(download_args_list):
                        if _download_cancelled:
                            print(f"Download cancelled before submitting task {i+1}")
                            break
                        future = executor.submit(download_worker, i, args)
                        future_to_index[future] = i
                    completed_count = 0
                    total_tasks = len(future_to_index)

                    for future in as_completed(future_to_index):
                        if _download_cancelled:
                            for remaining_future in future_to_index:
                                if not remaining_future.done():
                                    remaining_future.cancel()
                            executor.shutdown(wait=False)
                            break

                        try:
                            result = future.result()
                            results.append(result)
                            completed_count += 1
                            while not progress_queue.empty():
                                try:
                                    index, track_name, status = progress_queue.get_nowait()
                                    completion_counter += 1
                                    total_digits = len(str(total_tasks))
                                    indent_prefix = "       " if should_indent_tracks else ""
                                    
                                    if status == "SKIPPED":
                                        self.print(f'{indent_prefix}{completion_counter:0{total_digits}d}/{total_tasks} ▶ {track_name} |GRAY|(already exists)|RESET|', drop_level=1)
                                    elif status == "RATE_LIMITED":
                                        self.print(f'{indent_prefix}{completion_counter:0{total_digits}d}/{total_tasks} ⚠ {track_name} (rate limited)', drop_level=1)
                                    elif status is not None:
                                        error_msg = str(status)
                                        if "Could not get track info for" in error_msg:
                                            if ":" in error_msg:
                                                error_reason = error_msg.split(":", 1)[1].strip()
                                            else:
                                                error_reason = error_msg
                                        else:
                                            error_reason = error_msg

                                        self.print(f'{indent_prefix}{completion_counter:0{total_digits}d}/{total_tasks} ❌ {track_name}: {error_reason} |GRAY|(failed)|RESET|', drop_level=1)
                                    else:
                                        self.print(f'{indent_prefix}{completion_counter:0{total_digits}d}/{total_tasks} ✓ {track_name}', drop_level=1)
                                except queue.Empty:
                                    break
                        except Exception as e:
                            index = future_to_index[future]
                            results.append((index, None, e))
                actual_downloaded = sum(1 for r in results if r and r[2] is None and r[1] is not None and r[1] not in ["RATE_LIMITED", "SKIPPED"])
                actual_already_existed = sum(1 for r in results if r and r[2] is None and r[1] == "SKIPPED")
                actual_failed = sum(1 for r in results if r and (r[2] is not None or (r[1] == "RATE_LIMITED")))
                from utils.models import Oprinter

                if actual_failed > 0:
                    if actual_downloaded > 0 and actual_already_existed > 0:
                        Oprinter._original_oprint(self.oprinter, f"All {len(results)} tracks available! ({actual_downloaded} downloaded, {actual_already_existed} already existed, {actual_failed} failed)", drop_level=performance_summary_indent)
                    elif actual_downloaded > 0:
                        Oprinter._original_oprint(self.oprinter, f"{actual_downloaded + actual_failed} tracks processed! ({actual_downloaded} downloaded, {actual_failed} failed)", drop_level=performance_summary_indent)
                    elif actual_already_existed > 0:
                        Oprinter._original_oprint(self.oprinter, f"{actual_already_existed + actual_failed} tracks processed! ({actual_already_existed} already existed, {actual_failed} failed)", drop_level=performance_summary_indent)
                    else:
                        Oprinter._original_oprint(self.oprinter, f"{actual_failed} tracks failed.", drop_level=performance_summary_indent)
                else:
                    pass

                return results
            Downloader._concurrent_download_tracks = cancellable_concurrent_download_tracks
            print("[Patch] Applied cancellable concurrent download patch.")
            try:
                original_concurrent_func = Downloader._original_concurrent_download_tracks
                
                def patched_original_concurrent_download_tracks(self, track_list, download_args_list, concurrent_downloads, performance_summary_indent=0):
                    original_print_method = self.print
                    def indentation_aware_print(message, drop_level=0):
                        message_str = str(message)
                        is_track_progress = ('/' in message_str and 
                                           any(symbol in message_str for symbol in ['▶', '✓', '❌', '⚠']) and
                                           ('already exists' in message_str or 'failed' in message_str or 'rate limited' in message_str or 
                                            not any(keyword in message_str for keyword in ['Using', 'Summary:', 'Download'])))
                        
                        if is_track_progress:
                            indented_message = "       " + message_str
                            original_print_method(indented_message, drop_level=1)
                        else:
                            original_print_method(message, drop_level=drop_level)
                    self.print = indentation_aware_print
                    
                    try:
                        return original_concurrent_func(self, track_list, download_args_list, concurrent_downloads, performance_summary_indent)
                    finally:
                        self.print = original_print_method
                Downloader._original_concurrent_download_tracks = patched_original_concurrent_download_tracks
                print("[Patch] Applied indentation patch to original concurrent download function.")
                
            except Exception as e:
                print(f"[Patch Warning] Could not patch original concurrent download indentation: {e}")
            if not hasattr(Downloader, '_original_download_track'):
                Downloader._original_download_track = Downloader.download_track

                def cancellable_download_track(self, track_id, **kwargs):
                    """Patched version of download_track that checks for cancellation"""
                    global _download_cancelled
                    if _download_cancelled:
                        raise DownloadCancelledError("Download cancelled before track download")
                    return Downloader._original_download_track(self, track_id, **kwargs)
                Downloader.download_track = cancellable_download_track
                print("[Patch] Applied cancellable download_track patch.")
            try:
                from utils.models import Oprinter

                if not hasattr(Oprinter, '_original_oprint'):
                    Oprinter._original_oprint = Oprinter.oprint

                    def patched_oprint(self, inp: str, drop_level: int = 0):
                        inp_str = str(inp)
                        
                        is_summary_message = (
                            ("available! (" in inp_str and "downloaded" in inp_str and "already existed" in inp_str) or
                            ("processed! (" in inp_str) or
                            ("downloaded successfully!" in inp_str) or
                            ("failed." in inp_str and "tracks" in inp_str)
                        ) and not inp_str.strip().startswith("===")
                        is_completion_message = ("=== " in inp_str and "completed ===" in inp_str)

                        if is_summary_message and not is_completion_message:
                            return
                        elif not is_completion_message and any(keyword in inp_str for keyword in [
                            "tracks processed!", "tracks available!", "tracks downloaded successfully!",
                            "tracks already existed", "tracks failed.", "Summary:"
                        ]):
                            original_indent = self.indent_number
                            self.indent_number = 0
                            try:
                                Oprinter._original_oprint(self, inp, drop_level=0)
                            finally:
                                self.indent_number = original_indent
                        else:
                            Oprinter._original_oprint(self, inp, drop_level)

                    Oprinter.oprint = patched_oprint
                    print("[Patch] Applied Oprinter patch to remove summary indentation.")

            except Exception as oprinter_e:
                print(f"[Patch Warning] Could not patch Oprinter: {oprinter_e}")
            try:
                if not hasattr(Downloader, '_original_download_artist'):
                    Downloader._original_download_artist = Downloader.download_artist

                    def patched_download_artist(self, artist_id, **kwargs):
                        global _download_cancelled

                        try:
                            result = Downloader._original_download_artist(self, artist_id, **kwargs)
                            return result
                        except Exception as e:
                            if _download_cancelled or "Download cancelled" in str(e):
                                raise e
                            else:
                                raise e
                    def patched_download_artist_with_status_check(self, artist_id, **kwargs):
                        global _download_cancelled
                        original_print = self.print

                        def status_aware_print(message, drop_level=0):
                            message_str = str(message)
                            if "completed ===" in message_str and _download_cancelled:
                                if "=== Artist" in message_str:
                                    artist_name = message_str.split("=== Artist ")[1].split(" completed ===")[0] if "=== Artist " in message_str else "Unknown"
                                    original_print(f"=== ❌ Artist {artist_name} cancelled ===", drop_level=drop_level)
                                    original_print("", drop_level=drop_level)
                                elif "=== Album" in message_str:
                                    album_name = message_str.split("=== Album ")[1].split(" completed ===")[0] if "=== Album " in message_str else "Unknown"
                                    original_print(f"=== ❌ Album {album_name} cancelled ===", drop_level=drop_level)
                                    original_print("", drop_level=drop_level)
                                elif "=== Playlist" in message_str:
                                    playlist_name = message_str.split("=== Playlist ")[1].split(" completed ===")[0] if "=== Playlist " in message_str else "Unknown"
                                    original_print(f"=== ❌ Playlist {playlist_name} cancelled ===", drop_level=drop_level)
                                    original_print("", drop_level=drop_level)
                                elif "=== Track" in message_str:
                                    track_info = message_str.split("=== Track ")[1].split(" completed ===")[0] if "=== Track " in message_str else "Unknown"
                                    original_print(f"=== ❌ Track {track_info} cancelled ===", drop_level=drop_level)
                                    original_print("", drop_level=drop_level)
                            else:
                                original_print(message, drop_level=drop_level)
                        self.print = status_aware_print

                        try:
                            result = Downloader._original_download_artist(self, artist_id, **kwargs)
                            return result
                        finally:
                            self.print = original_print

                    Downloader.download_artist = patched_download_artist_with_status_check
                    print("[Patch] Applied download_artist patch to show correct completion status.")

            except Exception as artist_e:
                print(f"[Patch Warning] Could not patch download_artist: {artist_e}")
            try:
                if not hasattr(Downloader, '_original_download_track'):
                    Downloader._original_download_track = Downloader.download_track

                    def patched_download_track_with_status_check(self, track_id, **kwargs):
                        global _download_cancelled
                        original_print = self.print

                        def track_status_aware_print(message, drop_level=0):
                            message_str = str(message)
                            if "completed ===" in message_str and _download_cancelled:
                                if "=== Track" in message_str:
                                    track_info = message_str.split("=== Track ")[1].split(" completed ===")[0] if "=== Track " in message_str else "Unknown"
                                    original_print(f"=== ❌ Track {track_info} cancelled ===", drop_level=drop_level)
                                    original_print("", drop_level=drop_level)
                            else:
                                original_print(message, drop_level=drop_level)

                        self.print = track_status_aware_print
                        try:
                            result = Downloader._original_download_track(self, track_id, **kwargs)
                            return result
                        finally:
                            self.print = original_print

                    Downloader.download_track = patched_download_track_with_status_check
                if not hasattr(Downloader, '_original_download_album'):
                    Downloader._original_download_album = Downloader.download_album

                    def patched_download_album_with_status_check(self, album_id, **kwargs):
                        global _download_cancelled

                        original_print = self.print

                        def album_status_aware_print(message, drop_level=0):
                            message_str = str(message)
                            if "completed ===" in message_str and _download_cancelled:
                                if "=== Album" in message_str:
                                    album_name = message_str.split("=== Album ")[1].split(" completed ===")[0] if "=== Album " in message_str else "Unknown"
                                    original_print(f"=== ❌ Album {album_name} cancelled ===", drop_level=drop_level)
                                    original_print("", drop_level=drop_level)
                            else:
                                original_print(message, drop_level=drop_level)

                        self.print = album_status_aware_print
                        try:
                            result = Downloader._original_download_album(self, album_id, **kwargs)
                            return result
                        finally:
                            self.print = original_print

                    Downloader.download_album = patched_download_album_with_status_check
                if not hasattr(Downloader, '_original_download_playlist'):
                    Downloader._original_download_playlist = Downloader.download_playlist

                    def patched_download_playlist_with_status_check(self, playlist_id, **kwargs):
                        global _download_cancelled

                        original_print = self.print
                        original_download_track = self.download_track

                        def playlist_status_aware_print(message, drop_level=0):
                            message_str = str(message)
                            if "completed ===" in message_str and _download_cancelled:
                                if "=== Playlist" in message_str:
                                    playlist_name = message_str.split("=== Playlist ")[1].split(" completed ===")[0] if "=== Playlist " in message_str else "Unknown"
                                    original_print(f"=== ❌ Playlist {playlist_name} cancelled ===", drop_level=drop_level)
                                    original_print("", drop_level=drop_level)
                            else:
                                original_print(message, drop_level=drop_level)

                        def cancellation_aware_download_track(track_id, **track_kwargs):
                            if _download_cancelled:
                                service_name = getattr(self, 'service_name', 'Unknown')
                                raise DownloadCancelledError(f"Download cancelled during {service_name} playlist track processing")
                            return original_download_track(track_id, **track_kwargs)

                        self.print = playlist_status_aware_print
                        self.download_track = cancellation_aware_download_track
                        try:
                            result = Downloader._original_download_playlist(self, playlist_id, **kwargs)
                            return result
                        finally:
                            self.print = original_print
                            self.download_track = original_download_track

                    Downloader.download_playlist = patched_download_playlist_with_status_check

                print("[Patch] Applied completion status patches for all download types.")
                try:
                    def create_universal_cancellable_method(original_method, method_name, media_type):
                        """Factory function to create cancellation-aware download methods for all services"""
                        def universal_cancellable_download(self, *args, **kwargs):
                            global _download_cancelled
                            if _download_cancelled:
                                service_name = getattr(self, 'service_name', 'Unknown')
                                raise DownloadCancelledError(f"Download cancelled before {service_name} {media_type} processing")
                            original_print = self.print

                            def cancellation_checking_print(message, drop_level=0):
                                if _download_cancelled:
                                    service_name = getattr(self, 'service_name', 'Unknown')
                                    raise DownloadCancelledError(f"Download cancelled during {service_name} {media_type} processing")
                                return original_print(message, drop_level=drop_level)
                            self.print = cancellation_checking_print

                            try:
                                return original_method(self, *args, **kwargs)
                            finally:
                                self.print = original_print

                        return universal_cancellable_download
                    download_methods = [
                        ('download_track', 'track'),
                        ('download_album', 'album'),
                        ('download_playlist', 'playlist'),
                        ('download_artist', 'artist')
                    ]

                    for method_name, media_type in download_methods:
                        original_attr_name = f'_original_{method_name}_universal_patch'
                        if not hasattr(Downloader, original_attr_name):
                            original_method = getattr(Downloader, method_name)
                            setattr(Downloader, original_attr_name, original_method)
                            cancellable_method = create_universal_cancellable_method(original_method, method_name, media_type)
                            setattr(Downloader, method_name, cancellable_method)

                    print("[Patch] Applied universal cancellation patches for all music services (tracks, albums, playlists, and artists).")

                except Exception as universal_e:
                    print(f"[Patch Warning] Could not patch universal cancellation: {universal_e}")

            except Exception as other_e:
                print(f"[Patch Warning] Could not patch other download methods: {other_e}")

        except Exception as concurrent_e:
            print(f"[Patch Warning] Could not patch concurrent downloads: {concurrent_e}")

    except Exception as e:
        print(f"[Patch Warning] Could not patch download_file for cancellation: {e}")


def run_download_in_thread(orpheus, url, output_path, gui_settings, search_result_data=None):
    """Runs the download using the provided global Orpheus instance."""
    global output_queue, stop_event, app, download_process_active, DEFAULT_SETTINGS, _queue_log_handler_instance, _current_download_context
    import time
    import threading
    
    if _queue_log_handler_instance:
        _queue_log_handler_instance.reset_ffmpeg_state_for_current_download()

    if orpheus is None:
        logging.error("Orpheus instance not available. Cannot start download.")
        try:
            if 'app' in globals() and app and app.winfo_exists():
                 app.after(0, lambda: set_ui_state_downloading(False))
        except NameError: pass
        except Exception as e: logging.error(f"Error scheduling UI reset after Orpheus instance error: {e}")
        return

    def yield_to_gui():
        try:
            if 'app' in globals() and app and app.winfo_exists():
                app.update_idletasks()
            time.sleep(0.001)
        except:
            pass
    
    yielding_active = threading.Event()
    yielding_active.set()
    
    def periodic_yield():
        while yielding_active.is_set():
            yield_to_gui()
            time.sleep(0.1)
    yield_thread = threading.Thread(target=periodic_yield, daemon=True)
    yield_thread.start()

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    dummy_stderr = DummyStderr()
    is_cancelled = False
    download_exception_occurred = False
    start_time = datetime.datetime.now()
    media_type = None
    yield_to_gui()

    try:
        queue_writer = QueueWriter(output_queue, media_type=media_type)
        sys.stdout = queue_writer
        sys.stderr = dummy_stderr
        yield_to_gui()
        fresh_orpheus_settings = orpheus.settings if hasattr(orpheus, 'settings') else {}
        fresh_global_settings = fresh_orpheus_settings.get('global', {})
        ffmpeg_path_setting = fresh_global_settings.get("advanced", {}).get("ffmpeg_path", "ffmpeg")
        if isinstance(ffmpeg_path_setting, str):
            ffmpeg_path_setting = ffmpeg_path_setting.strip()
            if ffmpeg_path_setting and ffmpeg_path_setting.lower() != "ffmpeg":
                if os.path.isfile(ffmpeg_path_setting):
                    ffmpeg_dir = os.path.dirname(ffmpeg_path_setting)
                    current_path = os.environ.get("PATH", "")
                    if ffmpeg_dir not in current_path.split(os.pathsep):
                        os.environ["PATH"] = ffmpeg_dir + os.pathsep + current_path
        
        # Build downloader_settings by merging fresh settings with defaults for all sections
        # This ensures all required keys exist even on first run
        downloader_settings = {}
        
        # Get all section keys from both fresh settings and defaults
        all_section_keys = set(fresh_global_settings.keys()) | set(DEFAULT_SETTINGS["globals"].keys())
        
        for section_key in all_section_keys:
            fresh_section = fresh_global_settings.get(section_key, {})
            default_section = DEFAULT_SETTINGS["globals"].get(section_key, {})
            
            if section_key == "general":
                # Special handling for general section with key mapping
                downloader_settings["general"] = {
                    "download_path": fresh_section.get("download_path", default_section.get("output_path", "./downloads/")),
                    "download_quality": fresh_section.get("download_quality", default_section.get("quality", "hifi")),
                    "search_limit": fresh_section.get("search_limit", default_section.get("search_limit", 25)),
                    "concurrent_downloads": fresh_section.get("concurrent_downloads", default_section.get("concurrent_downloads", 5)),
                    "play_sound_on_finish": fresh_section.get("play_sound_on_finish", default_section.get("play_sound_on_finish", False)),
                    "progress_bar": False
                }
            elif isinstance(default_section, dict):
                # Merge section with defaults
                downloader_settings[section_key] = {**default_section, **fresh_section}
            else:
                # Non-dict section, use fresh value or default
                downloader_settings[section_key] = fresh_section if fresh_section else default_section
        if "advanced" in downloader_settings and \
           "conversion_flags" in downloader_settings["advanced"] and \
           "mp3" in downloader_settings["advanced"]["conversion_flags"]:
            mp3_flags = downloader_settings["advanced"]["conversion_flags"]["mp3"]
            if "audio_bitrate" in mp3_flags and "qscale:a" in mp3_flags:
                if fresh_global_settings.get("advanced",{}).get("conversion_flags",{}).get("mp3",{}).get("audio_bitrate"):
                    cleaned_mp3_flags = {"audio_bitrate": fresh_global_settings["advanced"]["conversion_flags"]["mp3"]["audio_bitrate"]}
                    downloader_settings["advanced"]["conversion_flags"]["mp3"] = cleaned_mp3_flags
                elif fresh_global_settings.get("advanced",{}).get("conversion_flags",{}).get("mp3",{}).get("qscale:a"):
                    cleaned_mp3_flags = {"qscale:a": fresh_global_settings["advanced"]["conversion_flags"]["mp3"]["qscale:a"]}
                    downloader_settings["advanced"]["conversion_flags"]["mp3"] = cleaned_mp3_flags

        yield_to_gui()

        module_controls_dict = orpheus.module_controls
        oprinter = Oprinter()
        downloader = Downloader(settings=downloader_settings, module_controls=module_controls_dict, oprinter=oprinter, path=output_path, use_ansi_colors=False)
        downloader.full_settings = {
            'global': downloader_settings,
            'modules': fresh_orpheus_settings.get('modules', {})
        }

        settings_global_for_defaults = fresh_global_settings if fresh_global_settings else DEFAULT_SETTINGS["globals"]
        module_defaults = settings_global_for_defaults.get("module_defaults", {})
        third_party_modules_dict = { ModuleModes.lyrics: module_defaults.get("lyrics") if module_defaults.get("lyrics") != "default" else None, ModuleModes.covers: module_defaults.get("covers") if module_defaults.get("covers") != "default" else None, ModuleModes.credits: module_defaults.get("credits") if module_defaults.get("credits") != "default" else None }
        downloader.third_party_modules = third_party_modules_dict
        parsed_url = urlparse(url); components = parsed_url.path.split('/'); module_name = None
        for netloc_pattern, mod_name in orpheus.module_netloc_constants.items():
            if re.findall(netloc_pattern, parsed_url.netloc): module_name = mod_name; break
        if not module_name: raise ValueError(f"Could not determine module for URL host: {parsed_url.netloc}")
        
        yield_to_gui()
        
        try:
            if orpheus.module_settings[module_name].url_decoding is ManualEnum.manual:
                # Use auto-auth patcher for Tidal to handle TV login automatically
                if module_name == 'tidal':
                    with TidalAutoAuthPatcher(output_queue):
                        module_instance = orpheus.load_module(module_name)
                else:
                    module_instance = orpheus.load_module(module_name)
                media_ident: MediaIdentification = module_instance.custom_url_parse(url)
                if not media_ident: raise ValueError(f"Module '{module_name}' custom_url_parse failed for URL: {url}")
                media_type = media_ident.media_type; media_id = media_ident.media_id
                if hasattr(media_ident, 'extra_kwargs') and media_ident.extra_kwargs:
                    downloader.extra_kwargs = media_ident.extra_kwargs
            else:
                media_id = None
                media_type = None
                if media_id is None or media_type is None:
                    if not components or len(components) <= 2:
                         if len(components) == 2 and components[1]: raise ValueError(f"Could not determine media type from short URL path: {parsed_url.path}")
                         else: raise ValueError(f"Invalid URL path structure: {parsed_url.path}")
                    url_constants = orpheus.module_settings[module_name].url_constants
                    if not url_constants: url_constants = {'track': DownloadTypeEnum.track, 'album': DownloadTypeEnum.album, 'release': DownloadTypeEnum.album, 'playlist': DownloadTypeEnum.playlist, 'artist': DownloadTypeEnum.artist}
                    type_matches = []; parsed_media_id = None
                    for i, component in enumerate(components):
                        if isinstance(component, str):
                            for url_keyword, type_enum in url_constants.items():
                                if component == url_keyword:
                                    type_matches.append(type_enum)
                                    break
                            if type_matches: break
                    if not type_matches: raise ValueError(f"Could not determine media type from URL path components: {components}")
                    media_type = type_matches[-1]
                    if len(components) > 1:
                        media_id = components[-1]                    
                    else:
                        raise ValueError(f"Could not determine media ID from URL path: {parsed_url.path}")
                if module_name == 'beatsource' and 'playlist' in components and len(components) > 2:
                    media_type = DownloadTypeEnum.playlist
                    media_id = components[-1]
                elif module_name == 'beatport' and 'chart' in components and len(components) > 2:
                    media_type = DownloadTypeEnum.playlist
                    media_id = components[-1]
                else:
                    if media_id is None or media_type is None:
                        if not components or len(components) <= 2:
                             if len(components) == 2 and components[1]: raise ValueError(f"Could not determine media type from short URL path: {parsed_url.path}")
                             else: raise ValueError(f"Invalid URL path structure: {parsed_url.path}")
                        url_constants = orpheus.module_settings[module_name].url_constants
                        if not url_constants: url_constants = {'track': DownloadTypeEnum.track, 'album': DownloadTypeEnum.album, 'release': DownloadTypeEnum.album, 'playlist': DownloadTypeEnum.playlist, 'artist': DownloadTypeEnum.artist}
                        type_matches = []; parsed_media_id = None
                        for i, component in enumerate(components):
                            if isinstance(component, str):
                                for url_keyword, type_enum in url_constants.items():
                                    if component == url_keyword:
                                        type_matches.append(type_enum)
                                        break
                                if type_matches: break
                        if not type_matches: raise ValueError(f"Could not determine media type from URL path components: {components}")
                        media_type = type_matches[-1]
                        if len(components) > 1:
                            media_id = components[-1]                        
                        else:
                            raise ValueError(f"Could not determine media ID from URL path: {parsed_url.path}")

            # Use auto-auth patcher for Tidal to handle TV login automatically
            if module_name == 'tidal':
                with TidalAutoAuthPatcher(output_queue):
                    downloader.service = orpheus.load_module(module_name)
            else:
                downloader.service = orpheus.load_module(module_name)
            downloader.service_name = module_name
            downloader.download_mode = media_type
            queue_writer.media_type = media_type
            _current_download_context = media_type
            
            yield_to_gui()
            
            is_beatport_chart = False
            
            if media_type == DownloadTypeEnum.track:
                downloader.set_indent_number(0)

                if stop_event.is_set(): is_cancelled = True
                else:
                    try:
                        yield_to_gui()
                        run_interruptible_download(
                            downloader.download_track,
                            stop_event,
                            track_id=str(media_id),
                            album_location=output_path + '/'
                        )
                        yield_to_gui()
                    except DownloadCancelledError:
                        is_cancelled = True
                        print("|GRAY|Stop requested. Cancelling during track download.|RESET|")
            elif media_type == DownloadTypeEnum.playlist:
                _current_download_context = DownloadTypeEnum.playlist
                if stop_event.is_set():
                    is_cancelled = True
                    print("|GRAY|Stop requested. Cancelling before playlist download.|RESET|")
                else:
                    try:
                        if hasattr(downloader, 'extra_kwargs') and downloader.extra_kwargs:
                            run_interruptible_download(
                                downloader.download_playlist,
                                stop_event,
                                media_id,
                                extra_kwargs=downloader.extra_kwargs
                            )
                        else:
                            run_interruptible_download(
                                downloader.download_playlist,
                                stop_event,
                                media_id
                            )
                        yield_to_gui()
                    except DownloadCancelledError:
                        is_cancelled = True
                        try:
                            print(f"=== ❌ Playlist {media_id} cancelled ===")
                        except UnicodeEncodeError:
                            print(f"=== X Playlist {media_id} cancelled ===")
                        print()
                        print("|GRAY|Stop requested. Cancelling during playlist download.|RESET|")
                    except Exception as e:
                        oprinter.oprint(f"Playlist download failed: {str(e)}")
                        download_exception_occurred = True
            elif media_type == DownloadTypeEnum.album:
                _current_download_context = DownloadTypeEnum.album
                if stop_event.is_set():
                    is_cancelled = True
                    print("|GRAY|Stop requested. Cancelling before album download.|RESET|")
                else:
                    try:
                        if hasattr(downloader, 'extra_kwargs') and downloader.extra_kwargs:
                            run_interruptible_download(
                                downloader.download_album,
                                stop_event,
                                media_id,
                                path=output_path,
                                extra_kwargs=downloader.extra_kwargs
                            )
                        else:
                            extra_kwargs = {} if downloader.service_name == 'deezer' else None
                            run_interruptible_download(
                                downloader.download_album,
                                stop_event,
                                media_id,
                                path=output_path,
                                extra_kwargs=extra_kwargs
                            )
                        yield_to_gui()
                    except DownloadCancelledError:
                        is_cancelled = True
                        try:
                            print(f"=== ❌ Album {media_id} cancelled ===")
                        except UnicodeEncodeError:
                            print(f"=== X Album {media_id} cancelled ===")
                        print()
                        print("|GRAY|Stop requested. Cancelling during album download.|RESET|")
                    except Exception as e:
                        oprinter.oprint(f"Album download failed: {str(e)}")
                        download_exception_occurred = True
            elif media_type == DownloadTypeEnum.artist:
                _current_download_context = DownloadTypeEnum.artist
                if stop_event.is_set():
                    is_cancelled = True
                    print("|GRAY|Stop requested. Cancelling before artist download.|RESET|")
                else:
                    try:
                        if hasattr(downloader, 'extra_kwargs') and downloader.extra_kwargs:
                            run_interruptible_download(
                                downloader.download_artist,
                                stop_event,
                                media_id,
                                extra_kwargs=downloader.extra_kwargs
                            )
                        else:
                            run_interruptible_download(
                                downloader.download_artist,
                                stop_event,
                                media_id
                            )
                        yield_to_gui()
                    except DownloadCancelledError:
                        is_cancelled = True
                        try:
                            print(f"=== ❌ Artist {media_id} cancelled ===")
                        except UnicodeEncodeError:
                            print(f"=== X Artist {media_id} cancelled ===")
                        print()
                        print("|GRAY|Stop requested. Cancelling during artist download.|RESET|")
                    except Exception as e:
                        oprinter.oprint(f"Artist download failed: {str(e)}")
                        download_exception_occurred = True
            elif media_type == DownloadTypeEnum.label:
                _current_download_context = DownloadTypeEnum.label
                if stop_event.is_set():
                    is_cancelled = True
                    print("|GRAY|Stop requested. Cancelling before label download.|RESET|")
                else:
                    try:
                        if hasattr(downloader, 'extra_kwargs') and downloader.extra_kwargs:
                            run_interruptible_download(
                                downloader.download_label,
                                stop_event,
                                media_id,
                                extra_kwargs=downloader.extra_kwargs
                            )
                        else:
                            run_interruptible_download(
                                downloader.download_label,
                                stop_event,
                                media_id
                            )
                        yield_to_gui()
                    except DownloadCancelledError:
                        is_cancelled = True
                        try:
                            print(f"=== ❌ Label {media_id} cancelled ===")
                        except UnicodeEncodeError:
                            print(f"=== X Label {media_id} cancelled ===")
                        print()
                        print("|GRAY|Stop requested. Cancelling during label download.|RESET|")
                    except Exception as e:
                        oprinter.oprint(f"Label download failed: {str(e)}")
                        download_exception_occurred = True
            else: print(f"ERROR: Unknown media type '{media_type.name if hasattr(media_type, 'name') else media_type}' encountered.")

            if is_cancelled: print("\nDownload Cancelled.")
        except FileNotFoundError as fnf_e:
            ffmpeg_path_setting = fresh_global_settings.get("advanced", {}).get("ffmpeg_path", "ffmpeg").strip()
            is_ffmpeg_error = False
            tb_str = traceback.format_exc()
            if "ffmpeg" in tb_str.lower():
                is_ffmpeg_error = True
            elif "ffmpeg" in str(fnf_e).lower():
                is_ffmpeg_error = True
            elif platform.system() == "Windows" and hasattr(fnf_e, 'winerror') and fnf_e.winerror == 2:
                is_ffmpeg_error = True
            elif any(phrase in str(fnf_e).lower() for phrase in ["no such file or directory", "the system cannot find the file specified", "cannot find"]):
                if hasattr(fnf_e, 'errno') and fnf_e.errno == 2:
                    is_ffmpeg_error = True
            
            if is_ffmpeg_error:
                download_exception_occurred = True
                user_msg = (
                    "\n[FFMPEG ERROR] FFmpeg was not found. This is required for audio conversion.\n\n"
                    "Possible Solutions:\n"
                    "1. Install FFmpeg: If not installed, download from ffmpeg.org and install it.\n"
                    "2. Check PATH: Ensure the directory containing ffmpeg.exe (or ffmpeg) is in your system's PATH environment variable.\n"
                    "3. Configure in GUI: Go to Settings > Global > Advanced > FFmpeg Path, and set the full path to your ffmpeg executable.\n"
                    "4. Place in App Folder: Download the FFmpeg binary and place it in the application folder or data folder.\n\n"
                    f"Current FFmpeg Path setting in GUI: '{ffmpeg_path_setting}'\n\n"
                    "Download process aborted."
                )
                print(user_msg + "\n")
            else:
                raise fnf_e

    except (DownloadCancelledError, AuthenticationError, DownloadError, NetworkError, OrpheusdlError) as e:
        download_exception_occurred = True
        if isinstance(e, DownloadCancelledError):
             is_cancelled = True; download_exception_occurred = False
             print("Download Cancelled.")
        else: error_type = type(e).__name__; print(f"\nERROR: {error_type}.\nDetails: {e}\n")
    except Exception as e:
        download_exception_occurred = True
        error_type = type(e).__name__; error_repr = repr(e)
        tb_str_generic = traceback.format_exc()
        tb_str_generic_lower = tb_str_generic.lower()

        is_soundcloud_hls_ffmpeg_issue = False
        if ("soundcloud" in tb_str_generic_lower and
            "hls_unexpected_error_in_try_block" in tb_str_generic_lower and
            "ffmpeg" in tb_str_generic_lower and
            ("[winerror 2]" in tb_str_generic_lower or
             "no such file or directory" in tb_str_generic_lower or
             "system cannot find the file specified" in tb_str_generic_lower)):
            is_soundcloud_hls_ffmpeg_issue = True

        if is_soundcloud_hls_ffmpeg_issue:
            ffmpeg_path_setting = fresh_global_settings.get("advanced", {}).get("ffmpeg_path", "ffmpeg").strip()
            user_msg = (
                "\n[FFMPEG ERROR - SoundCloud HLS] FFmpeg was not found or is misconfigured.\nThis is required for processing SoundCloud HLS streams.\n\n"
                "Possible Solutions:\n"
                "1. Install FFmpeg: If not installed, download from ffmpeg.org and install it.\n"
                "2. Check PATH: Ensure the directory containing ffmpeg.exe (or ffmpeg) is in your system's PATH environment variable.\n"
                "3. Configure in GUI: Go to Settings > Global > Advanced > FFmpeg Path, and set the full path to your ffmpeg executable.\n"
                "4. Place in App Folder: Download the FFmpeg binary and place it in the application folder or data folder.\n\n"
                f"Current FFmpeg Path setting in GUI: '{ffmpeg_path_setting}'\n\n"
                "Download process aborted."
            )
            print(user_msg + "\n")
        else:
            try:
                print(f"\nUNEXPECTED ERROR during download thread.\nType: {error_type}\nDetails: {error_repr}\nTraceback:\n{tb_str_generic}")
            except UnicodeEncodeError:
                safe_error_type = str(error_type).encode('ascii', 'replace').decode('ascii')
                safe_error_repr = str(error_repr).encode('ascii', 'replace').decode('ascii')
                safe_tb_str = str(tb_str_generic).encode('ascii', 'replace').decode('ascii')
                print(f"\nUNEXPECTED ERROR during download thread.\nType: {safe_error_type}\nDetails: {safe_error_repr}\nTraceback:\n{safe_tb_str}")
    finally:
        yielding_active.clear()
        
        end_time = datetime.datetime.now(); total_duration = end_time - start_time; formatted_time = beauty_format_seconds(total_duration.total_seconds())
        time_taken_message = f"Total time taken: {formatted_time}\n"
        if _queue_log_handler_instance and _queue_log_handler_instance._specific_ffmpeg_hls_error_logged_this_download:
            download_exception_occurred = True

        if is_cancelled:            
            pass
        else:
            final_status_message = "Download Finished.\n" 
            print(final_status_message)
        
        print(time_taken_message)
        print("\n")

        sys.stdout = original_stdout
        sys.stderr = original_stderr
        _current_download_context = None

        download_successful = not is_cancelled and not download_exception_occurred

        def final_ui_update(success=False):
            global progress_bar, stop_button, download_process_active, app, file_download_queue, current_batch_output_path, current_settings, DEFAULT_SETTINGS

            try:
                if 'progress_bar' in globals() and progress_bar and progress_bar.winfo_exists(): progress_bar.set(0)
                if 'stop_button' in globals() and stop_button and stop_button.winfo_exists(): stop_button.configure(state=tkinter.DISABLED)
                download_process_active = False
                if file_download_queue:
                    next_url = file_download_queue.pop(0)
                    print(f"Queueing next download from file: {next_url} ({len(file_download_queue)} remaining)")
                    if 'app' in globals() and app and app.winfo_exists() and current_batch_output_path:
                        app.after(100, lambda u=next_url, p=current_batch_output_path: _start_single_download(u, p, None))
                    else:
                        print("[Error] Cannot queue next download: App not available or batch path missing.")
                        set_ui_state_downloading(False)
                        file_download_queue.clear()
                        current_batch_output_path = None
                else:
                    set_ui_state_downloading(False)
                    is_batch_finish = (current_batch_output_path is not None)

                    if is_batch_finish:
                         print("File download queue is empty. Batch finished.")
                         current_batch_output_path = None
                    play_sound = False
                    try:
                        play_sound = current_settings.get("globals", {}).get("general", {}).get("play_sound_on_finish", DEFAULT_SETTINGS["globals"]["general"]["play_sound_on_finish"])
                    except Exception as setting_e: print(f"[Sound] Error reading play_sound setting: {setting_e}")

                    if play_sound:
                        sound_played = False
                        try:
                            current_platform = platform.system()
                            sound_module_available = (current_platform == "Windows" and 'winsound' in sys.modules)

                            if sound_module_available:
                                sound_alias_to_play = "SystemAsterisk" if success else "SystemHand"
                                winsound.PlaySound(sound_alias_to_play, winsound.SND_ALIAS | winsound.SND_ASYNC)
                                sound_played = True
                            elif current_platform == "Darwin":
                                sound_file = "/System/Library/Sounds/Glass.aiff" if success else "/System/Library/Sounds/Sosumi.aiff"
                                if os.path.exists(sound_file):
                                    subprocess.Popen(["afplay", sound_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                    sound_played = True
                                
                            if sound_played:
                                status_text = "completion" if success else "failure/cancellation"
                                finish_context = "Batch" if is_batch_finish else "Download"
                                print(f"[Sound] Played {finish_context} {status_text} sound ({current_platform}).")
                        except NameError:
                            print("[Sound] Sound playback skipped (winsound not available on this platform).")
                        except Exception as sound_e:
                            print(f"[Warning] Could not play completion/failure sound: {sound_e}")

            except NameError as final_ne:
                print(f"[Error] NameError during final UI update (widget missing?): {final_ne}")
                download_process_active = False; set_ui_state_downloading(False)
            except tkinter.TclError as final_tcl_e:
                 print(f"[Error] TclError during final UI update (widget destroyed?): {final_tcl_e}")
                 download_process_active = False
            except Exception as final_e:
                 print(f"[Error] Exception scheduling final UI update: {final_e}")
                 download_process_active = False; set_ui_state_downloading(False)

        try:
            if 'app' in globals() and app and app.winfo_exists():
                app.after(0, lambda s=download_successful: final_ui_update(success=s))
            else: print("[Debug] 'app' not found in finally block for UI update scheduling.")
        except NameError:
            print("[Debug] 'app' NameError in finally block.")
        except Exception as final_e:
             print(f"[Error] Exception scheduling final UI update: {final_e}")

def _start_single_download(url_to_download, output_path_final, search_result_data=None):
    """Starts the download in a separate thread for a single URL."""
    global download_process_active, current_settings, orpheus_instance, stop_event
    
    if orpheus_instance is None:
        print("Download cancelled: Orpheus instance is None.")
        try:
            if 'app' in globals() and app and app.winfo_exists():
                 show_centered_messagebox("Error", "Orpheus library not initialized.", dialog_type="error")
        except Exception: pass
        return False
    
    if download_process_active:
        print(f"Skipping start for {url_to_download}: A download is currently active.")
        return False
    
    try:
        parsed_url = urlparse(url_to_download)
        if not parsed_url.scheme in ['http', 'https'] or not parsed_url.netloc:
            show_centered_messagebox("Invalid Input", f"Input is not a valid URL or file path.\nPlease enter a valid web URL (http:// or https://) or the full path to a .txt file.", dialog_type="warning")
            return False
    except Exception as parse_e:
        show_centered_messagebox("Input Error", f"Could not process input: {url_to_download}\nError: {parse_e}\nPlease enter a valid web URL or .txt file path.", dialog_type="error")
        return False

    # Spotify: require username, client ID, and client secret before download
    if 'spotify.com' in url_to_download:
        spotify_creds = (current_settings.get("credentials") or {}).get("Spotify") or {}
        username = (spotify_creds.get("username") or "").strip()
        client_id = (spotify_creds.get("client_id") or "").strip()
        client_secret = (spotify_creds.get("client_secret") or "").strip()
        if not username or not client_id or not client_secret:
            show_centered_messagebox("Search Error", "Error during search: spotify -> Spotify credentials are required. Please fill in your username, client ID and secret in the settings.", dialog_type="warning")
            return False

    # macOS/Linux: Deno is not bundled; required for YouTube downloads. Show install pop-up if missing.
    if platform.system() in ("Darwin", "Linux") and ('youtube.com' in url_to_download or 'youtu.be' in url_to_download):
        deno_found, _ = find_system_deno()
        if not deno_found:
            try:
                if 'app' in globals() and app and app.winfo_exists():
                    app.after(0, _show_deno_install_message)
            except Exception:
                _show_deno_install_message()
            return False

    try:
        set_ui_state_downloading(True)
        stop_event.clear()
        download_process_active = True

        download_thread = threading.Thread(
            target=run_download_in_thread,
            args=(orpheus_instance, url_to_download, output_path_final, current_settings, search_result_data),
            daemon=True
        )
        print(f"Starting download thread for: {url_to_download}")
        download_thread.start()
        if platform.system() == "Windows":
            try:
                import ctypes
                from ctypes import wintypes
                thread_handle = ctypes.windll.kernel32.OpenThread(0x0002, False, download_thread.ident)
                if thread_handle:
                    ctypes.windll.kernel32.SetThreadPriority(thread_handle, -2)
                    ctypes.windll.kernel32.CloseHandle(thread_handle)
            except Exception:
                pass
        
        return True

    except Exception as e:
        print(f"Unexpected error starting download thread for {url_to_download}: {e}")
        show_centered_messagebox("Error", f"Failed to start download thread for {url_to_download}. Error: {e}", dialog_type="error")
        set_ui_state_downloading(False)
        download_process_active = False
        return False

def start_download_thread(search_result_data=None):
    """Validates inputs (URL or file path) and starts the download process(es). Queues downloads from files."""
    global download_process_active, current_settings, orpheus_instance, url_entry, path_var_main, stop_event
    global file_download_queue, current_batch_output_path

    if orpheus_instance is None:
        show_centered_messagebox("Error", "Orpheus library not initialized. Cannot start download.", dialog_type="error")
        print("Download cancelled: Orpheus instance is None.")
        return

    try:
        if 'url_entry' not in globals() or not url_entry or not url_entry.winfo_exists():
            print("Error: URL entry widget not available."); return
        if 'path_var_main' not in globals() or not path_var_main:
            print("Error: Path variable not available."); return

        input_text = url_entry.get().strip()
        if not input_text:
             show_centered_messagebox("Info", "Please enter a URL or a file path.", dialog_type="warning"); return

        output_path = path_var_main.get().strip()
        if not output_path:
            show_centered_messagebox("Info", "Please select a download path.", dialog_type="warning"); return
        output_path_final = ""
        try:
            norm_path = os.path.normpath(output_path)
            output_path_final = os.path.join(norm_path, '')
            if os.path.exists(norm_path):
                if not os.path.isdir(norm_path):
                    show_centered_messagebox("Error", f"Output path '{norm_path}' exists but is a file.", dialog_type="error"); return
            else:
                os.makedirs(norm_path, exist_ok=True)
                print(f"Created output directory: {norm_path}")
        except OSError as e:
            show_centered_messagebox("Error", f"Invalid or inaccessible output path: '{output_path}'.\nError: {e}", dialog_type="error"); return
        except Exception as e:
            show_centered_messagebox("Error", f"An unexpected error occurred validating path '{output_path}'.\nError: {e}", dialog_type="error"); return
        if os.path.exists(input_text) and os.path.isfile(input_text):
            print(f"Detected file input: {input_text}")
            file_download_queue.clear()
            current_batch_output_path = output_path_final
            urls_in_file = []
            try:
                with open(input_text, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            urls_in_file.append(line)
            except Exception as e:
                show_centered_messagebox("File Error", f"Error reading file: {input_text}\n{e}", dialog_type="error")
                current_batch_output_path = None
                return

            if not urls_in_file:
                show_centered_messagebox("Info", f"File '{input_text}' is empty or contains no valid URLs.", dialog_type="warning")
                current_batch_output_path = None
                return
            file_download_queue.extend(urls_in_file)
            print(f"Added {len(file_download_queue)} URLs to the download queue.")
            if file_download_queue:
                first_url = file_download_queue.pop(0)
                print(f"Attempting to start first download from file queue: {first_url}")
                _start_single_download(first_url, current_batch_output_path, None)
            else:
                 print("File queue was unexpectedly empty after population.")
                 current_batch_output_path = None

        else:
            file_download_queue.clear()
            current_batch_output_path = None
            print(f"Treating input as single URL: {input_text}")
            _start_single_download(input_text, output_path_final, search_result_data)

    except Exception as e:
        print(f"Unexpected error in start_download_thread: {e}")
        show_centered_messagebox("Error", f"An unexpected error occurred: {e}", dialog_type="error")
        file_download_queue.clear()
        current_batch_output_path = None

def stop_download():
    global stop_event, output_queue
    stop_event.set()
    output_queue.put("|GRAY|Download stop requested... Please wait.|RESET|\n")

# Omit ID from displaycolumns so the theme never draws a zero-width slot (avoids right-edge artifact)
_TREE_DISPLAYCOLUMNS = ("Preview", "#", "Title", "Artist", "Duration", "Year", "Additional", "Explicit")

def on_platform_change(*args):
    global platform_var
    try:
        if 'platform_var' in globals() and platform_var:
            platform = platform_var.get(); update_search_types(platform)
    except NameError: pass
    except Exception as e: print(f"Error in on_platform_change: {e}")

def update_search_types(platform):
    global type_var, type_combo
    # Only Beatport and Beatsource support label search; others get track/artist/playlist/album (or platform-specific)
    # "All" uses default types (track, artist, playlist, album) so all platforms can participate
    # Tidal: add Explore Atmos (tracks/albums) options
    platform_types = {
        "All": sorted(["track", "artist", "playlist", "album"]),
        "YouTube": ["track", "playlist", "channel"],
        "Beatport": ["track", "artist", "playlist", "album", "label"],
        "Beatsource": ["track", "artist", "playlist", "album", "label"],
        "Qobuz": ["track", "artist", "playlist", "album"],
        "Tidal": ["track", "artist", "playlist", "album", "album  ◗◖ ᴀᴛᴍᴏs", "track  ◗◖ ᴀᴛᴍᴏs", "playlist  ◗◖ ᴀᴛᴍᴏs"],
    }
    default_types = sorted(["track", "artist", "playlist", "album"])
    available_types = sorted(platform_types.get(platform, default_types))
    try:
        if 'type_var' in globals() and type_var and 'type_combo' in globals() and type_combo and type_combo.winfo_exists():
            current_type = type_var.get(); type_combo.configure(values=available_types)
            if current_type in available_types: type_var.set(current_type)
            elif "track" in available_types: type_var.set("track")
            elif available_types: type_var.set(available_types[0])
            else: type_var.set("")
    except NameError: pass
    except tkinter.TclError as e: print(f"TclError updating search types (widget destroyed?): {e}")
    except Exception as e: print(f"Error updating search types: {e}")
    _update_search_placeholder()

def _update_search_placeholder(*args):
    """Set search entry placeholder when Tidal + track/album (ATMOS) selected, else default."""
    try:
        if 'search_entry' not in globals() or not search_entry or not search_entry.winfo_exists():
            return
        if 'type_var' not in globals() or not type_var or 'platform_var' not in globals() or not platform_var:
            return
        platform = (platform_var.get() or "").strip()
        search_type = (type_var.get() or "").strip()
        # Normalize: strip emoji/pipe to get base type for comparison
        normalized_type = search_type.replace("  ◗◖ ᴀᴛᴍᴏs", " (ATMOS)").replace("  ◗◖ ᴀᴛᴍᴏs", " (ATMOS)").replace("( ◗◖ ᴀᴛᴍᴏs )", "(ATMOS)").replace("(◗◖ ᴀᴛᴍᴏs )", "(ATMOS)").replace("(◗◖ ᴀᴛᴍᴏs)", "(ATMOS)").replace("(◗◖ atmos)", "(ATMOS)").replace("(◗◖ atmos )", "(ATMOS)").replace("(◗◖atmos )", "(ATMOS)").replace("(◗◖ATMOS )", "(ATMOS)").strip()
        if platform.lower() == "tidal" and normalized_type in ("album (ATMOS)", "track (ATMOS)", "playlist (ATMOS)"):
            placeholder = "Enter search query or hit Search to explore..."
        else:
            placeholder = "Enter search query..."
        search_entry.configure(placeholder_text=placeholder)
    except (NameError, tkinter.TclError, Exception):
        pass

def clear_treeview():
    global tree, scrollbar, app
    try:
        # Cancel pending lazy_load_visible_covers to avoid stale callbacks after clear (can contribute to deadlock)
        if hasattr(on_tree_scroll, '_scheduled_id') and on_tree_scroll._scheduled_id and 'app' in globals() and app and app.winfo_exists():
            try:
                app.after_cancel(on_tree_scroll._scheduled_id)
                on_tree_scroll._scheduled_id = None
            except Exception:
                pass
        if 'tree' in globals() and tree and tree.winfo_exists():
            for item in tree.get_children(): tree.delete(item)
        if 'app' in globals() and app and app.winfo_exists() and 'tree' in globals() and tree and tree.winfo_exists() and 'scrollbar' in globals() and scrollbar and scrollbar.winfo_exists():
            app.after(0, lambda: _check_and_toggle_scrollbar(tree, scrollbar))
    except NameError: pass
    except tkinter.TclError as e: print(f"TclError clearing treeview (widget destroyed?): {e}")
    except Exception as e: print(f"Error clearing treeview: {e}")

def _update_preview_column_heading(show_expand_icon):
    """Set the Preview column header to ≡ (album/playlist/artist) or ▶ (track/tracklist)."""
    try:
        if 'tree' not in globals() or not tree or not tree.winfo_exists():
            return
        tree.heading("Preview", text="  ≡  " if show_expand_icon else " ▶ ")
    except (tkinter.TclError, Exception):
        pass

def clear_search_results_data():
     global search_results_data, selection_var, search_download_button, _expanded_album_playlist_iids
     search_results_data = []
     _expanded_album_playlist_iids.clear()
     # Clear any playing preview audio
     clear_preview_state()
     try:
        if 'selection_var' in globals() and selection_var:
            if selection_var.get() != "": selection_var.set("")
        if 'search_download_button' in globals() and search_download_button and search_download_button.winfo_exists():
            search_download_button.configure(state="disabled", text="Download")
     except NameError: pass
     except tkinter.TclError as e: print(f"TclError clearing search results data (widget destroyed?): {e}")
     except Exception as e: print(f"Error clearing search results data: {e}")

def clear_search_ui():
    global search_entry, search_progress_bar

    clear_treeview(); clear_search_results_data()
    try:
        if 'search_progress_bar' in globals() and search_progress_bar and search_progress_bar.winfo_exists():
            search_progress_bar.stop(); search_progress_bar.set(0)
    except NameError: pass
    except tkinter.TclError as e: print(f"TclError resetting search progress bar (widget destroyed?): {e}")
    except Exception as e: print(f"Error resetting search progress bar: {e}")

def display_results(results):
    global search_results_data, tree, scrollbar, app, platform_var, type_var, _album_track_list_context
    clear_treeview(); search_results_data = []
    _album_track_list_context = None  # New search: leave any album/playlist/artist view
    _update_results_header_context(None)  # Reset to "RESULTS", hide badge and Back button
    try:
        if '_back_to_search_button' in globals() and _back_to_search_button and _back_to_search_button.winfo_exists():
            _back_to_search_button.pack_forget()
    except (tkinter.TclError, Exception):
        pass
    item_number = 1
    seen_ids = set()
    has_album_or_playlist_results = False
    local_DownloadTypeEnum = DownloadTypeEnum
    try:
        current_search_type_str = type_var.get() if ('type_var' in globals() and type_var) else "track"
        current_platform_str = platform_var.get() if ('platform_var' in globals() and platform_var) else "Unknown"
    except NameError:
        current_search_type_str = "track"
        current_platform_str = "Unknown"
    except Exception as e:
        print(f"Error getting search type/platform: {e}")
        current_search_type_str = "track"
        current_platform_str = "Unknown"
    current_search_type_lower = (current_search_type_str or "track").lower()

    # Show "Label" or "Channel" instead of "Artist" only when searching by Label or YouTube Channel (not for playlist/album/track)
    try:
        if 'tree' in globals() and tree and tree.winfo_exists():
            if current_search_type_lower == "label":
                artist_col_text = "Label"
            elif current_platform_str and current_platform_str.lower() == "youtube" and current_search_type_lower == "channel":
                artist_col_text = "Channel"
            else:
                artist_col_text = "Artist"
            tree.heading("Artist", text=artist_col_text)
    except (NameError, tkinter.TclError, Exception):
        pass

    for result in results:
        res_id = result.get('id', f'sim_{item_number}')
        _y = result.get('year')
        _y = '' if _y is None or str(_y) == 'None' else str(_y)
        name = result.get('title') or ''
        artist_str = result.get('artist') or ''
        duration_str = result.get('duration') or ''
        year = _y
        explicit = result.get('explicit', '')
        additional_str = result.get('quality') or ''
        unique_tree_iid = f"item_{item_number}"
        # Per-result platform (for cover icon and API calls); fallback to current dropdown selection
        row_platform = result.get('platform') or current_platform_str
        
        # Get preview URL and cover URL from the result if available
        preview_url = result.get('preview_url', None)
        cover_url = result.get('cover_url', None)
        thumbnail_url = None  # Small/original thumbnail for fallback when full-size fails (e.g. YouTube)
        if (row_platform or '').lower() == 'youtube' and cover_url:
            thumbnail_url = cover_url
        # For YouTube, upgrade thumbnail URL to full-size if available
        if (row_platform or '').lower() == 'youtube' and cover_url:
            raw_result = result.get('raw_result')
            cover_url = _get_fullsize_cover_url(cover_url, row_platform or current_platform_str, raw_result)
        
        # Use duration_seconds when provided; otherwise parse duration string so Time column sorts (e.g. YouTube playlist/channel)
        dur_sec = result.get('duration_seconds')
        if dur_sec is None and (result.get('duration') or duration_str):
            dur_sec = _parse_duration_str_to_seconds(result.get('duration') or duration_str)
        result_type = result.get('type', current_search_type_str) or current_search_type_str
        # Normalize: strip emoji from inside parentheses if present for comparison
        normalized_result_type = result_type.replace("  ◗◖ ᴀᴛᴍᴏs", " (ATMOS)").replace("  ◗◖ ᴀᴛᴍᴏs", " (ATMOS)").replace("( ◗◖ ᴀᴛᴍᴏs )", "(ATMOS)").replace("(◗◖ ᴀᴛᴍᴏs )", "(ATMOS)").replace("(◗◖ ᴀᴛᴍᴏs)", "(ATMOS)").replace("(◗◖ atmos)", "(ATMOS)").replace("(◗◖atmos)", "(ATMOS)").replace("(◗◖ATMOS)", "(ATMOS)").strip()
        if normalized_result_type in ("track (ATMOS)", "album (ATMOS)"):
            result_type = 'track' if 'track' in normalized_result_type.lower() else 'album'
        # Hide entries that have no Time/Duration when we expect a track row
        if result_type == "track" and not duration_str and dur_sec is None:
            continue
        result_entry = {
            "id": res_id, "number": str(item_number), "title": name,
            "artist": artist_str, "duration": duration_str, "year": year,
            "additional": additional_str, "explicit": explicit,
            "platform": row_platform, "type": result_type,
            "raw_result": result.get('raw_result'),
            "tree_iid": unique_tree_iid,
            "preview_url": preview_url,
            "cover_url": cover_url,
            "duration_seconds": dur_sec
        }
        if thumbnail_url:
            result_entry["thumbnail_url"] = thumbnail_url
        if current_search_type_lower == "artist":
            result_entry["title"] = ""
            result_entry["artist"] = name
            result_entry["is_artist"] = True
        if current_search_type_lower == "label":
            result_entry["title"] = ""
            result_entry["artist"] = artist_str or name  # Label name in Label column only
        if current_search_type_lower in ("album", "playlist"):
            result_entry["is_album_playlist"] = True
            has_album_or_playlist_results = True
        # Tidal explore (and per-result type): album/playlist rows get ≡ to open track list; track rows get ▶ and lazy-load preview
        if result_type == "album":
            result_entry["is_album_playlist"] = True
            has_album_or_playlist_results = True
        if result_type == "playlist":
            result_entry["is_album_playlist"] = True
            has_album_or_playlist_results = True
        # YouTube channel: expand to show channel's videos (uploads)
        if current_platform_str.lower() == "youtube" and current_search_type_lower == "channel":
            result_entry["is_album_playlist"] = True
        # Beatport/Beatsource label: expand to show releases and tracks
        if current_search_type_lower == "label":
            result_entry["is_album_playlist"] = True
            if result.get("label_slug"):
                result_entry["label_slug"] = result.get("label_slug")

        search_results_data.append(result_entry)

        try:
            if 'tree' in globals() and tree and tree.winfo_exists():
                # Preview icon: ▶ for play (or lazy-load), ≡ for expand (album/playlist/artist)
                # Use result_type so Tidal Explore track rows get ▶ and album rows get ≡
                is_track_row = (current_search_type_str.lower() == "track") or (result_type == "track")
                is_album_playlist_row = (current_search_type_lower in ("album", "playlist") or ((row_platform or '').lower() == "youtube" and current_search_type_lower == "channel") or current_search_type_lower == "label") or (result_type == "album") or (result_type == "playlist")
                is_artist_row = current_search_type_lower == "artist"
                can_lazy_load_preview = ((row_platform or '').lower() in ('qobuz', 'soundcloud', 'spotify', 'tidal')) and is_track_row
                is_youtube_track = ((row_platform or '').lower() == 'youtube') and is_track_row
                preview_icon = (PREVIEW_EXPAND_COLLAPSED if (is_album_playlist_row or is_artist_row) else
                    (PREVIEW_PLAY_ICON if (preview_url or can_lazy_load_preview or is_youtube_track) else PREVIEW_UNAVAILABLE))
                
                if current_search_type_lower in ("artist", "label"):
                    values = (
                        preview_icon,
                        str(item_number),
                        "",
                        result_entry["artist"],
                        "",
                        "",
                        additional_str,
                        explicit,
                        res_id
                    )
                else:
                    values = (
                        preview_icon,
                        str(item_number),
                        name,
                        artist_str,
                        duration_str,
                        year,
                        additional_str,
                        explicit,
                        res_id
                    )
                
                # Insert item without image - cover will be lazy loaded when visible
                # Alternating row bg: odd rows (1,3,5) = #222222, even rows (2,4,6) = default
                row_tag = "oddrow" if (item_number % 2 == 1) else "evenrow"
                tree.insert("", "end", iid=unique_tree_iid, values=values, tags=(row_tag,))
                
                item_number += 1
                seen_ids.add(res_id)
                
                # Keep UI responsive during result display (update every 5 items)
                if item_number % 5 == 0 and 'app' in globals() and app and app.winfo_exists():
                    try:
                        app.update_idletasks()
                    except:
                        pass
            else:
                break
        except NameError: break
        except tkinter.TclError as e: 
            if not getattr(sys, 'frozen', False):
                print(f"TclError inserting into treeview (widget destroyed?): {e}", file=sys.__stderr__)
                print(f"[GUI Debug] Failed to insert item {item_number} with iid '{unique_tree_iid}' and res_id '{res_id}'", file=sys.__stderr__)
            break
        except Exception as e: 
            if not getattr(sys, 'frozen', False):
                print(f"Error inserting into treeview: {e}", file=sys.__stderr__)
    
    _update_preview_column_heading(has_album_or_playlist_results or current_search_type_lower in ("album", "playlist", "artist", "label") or (current_platform_str.lower() == "youtube" and current_search_type_lower == "channel"))
    try:
        if 'app' in globals() and app and app.winfo_exists() and 'tree' in globals() and tree and tree.winfo_exists() and 'scrollbar' in globals() and scrollbar and scrollbar.winfo_exists():
            app.after(50, lambda: _check_and_toggle_scrollbar(tree, scrollbar))
    except NameError: pass
    except Exception as e: 
        if not getattr(sys, 'frozen', False):
            print(f"Error scheduling scrollbar check after display: {e}")
    
    # Trigger lazy loading for visible covers after a short delay
    try:
        if 'app' in globals() and app and app.winfo_exists():
            app.after(100, lazy_load_visible_covers)
    except:
        pass

TIDAL_EXPLORE_TYPES = ("track (ATMOS)", "album (ATMOS)", "playlist (ATMOS)", "album  ◗◖ ᴀᴛᴍᴏs", "track  ◗◖ ᴀᴛᴍᴏs", "playlist  ◗◖ ᴀᴛᴍᴏs")

def _result_has_dolby_atmos(quality_str, raw_result):
    """True if the result is Dolby Atmos (from quality string or raw Tidal audioModes)."""
    if quality_str and 'Dolby Atmos' in str(quality_str):
        return True
    if isinstance(raw_result, dict) and 'DOLBY_ATMOS' in (raw_result.get('audioModes') or []):
        return True
    return False

def _run_single_platform_search(orpheus, platform_name, search_type_str, query, search_limit, output_queue=None):
    """Run search on one platform. Returns (list of formatted result dicts, error_message or None)."""
    local_DownloadTypeEnum = DownloadTypeEnum
    # Normalize ATMOS type for branching (e.g., "album  ◗◖ ᴀᴛᴍᴏs" → "album (ATMOS)")
    normalized_type = search_type_str.replace("  ◗◖ ᴀᴛᴍᴏs", " (ATMOS)").replace("( ◗◖ ᴀᴛᴍᴏs )", "(ATMOS)").replace("(◗◖ ᴀᴛᴍᴏs )", "(ATMOS)").replace("(◗◖ ᴀᴛᴍᴏs)", "(ATMOS)").replace("(◗◖ atmos)", "(ATMOS)").replace("(◗◖ atmos )", "(ATMOS)").replace("(◗◖atmos )", "(ATMOS)").replace("(◗◖ATMOS )", "(ATMOS)").strip() if search_type_str else ""
    is_tidal_atmos = platform_name and platform_name.lower() == 'tidal' and search_type_str in TIDAL_EXPLORE_TYPES
    query_stripped = (query or "").strip()

    # Tidal ATMOS with a search query: run normal search by base type, then filter to Dolby Atmos only
    if is_tidal_atmos and query_stripped:
        explore_map = {"track (ATMOS)": "track", "album (ATMOS)": "album", "playlist (ATMOS)": "playlist"}
        base_type = explore_map.get(normalized_type)
        if base_type is None:
            return [], f"Unsupported Tidal explore type: {normalized_type}"
        search_type_map = {"track": local_DownloadTypeEnum.track, "album": local_DownloadTypeEnum.album, "playlist": local_DownloadTypeEnum.playlist}
        query_type = search_type_map.get(base_type)
        # For playlist ATMOS, search for "dolby " + user query so results are Dolby-related playlists
        search_query = ("dolby " + query_stripped) if base_type == 'playlist' else query_stripped
        try:
            if output_queue:
                with TidalAutoAuthPatcher(output_queue):
                    module_instance = orpheus.load_module(platform_name.lower())
            else:
                module_instance = orpheus.load_module(platform_name.lower())
            search_results = module_instance.search(query_type, search_query, limit=search_limit)
        except Exception as e:
            return [], f"Error during search ({platform_name}): {str(e)}"
        formatted_results = []
        for result in search_results:
            raw_result = None
            extra_kwargs = getattr(result, 'extra_kwargs', {}) or {}
            if isinstance(extra_kwargs, dict):
                raw_result = extra_kwargs.get('raw_result')
                if raw_result is None and isinstance(extra_kwargs.get('data'), dict):
                    data = extra_kwargs['data']
                    rid = str(getattr(result, 'result_id', ''))
                    raw_result = data.get(rid) or data.get(int(rid)) if rid.isdigit() else None
                    if raw_result is None and data:
                        raw_result = next(iter(data.values()))
            if raw_result is None:
                raw_result = result
            quality_str = ', '.join([str(q) for q in getattr(result, 'additional', []) or []]) or ''
            # Playlists don't have audioModes; only filter by Atmos for tracks/albums
            if base_type != 'playlist' and not _result_has_dolby_atmos(quality_str, raw_result):
                continue
            cover_url = getattr(result, 'image_url', None)
            _yr = getattr(result, 'year', None)
            _yr_str = '' if _yr is None or str(_yr) == 'None' else str(_yr)
            raw_duration_seconds = getattr(result, 'duration', None)
            if raw_duration_seconds is not None and isinstance(raw_duration_seconds, str):
                raw_duration_seconds = _parse_duration_str_to_seconds(raw_duration_seconds)
            try:
                raw_duration_seconds = int(raw_duration_seconds) if raw_duration_seconds is not None else None
            except (TypeError, ValueError):
                raw_duration_seconds = None
            result_type = base_type
            formatted_result = {
                'id': str(getattr(result, 'result_id', '')),
                'title': str(getattr(result, 'name', '') or ''),
                'artist': ', '.join([str(a) for a in getattr(result, 'artists', []) or []]) or '',
                'duration': beauty_format_seconds(raw_duration_seconds) if raw_duration_seconds is not None else '',
                'duration_seconds': raw_duration_seconds,
                'year': _yr_str,
                'quality': quality_str,
                'explicit': '🅴' if getattr(result, 'explicit', False) else '',
                'preview_url': getattr(result, 'preview_url', None),
                'cover_url': cover_url,
                'raw_result': raw_result,
                'platform': platform_name,
                'type': result_type,
            }
            formatted_results.append(formatted_result)
        return formatted_results, None

    # Tidal explore: browse Dolby Atmos by format (no query) – only show Atmos items
    if is_tidal_atmos and not query_stripped:
        explore_map = {
            "track (ATMOS)": ("atmos", "tracks"),
            "album (ATMOS)": ("atmos", "albums"),
            "playlist (ATMOS)": ("atmos", "playlists"),
        }
        format_name, content_type = explore_map.get(normalized_type, (None, None))
        if format_name is None:
            return [], f"Unsupported Tidal explore type: {normalized_type}"
        try:
            if output_queue:
                with TidalAutoAuthPatcher(output_queue):
                    module_instance = orpheus.load_module(platform_name.lower())
            else:
                module_instance = orpheus.load_module(platform_name.lower())
            search_results = module_instance.explore(format_name, content_type, limit=search_limit)
        except Exception as e:
            return [], f"Error during explore ({platform_name}): {str(e)}"
        formatted_results = []
        for result in search_results:
            extra_kwargs = getattr(result, 'extra_kwargs', {}) or {}
            media_type = extra_kwargs.get('media_type')
            result_type = (media_type.name.lower() if media_type and hasattr(media_type, 'name') else content_type.rstrip('s'))
            raw_result = extra_kwargs.get('raw_result', result)
            quality_str = ', '.join([str(q) for q in getattr(result, 'additional', []) or []]) or ''
            # Playlists don't have audioModes; only filter by Atmos for tracks/albums
            if content_type != 'playlists' and not _result_has_dolby_atmos(quality_str, raw_result):
                continue
            cover_url = getattr(result, 'image_url', None)
            _yr = getattr(result, 'year', None)
            _yr_str = '' if _yr is None or str(_yr) == 'None' else str(_yr)
            raw_duration_seconds = getattr(result, 'duration', None)
            if raw_duration_seconds is not None and isinstance(raw_duration_seconds, str):
                raw_duration_seconds = _parse_duration_str_to_seconds(raw_duration_seconds)
            try:
                raw_duration_seconds = int(raw_duration_seconds) if raw_duration_seconds is not None else None
            except (TypeError, ValueError):
                raw_duration_seconds = None
            formatted_result = {
                'id': str(getattr(result, 'result_id', '')),
                'title': str(getattr(result, 'name', '') or ''),
                'artist': ', '.join([str(a) for a in getattr(result, 'artists', []) or []]) or '',
                'duration': beauty_format_seconds(raw_duration_seconds) if raw_duration_seconds is not None else '',
                'duration_seconds': raw_duration_seconds,
                'year': _yr_str,
                'quality': quality_str,
                'explicit': '🅴' if getattr(result, 'explicit', False) else '',
                'preview_url': getattr(result, 'preview_url', None),
                'cover_url': cover_url,
                'raw_result': raw_result,
                'platform': platform_name,
                'type': result_type,
            }
            formatted_results.append(formatted_result)
        return formatted_results, None

    search_type_map = {"track": local_DownloadTypeEnum.track, "album": local_DownloadTypeEnum.album, "artist": local_DownloadTypeEnum.artist, "playlist": local_DownloadTypeEnum.playlist, "channel": local_DownloadTypeEnum.artist, "label": local_DownloadTypeEnum.label}
    query_type = search_type_map.get((search_type_str or "").lower())
    if not query_type:
        return [], f"Invalid search type: {search_type_str}"
    try:
        if platform_name.lower() == 'tidal' and output_queue:
            with TidalAutoAuthPatcher(output_queue):
                module_instance = orpheus.load_module(platform_name.lower())
        else:
            module_instance = orpheus.load_module(platform_name.lower())
        search_results = module_instance.search(query_type, query, limit=search_limit)
    except Exception as e:
        return [], f"Error during search ({platform_name}): {str(e)}"
    formatted_results = []
    for result in search_results:
        if search_type_str and search_type_str.lower() in ('album', 'playlist'):
            addl = getattr(result, 'additional', None) or []
            if '0 tracks' in addl:
                continue
        raw_result = None
        extra_kwargs = getattr(result, 'extra_kwargs', {})
        if isinstance(extra_kwargs, dict):
            raw_result = extra_kwargs.get('raw_result')
            if raw_result is None and isinstance(extra_kwargs.get('data'), dict):
                data = extra_kwargs['data']
                rid = getattr(result, 'result_id', '')
                rid_str = str(rid)
                raw_result = data.get(rid) or data.get(rid_str) or (data.get(int(rid)) if (rid_str.isdigit()) else None)
                if raw_result is None and data:
                    raw_result = next(iter(data.values()))
        if raw_result is None:
            raw_result = result
        cover_url = getattr(result, 'image_url', None)
        if platform_name.lower() == 'youtube' and cover_url:
            cover_url = _get_fullsize_cover_url(cover_url, platform_name, raw_result)
        _yr = getattr(result, 'year', None)
        _yr_str = '' if _yr is None or str(_yr) == 'None' else str(_yr)
        raw_duration_seconds = getattr(result, 'duration', None)
        if raw_duration_seconds is not None:
            if isinstance(raw_duration_seconds, str):
                raw_duration_seconds = _parse_duration_str_to_seconds(raw_duration_seconds)
            try:
                raw_duration_seconds = int(raw_duration_seconds) if raw_duration_seconds is not None else None
            except (TypeError, ValueError):
                raw_duration_seconds = None
        _name = str(getattr(result, 'name', '') or '')
        _artists_str = ', '.join([str(a) for a in getattr(result, 'artists', []) or []]) or ''
        quality_str = ', '.join([str(q) for q in getattr(result, 'additional', []) or []]) or ''
        if not quality_str and search_type_str and search_type_str.lower() in ('album', 'playlist') and raw_result and isinstance(raw_result, dict):
            t = (raw_result.get('tracks') or {}).get('total')
            if t is not None and t > 0:
                quality_str = "1 track" if t == 1 else f"{t} tracks"
            else:
                tc = (raw_result.get('attributes') or {}).get('trackCount')
                if tc is not None and tc > 0:
                    quality_str = "1 track" if tc == 1 else f"{tc} tracks"
        formatted_result = {
            'id': str(getattr(result, 'result_id', '')),
            'title': _name,
            'artist': _artists_str,
            'duration': beauty_format_seconds(raw_duration_seconds) if raw_duration_seconds is not None else '',
            'duration_seconds': raw_duration_seconds,
            'year': _yr_str,
            'quality': quality_str,
            'explicit': '🅴' if getattr(result, 'explicit', False) else '',
            'preview_url': getattr(result, 'preview_url', None),
            'cover_url': cover_url,
            'raw_result': raw_result,
            'platform': platform_name,
            'type': (search_type_str or 'track').lower(),
        }
        if search_type_str and search_type_str.lower() == 'label':
            formatted_result['title'] = ''
            formatted_result['artist'] = _name
        if isinstance(extra_kwargs, dict) and extra_kwargs.get('label_slug'):
            formatted_result['label_slug'] = extra_kwargs['label_slug']
        formatted_results.append(formatted_result)
    return formatted_results, None


def _relevance_score(query, result):
    """Score how well a result matches the search query (higher = better match). Used to sort by best match."""
    if not query or not isinstance(result, dict):
        return 0.0
    q = query.lower().strip()
    title = (result.get('title') or '').lower().strip()
    artist = (result.get('artist') or '').lower().strip()
    combined = f"{title} {artist}"
    score = 0.0
    if q == title:
        score += 1000.0
    elif q in title:
        score += 500.0
    elif title and title in q:
        score += 300.0
    elif q in combined:
        score += 200.0
    q_words = [w for w in q.replace('-', ' ').split() if len(w) > 1]
    for w in q_words:
        if w in title:
            score += 20.0
        if w in artist:
            score += 5.0
    if title.startswith(q[:min(len(q), 20)].strip()) or q.startswith(title[:min(len(title), 20)].strip()):
        score += 50.0
    return score


def _sort_results_by_relevance(query, results):
    """Sort results list in place by relevance to query (best match first)."""
    if not query or not results:
        return
    results.sort(key=lambda r: _relevance_score(query, r), reverse=True)


def run_search_all_platforms_target(orpheus, platforms_list, search_type_str, query, gui_settings):
    """Run search on all given platforms and merge results; update UI on main thread."""
    global search_process_active, app, output_queue
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    dummy_stderr = DummyStderr()
    queue_writer = QueueWriter(output_queue) if output_queue else None
    if queue_writer:
        sys.stdout = queue_writer
        sys.stderr = dummy_stderr
    try:
        search_limit = gui_settings.get("globals", {}).get("general", {}).get("search_limit", 25)
        try:
            search_limit = int(search_limit)
        except (ValueError, TypeError):
            search_limit = 25
        _search_all_timeout_sec = 60  # per platform; avoids infinite hang if one platform blocks (e.g. Tidal auth)
        combined = []
        for platform_name in platforms_list:
            out = []
            def _one_platform():
                r, e = _run_single_platform_search(orpheus, platform_name, search_type_str, query, search_limit, output_queue)
                out.append((r, e))
            t = threading.Thread(target=_one_platform, daemon=True)
            t.start()
            t.join(timeout=_search_all_timeout_sec)
            if t.is_alive():
                # Platform did not return in time (e.g. Tidal waiting for login) – skip it
                results, err = [], f"{platform_name} timed out (skipped)"
            else:
                results, err = out[0] if out else ([], "No result")
            if err and not results:
                continue  # Skip platform on error, continue with others
            for r in results:
                r['platform'] = platform_name
                combined.append(r)
        def _update_ui():
            global search_process_active
            if '_clear_expand_long_loading_message' in globals() and callable(_clear_expand_long_loading_message):
                _clear_expand_long_loading_message()
            if '_expand_loading_message_prefix' in globals():
                globals()["_expand_loading_message_prefix"] = "Fetching all data"
            set_ui_state_searching(False)
            search_process_active = False
            if not combined:
                show_centered_messagebox("No Results", "The search completed successfully, but found no results matching your query on any platform.", dialog_type="info")
                display_results([])
            else:
                _sort_results_by_relevance(query, combined)
                display_results(combined)
        if app and app.winfo_exists():
            app.after(0, _update_ui)
        else:
            search_process_active = False
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr


def run_search_thread_target(orpheus, platform_name, search_type_str, query, gui_settings):
    """Runs the search using the provided global Orpheus instance."""
    global search_process_active, app, output_queue, DEFAULT_SETTINGS
    local_DownloadTypeEnum = DownloadTypeEnum

    # Redirect stdout/stderr to QueueWriter to handle frozen apps and capture auth output
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    dummy_stderr = DummyStderr()
    queue_writer = QueueWriter(output_queue)
    
    # Always redirect stdout to QueueWriter for proper Tidal TV auth handling
    sys.stdout = queue_writer
    sys.stderr = dummy_stderr

    # Initialize these before try block so finally can access them
    results = []
    error_message = None
    early_return = False

    try:
        if orpheus is None:
            if 'output_queue' in globals() and output_queue:
                output_queue.put("ERROR: Orpheus instance not available. Cannot start search.\n")
            try:
                if 'app' in globals() and app and app.winfo_exists():
                    app.after(0, lambda: set_ui_state_searching(False))
            except NameError: pass
            except Exception: pass
            early_return = True
            return
        search_limit = gui_settings.get("globals", {}).get("general", {}).get("search_limit", 25)
        try: search_limit = int(search_limit)
        except (ValueError, TypeError): search_limit = 25
        results, error_message = _run_single_platform_search(orpheus, platform_name, search_type_str, query, search_limit, output_queue)
        if results:
            error_message = None
    except Exception as e:
        error_message = f"Error during search: {str(e)}"
        results = []
    finally:
        # Restore original stdout/stderr
        sys.stdout = original_stdout
        sys.stderr = original_stderr

        # Skip UI update if we returned early (e.g., orpheus was None)
        if early_return:
            return

        def _update_ui():
            global search_process_active
            if '_clear_expand_long_loading_message' in globals() and callable(_clear_expand_long_loading_message):
                _clear_expand_long_loading_message()
            if '_expand_loading_message_prefix' in globals():
                globals()["_expand_loading_message_prefix"] = "Fetching all data"
            if error_message: 
                set_ui_state_searching(False)
                show_centered_messagebox("Search Error", error_message, dialog_type="error"); clear_treeview(); clear_search_results_data()
            elif not results: 
                set_ui_state_searching(False)
                show_centered_messagebox("No Results", "The search completed successfully, but found no results matching your query.", dialog_type="info"); display_results([])
            else: 
                _sort_results_by_relevance(query, results)
                display_results(results)
                set_ui_state_searching(False)  # Stop progress bar AFTER results are displayed
            search_process_active = False
        try:
            if 'app' in globals() and app and app.winfo_exists():
                app.after(0, _update_ui)
            else:
                search_process_active = False
        except NameError:
            search_process_active = False
        except Exception:
            search_process_active = False

def start_search():
    """Validates input and starts the search process in a separate thread using the global Orpheus instance."""
    global search_process_active, current_settings, orpheus_instance, search_entry, platform_var, type_var, installed_platform_keys

    if orpheus_instance is None:
        show_centered_messagebox("Error", "Orpheus library not initialized. Cannot start search.", dialog_type="error")
        print("Search cancelled: Orpheus instance is None.")
        return

    try:
        if 'search_entry' not in globals() or not search_entry or not search_entry.winfo_exists(): print("Error: Search entry widget not available."); return
        if 'platform_var' not in globals() or not platform_var: print("Error: Platform variable not available."); return
        if 'type_var' not in globals() or not type_var: print("Error: Type variable not available."); return

        query = search_entry.get().strip(); platform_name = platform_var.get(); search_type_str = type_var.get()
        is_tidal_explore = platform_name and platform_name.lower() == 'tidal' and search_type_str in TIDAL_EXPLORE_TYPES
        if not query and not is_tidal_explore: show_centered_messagebox("Info", "Please enter a search query.", dialog_type="warning"); return
        if not platform_name: show_centered_messagebox("Info", "Please select a platform.", dialog_type="warning"); return
        if not search_type_str: show_centered_messagebox("Info", "Please select a search type.", dialog_type="warning"); return
        if search_process_active: show_centered_messagebox("Busy", "A search is already in progress!", dialog_type="warning"); return
        # Spotify: require username, client ID, and client secret before search/download (single-platform only)
        if platform_name == "Spotify":
            spotify_creds = (current_settings.get("credentials") or {}).get("Spotify") or {}
            username = (spotify_creds.get("username") or "").strip()
            client_id = (spotify_creds.get("client_id") or "").strip()
            client_secret = (spotify_creds.get("client_secret") or "").strip()
            if not username or not client_id or not client_secret:
                show_centered_messagebox("Search Error", "Error during search: spotify -> Spotify credentials are required. Please fill in your username, client ID and secret in the settings.", dialog_type="warning")
                return

        clear_search_ui()
        set_ui_state_searching(True)
        search_process_active = True
        if platform_name == "All":
            platforms_list = get_searchable_platforms(current_settings, installed_platform_keys or [], get_data_directory() or application_path)
            if not platforms_list:
                set_ui_state_searching(False)
                search_process_active = False
                show_centered_messagebox("No Platforms", "No platforms are configured for search. Add credentials (or cookies for Apple Music) for at least one platform in Settings.", dialog_type="warning")
                return
            globals()["_expand_loading_message_prefix"] = "Searching all platforms"
            if 'app' in globals() and app and app.winfo_exists():
                globals()["_expand_long_loading_after_id"] = app.after(8000, _show_expand_long_loading_message)
            search_thread = threading.Thread(target=run_search_all_platforms_target, args=(orpheus_instance, platforms_list, search_type_str, query, current_settings), daemon=True)
        else:
            # Tidal Dolby Atmos search (with or without query) can take a while; show "Fetching all data..." after 8s
            if platform_name and platform_name.strip().lower() == 'tidal' and search_type_str in TIDAL_EXPLORE_TYPES:
                globals()["_expand_loading_message_prefix"] = "Fetching all data"
                if 'app' in globals() and app and app.winfo_exists():
                    globals()["_expand_long_loading_after_id"] = app.after(8000, _show_expand_long_loading_message)
            search_thread = threading.Thread(target=run_search_thread_target, args=(orpheus_instance, platform_name, search_type_str, query, current_settings), daemon=True)
        search_thread.start()
    except NameError as e:
        print(f"Error starting search (widgets not ready?): {e}")
        search_process_active = False
    except Exception as e:
        print(f"Unexpected error in start_search: {e}")
        set_ui_state_searching(False)
        search_process_active = False

def on_tree_select(event):
    global tree, search_results_data, selection_var, search_download_button
    try:
        if 'tree' not in globals() or not tree or not tree.winfo_exists(): return
        if 'selection_var' not in globals() or not selection_var: return
        if 'search_download_button' not in globals() or not search_download_button or not search_download_button.winfo_exists(): return

        selection = tree.selection()
        if selection:
            selected_count = len(selection)
            if selected_count == 1:
                selected_iid = selection[0]
                selected_item_data = next((item for item in search_results_data if str(item.get('tree_iid')) == str(selected_iid)), None)
                if selected_item_data: 
                    selection_var.set(selected_item_data['number'])
                    search_download_button.configure(state="normal", text="Download")
                else: 
                    print(f"Selected iid {selected_iid} not found in search_results_data.")
                    selection_var.set("")
                    search_download_button.configure(state="disabled", text="Download")
            else:
                selected_numbers = []
                for selected_iid in selection:
                    selected_item_data = next((item for item in search_results_data if str(item.get('tree_iid')) == str(selected_iid)), None)
                    if selected_item_data:
                        selected_numbers.append(selected_item_data['number'])
                try:
                    selected_numbers.sort(key=int)
                except ValueError:
                    pass
                
                selection_var.set(",".join(selected_numbers))
                search_download_button.configure(state="normal", text=f"Download {selected_count} IDs")
        else: 
            selection_var.set("")
            search_download_button.configure(state="disabled", text="Download")
    except NameError: pass
    except tkinter.TclError as e: print(f"TclError in tree select (widget destroyed?): {e}")
    except Exception as e: print(f"Error in tree select: {e}")

def on_selection_change(*args):
    global selection_var, search_results_data, search_download_button, selection_entry
    try:
        if 'selection_var' not in globals() or not selection_var: return
        if 'search_download_button' not in globals() or not search_download_button or not search_download_button.winfo_exists(): return

        selection_str = selection_var.get().strip()
        
        # Dynamic resizing of the selection entry
        if 'selection_entry' in globals() and selection_entry and selection_entry.winfo_exists():
            # Base width 35, approx 7-8 pixels per character
            # Cap at a reasonable max width if needed, or let it grow
            # Using 8px per char as a heuristic for the font
            new_width = max(35, len(selection_str) * 8)
            # Optional: Cap max width to prevent UI breaking, e.g., 400
            new_width = min(new_width, 400) 
            try:
                selection_entry.configure(width=new_width)
            except Exception:
                pass

        if not selection_str: 
            search_download_button.configure(state="disabled", text="Download")
            return
        if "," in selection_str:
            # Multi-selection logic is handled in on_tree_select, but we still need to enable button if valid
            # If it contains commas, it's likely a list of IDs.
            # We assume it's valid if it came from the tree selection.
            # If user manually typed it, we might want to validate, but for now let's trust the flow or just check basic format.
            # The original code returned here, disabling the button update logic below for single items.
            # But we need to ensure the button is enabled for multi-selection.
            # The button text is updated in on_tree_select, so we might just want to return or ensure state is normal.
            # However, if user types manually "1, 2", we might want to handle it.
            # For now, preserving original behavior of returning, but ensuring button state if needed?
            # Actually, on_tree_select sets the button text and state. 
            # This callback is triggered by the var change. 
            # If on_tree_select set the var, this runs.
            # If on_tree_select ALREADY set the button state/text, we shouldn't overwrite it with "Download" (single) logic.
            return

        try:
            selection_num = int(selection_str)
            matching_item = next((item for item in search_results_data if item.get('number') == str(selection_num)), None)
            search_download_button.configure(state="normal" if matching_item else "disabled", text="Download")
        except ValueError:
            search_download_button.configure(state="disabled", text="Download")
            
    except NameError: pass
    except tkinter.TclError as e: print(f"TclError in selection change (widget destroyed?): {e}")
    except Exception as e:
        print(f"Error in selection change validation: {e}")
        if 'search_download_button' in globals() and search_download_button and search_download_button.winfo_exists():
            search_download_button.configure(state="disabled", text="Download")

def get_selected_item_data():
    global selection_var, search_results_data
    try:
        if 'selection_var' not in globals() or not selection_var: return None

        selection_num_str = selection_var.get().strip()
        if not selection_num_str: return None
        selection_num = int(selection_num_str)
        return next((item for item in search_results_data if item.get('number') == str(selection_num)), None)
    except NameError: return None
    except (ValueError, Exception): return None

def get_selected_items_data():
    """Get data for all currently selected items in the tree."""
    global tree, search_results_data
    try:
        if 'tree' not in globals() or not tree or not tree.winfo_exists(): return []
        if 'search_results_data' not in globals() or not search_results_data: return []

        selection = tree.selection()
        if not selection: return []
        
        selected_items = []
        for selected_iid in selection:
            selected_item_data = next((item for item in search_results_data if str(item.get('tree_iid')) == str(selected_iid)), None)
            if selected_item_data:
                selected_items.append(selected_item_data)
            else:
                print(f"Selected iid {selected_iid} not found in search_results_data.")
        
        return selected_items
    except NameError: return []
    except Exception as e: 
        print(f"Error getting selected items data: {e}")
        return []

# Search Results Context Menu
_search_context_menu = None
_search_context_menu_wrapper = None  # Wrapper with padx/pady=1 so frame border isn't clipped (like artwork menu)
_search_context_menu_bottom_label = None  # "No other formats available" for SoundCloud/Apple Music
_search_context_menu_app_binding_id = None   # So we can unbind only our Button-1 handler (left-click to dismiss)
_search_context_menu_tree_binding_id = None  # Tree ButtonRelease-1 so release on another row dismisses (avoids competing with tree Button-1 on macOS)
_search_quality_menu = None
_search_context_quality_var = None
_search_quality_buttons = []  # List to store quality button references
_search_copy_url_button = None # Reference to the open URL button (opens link in external browser)

def _create_search_context_menu():
    """Create the search results right-click context menu."""
    global _search_context_menu, _search_context_menu_wrapper, _search_context_menu_bottom_label, _search_quality_menu, _search_context_quality_var, _search_quality_buttons, _search_copy_url_button, app, BUTTON_COLOR
    
    if _search_context_menu is not None:
        return
    
    if 'app' not in globals() or not app:
        return
    
    try:
        # Wrapper: fixed width; menu frame and spacer also fixed width so menu doesn't grow
        _search_context_menu_wrapper = customtkinter.CTkFrame(app, fg_color="transparent", width=CONTEXT_MENU_WIDTH)
        # Main context menu frame - fixed width; rounded corners
        _search_context_menu = customtkinter.CTkFrame(_search_context_menu_wrapper, border_width=1, border_color="#565B5E", fg_color=TOOLTIP_MENU_BG, width=CONTEXT_MENU_WIDTH)
        _search_context_menu.configure(cursor=HAND_CURSOR)
        button_color = TOOLTIP_MENU_BG
        
        # Open URL button - same style as copy/paste buttons (icon color = text color)
        external_link_icon = _create_external_link_icon(color=CONTEXT_MENU_TEXT_COLOR)
        _search_copy_url_button = customtkinter.CTkButton(
            _search_context_menu, 
            text="Link", 
            image=external_link_icon,
            compound="left",
            command=_open_selected_url,
            width=100,
            height=24,
            font=("Segoe UI", 11),
            fg_color=button_color,
            hover_color="#1F6AA5",
            text_color=CONTEXT_MENU_TEXT_COLOR,
            text_color_disabled=CONTEXT_MENU_TEXT_DISABLED,
            border_width=0,
            anchor="w"
        )
        _search_copy_url_button.image = external_link_icon  # Keep reference
        _search_copy_url_button.pack(pady=(2, 1), padx=2, fill="x")
        
        # Separator line (slightly lighter than menu bg so it's visible)
        separator = customtkinter.CTkFrame(_search_context_menu, width=50, height=2, fg_color="#2B2B2B")
        separator.pack(fill="x", padx=2, pady=2)
        
        # Quality options as buttons (like a submenu)
        # Create 4 buttons to support platforms like TIDAL that have 4 quality tiers
        _search_context_quality_var = tkinter.StringVar(value="hifi")

        quality_options = [
            ("Lossless", "hifi"),
            ("High Quality", "high"),
            ("Low Quality", "low"),
            ("Low Quality", "low")  # 4th button for TIDAL (will be reconfigured dynamically)
        ]
        
        _search_quality_buttons.clear()  # Clear any existing button references
        for i, (label, value) in enumerate(quality_options):
            btn = customtkinter.CTkButton(
                _search_context_menu,
                text=label,
                command=lambda v=value: _select_quality_and_download(v),
                width=100,
                height=24,
                font=("Segoe UI", 11),
                fg_color=button_color,
                hover_color="#1F6AA5",
                text_color=CONTEXT_MENU_TEXT_COLOR,
                text_color_disabled=CONTEXT_MENU_TEXT_DISABLED,
                border_width=0,
                anchor="w"
            )
            # Hide 4th button by default (will be shown for TIDAL); last button gets minimal bottom pady (2); SoundCloud/Apple Music get 4 when repacked
            if i < 3:
                btn.pack(pady=(1, 2) if i == 2 else 1, padx=2, fill="x")
            _search_quality_buttons.append(btn)  # Store reference to button

        # One-liner for SoundCloud/Apple Music: "No other formats available"
        _search_context_menu_bottom_label = customtkinter.CTkLabel(
            _search_context_menu, text="  1 format available",
            font=("Segoe UI", 10), text_color="#808080"
        )
        # show_search_context_menu packs it when platform is soundcloud/applemusic

        # Pack menu frame in wrapper
        _search_context_menu.pack(fill="x", padx=0, pady=0)
        
    except Exception as e:
        print(f"Error creating search context menu: {e}")
        _search_context_menu = None
        _search_context_menu_wrapper = None
        _search_context_menu_bottom_label = None

def _select_quality_and_download(quality_value):
    """Set quality and start download."""
    global _search_context_menu, settings_vars
    
    _hide_search_context_menu()
    
    try:
        # Update the global quality setting
        if 'settings_vars' in globals() and settings_vars:
            quality_var = settings_vars.get("globals", {}).get("general.quality")
            if quality_var and isinstance(quality_var, tkinter.StringVar):
                quality_var.set(quality_value)
                print(f"Quality set to: {quality_value}")
                # Auto-save the setting
                save_settings(show_confirmation=False)
        
        # Start download
        download_selected()
    except Exception as e:
        print(f"Error in quality download: {e}")

def _open_selected_url(event=None):
    """Open the URL of the selected item in external browser."""
    global app, _search_context_menu
    
    _hide_search_context_menu()
    
    try:
        selected_items = get_selected_items_data()
        if not selected_items:
            print("No items selected to open URL.")
            return
        
        # Build URLs for all selected items and open them
        urls_opened = 0
        for item_data in selected_items:
            url = build_url_from_result(item_data)
            if url:
                try:
                    webbrowser.open(url)
                    urls_opened += 1
                except Exception as e:
                    print(f"Error opening URL {url}: {e}")
        
        if urls_opened > 0:
            print(f"Opened {urls_opened} URL(s) in external browser.")
        else:
            print("Could not build URL(s) for selected item(s).")
            
    except Exception as e:
        print(f"Error opening URL: {e}")

def _set_search_quality(quality_value):
    """Set the quality for search result downloads."""
    global _search_context_quality_var, settings_vars
    
    try:
        # Update the global quality setting
        if 'settings_vars' in globals() and settings_vars:
            quality_var = settings_vars.get("globals", {}).get("general.quality")
            if quality_var and isinstance(quality_var, tkinter.StringVar):
                quality_var.set(quality_value)
                print(f"Quality set to: {quality_value}")
                # Auto-save the setting
                save_settings(show_confirmation=False)
    except Exception as e:
        print(f"Error setting quality: {e}")

def _download_with_quality(event=None):
    """Download selected items with the chosen quality."""
    global _search_context_menu  
    
    _hide_search_context_menu()
    download_selected()

def _create_download_icon(size=(16, 16), color="#AAAAAA"):
    """Creates a simple line download icon (Arrow + Line)."""
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    w, h = size
    cx = w // 2
    
    # Bottom horizontal line
    # x: 3 to 13, y: 13
    draw.line([(3, 13), (13, 13)], fill=color, width=1)
    
    # Arrow shaft
    # x: 8, y: 2 to 10
    draw.line([(cx, 2), (cx, 10)], fill=color, width=1)
    
    # Arrow head (simple lines)
    # Tip at (8, 10), left at (5, 7), right at (11, 7)
    draw.line([(cx - 3, 7), (cx, 10), (cx + 3, 7)], fill=color, width=1)
    
    return customtkinter.CTkImage(light_image=image, dark_image=image, size=size)

def _dolby_double_d_photoimage(size=(16, 16), color="#E0E0E0"):
    """Create a small Dolby-style double-D icon (two filled D's, right one mirrored). Returns (PIL Image, PhotoImage)."""
    # Draw at 2x resolution for sharpness
    w, h = size[0] * 2, size[1] * 2
    image = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    stem_w = max(2, w // 6)
    mid = w // 2
    # Left D: stem (vertical bar) + curve (right half of ellipse)
    draw.rectangle([0, 0, stem_w, h], fill=color)
    draw.chord([stem_w, 0, mid, h], 270, 90, fill=color)  # right half of ellipse
    # Right D: curve (left half of ellipse) + stem
    draw.chord([mid, 0, w - stem_w, h], 90, 270, fill=color)  # left half of ellipse
    draw.rectangle([w - stem_w, 0, w, h], fill=color)
    image = image.resize(size, Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(image)
    return image, photo

def _create_undo_icon(size=(16, 16), color="#AAAAAA"):
    """Creates an undo icon (side-U curved arrow pointing left)."""
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Arrow head (simple lines)
    # Tip at (2, 6), top at (6, 3), bottom at (6, 9)
    draw.line([(6, 3), (2, 6), (6, 9)], fill=color, width=1)
    
    # Top line from tip to curve start
    draw.line([(2, 6), (10, 6)], fill=color, width=1)
    
    # Curve part (arc)
    # Bounding box [7, 6, 13, 12] creates a semi-circle from (10, 6) to (10, 12)
    # start=270 (top), end=90 (bottom) clockwise
    draw.arc([7, 6, 13, 12], start=270, end=90, fill=color, width=1)
    
    # Bottom line from curve end to tail
    draw.line([(10, 12), (3, 12)], fill=color, width=1)
    
    return customtkinter.CTkImage(light_image=image, dark_image=image, size=size)

_undo_stacks = {}

def _push_undo(widget):
    """Push current text to undo stack for the given widget."""
    if not widget: return
    if widget not in _undo_stacks:
        _undo_stacks[widget] = []
    
    current_text = widget.get()
    # Only push if different from last state
    if not _undo_stacks[widget] or _undo_stacks[widget][-1] != current_text:
        _undo_stacks[widget].append(current_text)
        # Limit stack size
        if len(_undo_stacks[widget]) > 20:
            _undo_stacks[widget].pop(0)

def _undo_text():
    """Undo text in the target widget."""
    global _target_widget
    if not _target_widget or _target_widget not in _undo_stacks or not _undo_stacks[_target_widget]:
        hide_context_menu()
        return
    
    # The top of the stack is the CURRENT state, so we pop it and take the next one
    # If we only have one item, it might be the current state.
    current_text = _target_widget.get()
    if _undo_stacks[_target_widget] and _undo_stacks[_target_widget][-1] == current_text:
        _undo_stacks[_target_widget].pop()
    
    if _undo_stacks[_target_widget]:
        previous_text = _undo_stacks[_target_widget].pop()
        _target_widget.delete(0, tkinter.END)
        _target_widget.insert(0, previous_text)
    
    hide_context_menu()

def _create_paste_icon(size=(16, 16), color="#AAAAAA"):
    """Creates a simple clipboard paste icon."""
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Main clipboard body
    # x: 3 to 13, y: 4 to 15
    draw.rounded_rectangle([3, 4, 13, 15], radius=1, outline=color, width=1)
    
    # Handle on top
    # x: 6 to 10, y: 1 to 4
    draw.rounded_rectangle([6, 1, 10, 4], radius=1, outline=color, width=1)
    
    return customtkinter.CTkImage(light_image=image, dark_image=image, size=size)


def _create_copy_icon(size=(16, 16), color="#AAAAAA"):
    """Creates a copy icon (two overlapping squares)."""
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    w, h = size
    square_size = 8
    stroke_width = 1
    
    # Back square (top-left) - Fixed orientation
    bx1, by1 = 2, 2
    bx2, by2 = 2 + square_size, 2 + square_size
    
    # Front square (bottom-right) - Fixed orientation
    fx1, fy1 = 5, 5
    fx2, fy2 = 5 + square_size, 5 + square_size
    
    # Draw back square partially to simulate overlap without solid fill
    # Top side
    draw.line([(bx1, by1), (bx2, by1)], fill=color, width=stroke_width)
    # Left side
    draw.line([(bx1, by1), (bx1, by2)], fill=color, width=stroke_width)
    # Right side (only until it hits the front square)
    draw.line([(bx2, by1), (bx2, fy1)], fill=color, width=stroke_width)
    # Bottom side (only until it hits the front square)
    draw.line([(bx1, by2), (fx1, by2)], fill=color, width=stroke_width)
    
    # Draw front square fully (outline only)
    draw.rectangle(
        [fx1, fy1, fx2, fy2],
        outline=color,
        width=stroke_width
    )
    
    return customtkinter.CTkImage(light_image=image, dark_image=image, size=size)


def _create_save_icon(size=(16, 16), color="#AAAAAA"):
    """Creates a save icon (floppy disk)."""
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    w, h = size
    stroke_width = 1
    
    # Floppy disk shape
    # Top rectangle (label area)
    top_x1, top_y1 = 3, 2
    top_x2, top_y2 = 13, 5
    
    # Main body
    body_x1, body_y1 = 2, 5
    body_x2, body_y2 = 14, 13
    
    # Draw main body
    draw.rectangle([body_x1, body_y1, body_x2, body_y2], outline=color, width=stroke_width)
    
    # Draw top label area
    draw.rectangle([top_x1, top_y1, top_x2, top_y2], outline=color, width=stroke_width)
    
    # Draw metal slider (bottom center)
    slider_x1, slider_y1 = 6, 11
    slider_x2, slider_y2 = 10, 12
    draw.rectangle([slider_x1, slider_y1, slider_x2, slider_y2], outline=color, width=stroke_width)
    
    # Draw center hole
    hole_x1, hole_y1 = 7, 7
    hole_x2, hole_y2 = 9, 9
    draw.rectangle([hole_x1, hole_y1, hole_x2, hole_y2], fill=color, outline=color)
    
    return customtkinter.CTkImage(light_image=image, dark_image=image, size=size)


def _create_save_as_icon(size=(16, 16), color="#AAAAAA"):
    """Creates a save-as icon (floppy disk with pencil overlay)."""
    buf = (16, 16)
    image = Image.new("RGBA", buf, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    stroke_width = 1

    # Floppy disk
    draw.rectangle([2, 5, 14, 13], outline=color, width=stroke_width)
    draw.rectangle([3, 2, 13, 5], outline=color, width=stroke_width)
    draw.rectangle([6, 11, 10, 12], outline=color, width=stroke_width)
    draw.rectangle([7, 7, 9, 9], fill=color, outline=color)

    # Pencil overlay (diagonal, lower-left to upper-right, tip at top-right)
    draw.line([(5, 12), (12, 5)], fill=color, width=stroke_width)
    draw.line([(6, 11), (13, 4)], fill=color, width=stroke_width)
    draw.line([(5, 12), (6, 11)], fill=color, width=stroke_width)
    draw.line([(12, 5), (13, 4)], fill=color, width=stroke_width)

    if size != buf:
        image = image.resize(size, Image.Resampling.NEAREST)
    return customtkinter.CTkImage(light_image=image, dark_image=image, size=size)


def _create_external_link_icon(size=(16, 16), color="#AAAAAA"):
    """Creates an external link icon (square with open corner and arrow pointing out)."""
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    w, h = size
    square_size = 9
    stroke_width = 1.5
    
    # Square position (lower-left portion of icon)
    sq_x1, sq_y1 = 2, 5
    sq_x2, sq_y2 = 2 + square_size, 5 + square_size
    
    # Draw square outline with open top-right corner
    # Left side (full height)
    draw.line([(sq_x1, sq_y1), (sq_x1, sq_y2)], fill=color, width=int(stroke_width))
    # Bottom side (full width)
    draw.line([(sq_x1, sq_y2), (sq_x2, sq_y2)], fill=color, width=int(stroke_width))
    # Top side (only left portion, leaving corner open)
    draw.line([(sq_x1, sq_y1), (sq_x2 - 3, sq_y1)], fill=color, width=int(stroke_width))
    # Right side (only bottom portion, leaving corner open)
    draw.line([(sq_x2, sq_y1 + 3), (sq_x2, sq_y2)], fill=color, width=int(stroke_width))
    
    # Arrow pointing diagonally up-right from center of square
    # Arrow starts from approximately center of square
    arrow_start_x = sq_x1 + square_size // 2
    arrow_start_y = sq_y1 + square_size // 2
    # Arrow end point (extending beyond the open corner)
    arrow_end_x = sq_x2 + 4
    arrow_end_y = sq_y1 - 3
    
    # Draw arrow shaft
    draw.line([(arrow_start_x, arrow_start_y), (arrow_end_x, arrow_end_y)], fill=color, width=int(stroke_width))
    
    # Draw arrowhead (triangle pointing up-right)
    arrowhead_size = 3
    # Arrowhead points: tip (at end), left point, bottom point
    tip_x, tip_y = arrow_end_x, arrow_end_y
    left_x, left_y = tip_x - arrowhead_size, tip_y
    bottom_x, bottom_y = tip_x, tip_y + arrowhead_size
    
    # Draw arrowhead as filled triangle
    draw.polygon([(tip_x, tip_y), (left_x, left_y), (bottom_x, bottom_y)], fill=color)
    
    return customtkinter.CTkImage(light_image=image, dark_image=image, size=size)

def show_search_context_menu(event):
    """Show the right-click context menu for search results."""
    global _search_context_menu, _search_context_menu_wrapper, _search_context_menu_bottom_label, _search_context_quality_var, _search_quality_buttons, _search_copy_url_button, _search_context_menu_app_binding_id, _search_context_menu_tree_binding_id, tree, app, settings_vars
    
    _create_search_context_menu()
    
    if not _search_context_menu or not _search_context_menu_wrapper:
        return
    
    try:
        # First, select the item under the cursor if not already selected
        item = tree.identify_row(event.y)
        if item:
            current_selection = tree.selection()
            if item not in current_selection:
                # Single click on unselected item - select it
                tree.selection_set(item)
        
        # Check if there's a selection
        if not tree.selection():
            return
        
        # Determine available qualities based on platform
        selected_items = get_selected_items_data()
        platform_name = ""
        if selected_items:
            # Use the first selected item's platform
            platform_name = selected_items[0].get('platform', '').lower()
        
        # Define platform-specific button configurations
        # Each platform has: (label, quality_value) tuples for buttons
        # Most platforms use 3 buttons, TIDAL uses 4
        platform_button_configs = {
            'qobuz': [
                ("HiFi", "hifi"),
                ("FLAC", "lossless"),
                ("MP3 320", "high")
            ],
            'tidal': [
                ("HiFi", "hifi"),
                ("FLAC", "lossless"),
                ("AAC 320", "high"),
                ("AAC 96", "low")
            ],
            'spotify': [
                ("FLAC", "lossless"),
                ("OGG 320", "hifi"),
                ("OGG 160", "high")
            ],
            'youtube': [
                ("OPUS", "hifi"),
                ("AAC", "high"),
                ("MP3", "low")
            ],
            'applemusic': [
                ("ALAC", "lossless"),
                ("AAC 256", "high"),
                ("AAC 128", "low")
            ],
            'apple music': [
                ("ALAC", "lossless"),
                ("AAC 256", "high"),
                ("AAC 128", "low")
            ],
            'soundcloud': [
                ("FLAC", "lossless"),
                ("AAC 256", "high"),
                ("AAC 128", "low")
            ],
            'beatport': [
                ("FLAC", "lossless"),
                ("AAC 256", "high"),
                ("AAC 128", "low")
            ],
            'beatsource': [
                ("FLAC", "lossless"),
                ("AAC 256", "high"),
                ("AAC 128", "low")
            ],
            # Default configuration for most platforms
            'default': [
                ("FLAC", "lossless"),
                ("MP3 320", "high"),
                ("MP3 128", "low")
            ]
        }
        
        # Define available qualities per platform
        # Ensure all options in button configs are marked as available
        platform_available_qualities = {
            'applemusic': ['high'],
            'apple music': ['high'],
            'soundcloud': ['high'],
            'spotify': ['hifi', 'high'],
            'qobuz': ['hifi', 'lossless', 'high'],
            'tidal': ['hifi', 'lossless', 'high', 'low'],
            'youtube': ['hifi', 'high', 'low'],
            'beatport': ['lossless', 'high', 'low'],
            'beatsource': ['lossless', 'high', 'low'],
            # Other platforms support all default qualities
        }
        
        # Get button configuration for this platform
        button_config = platform_button_configs.get(platform_name, platform_button_configs['default'])
        
        # Get available qualities for this platform (default: all available for default config)
        default_qualities = [v for _, v in platform_button_configs['default']]
        available_qualities = platform_available_qualities.get(platform_name, default_qualities)
        
        # Determine if we need to show the 4th button (for TIDAL)
        needs_4_buttons = len(button_config) > 3
        
        # Reset packing for all quality buttons to ensure correct order
        for btn in _search_quality_buttons:
            if btn and btn.winfo_exists():
                btn.pack_forget()

        # Update button labels, commands, states, and visibility based on platform
        for i, btn in enumerate(_search_quality_buttons):
            if btn and btn.winfo_exists():
                if i < len(button_config):
                    label, quality_value = button_config[i]
                    is_available = quality_value in available_qualities
                    
                    if is_available:
                        # Create and store icons (icon color = text color)
                        icon = _create_download_icon(color=CONTEXT_MENU_TEXT_COLOR)
                        btn.image = icon  # Keep reference
                        
                        # Update button text, icon and command
                        btn.configure(
                            text=label,
                            image=icon,
                            compound="left",
                            command=lambda v=quality_value: _select_quality_and_download(v),
                            state="normal"
                        )
                        # Last visible button: less bottom pady for 3+ option platforms; a bit more for SoundCloud/Apple Music (1 option)
                        is_last_visible = i == len(button_config) - 1
                        if is_last_visible and platform_name in ('soundcloud', 'applemusic', 'apple music'):
                            btn.pack(pady=(1, 4), padx=2, fill="x")
                        else:
                            btn.pack(pady=(1, 2) if is_last_visible else 1, padx=2, fill="x")
                    else:
                        # Hide unavailable option
                        btn.pack_forget()
                else:
                    # Hide unused buttons (e.g. 4th button if config has fewer items)
                    btn.pack_forget()
        
        # For SoundCloud/Apple Music: show "No other formats available" below the quality button
        if _search_context_menu_bottom_label and _search_context_menu_bottom_label.winfo_exists():
            if platform_name in ('soundcloud', 'applemusic', 'apple music'):
                _search_context_menu_bottom_label.pack(side="bottom", pady=(2, 4), padx=6, anchor="w")
            else:
                _search_context_menu_bottom_label.pack_forget()
        
        # Update quality radio button to match current setting
        if 'settings_vars' in globals() and settings_vars and _search_context_quality_var:
            quality_var = settings_vars.get("globals", {}).get("general.quality")
            if quality_var and isinstance(quality_var, tkinter.StringVar):
                current_quality = quality_var.get()
                _search_context_quality_var.set(current_quality)
        
        # Position the menu at the cursor (place wrapper so 1px padding keeps frame border visible)
        x_root, y_root = app.winfo_pointerxy()
        scaling = app._get_window_scaling()
        menu_x = (x_root - app.winfo_rootx()) / scaling + 2
        menu_y = (y_root - app.winfo_rooty()) / scaling + 2
        
        _search_context_menu_wrapper.place(x=menu_x, y=menu_y)
        _search_context_menu_wrapper.lift()
        
        # Bind left-click outside to hide menu. Tree: use ButtonRelease-1 so we don't compete with tree's Button-1 (macOS selection).
        _unbind_search_context_menu_hide()
        _search_context_menu_app_binding_id = app.bind("<Button-1>", _hide_search_context_menu_on_click, add=True)
        if 'tree' in globals() and tree and tree.winfo_exists():
            _search_context_menu_tree_binding_id = tree.bind("<ButtonRelease-1>", _hide_search_context_menu_on_click, add=True)
        
    except Exception as e:
        print(f"Error showing search context menu: {e}")

def _unbind_search_context_menu_hide():
    """Remove the left-click bindings we added to dismiss the search context menu."""
    global _search_context_menu_app_binding_id, _search_context_menu_tree_binding_id
    try:
        if _search_context_menu_app_binding_id and 'app' in globals() and app and app.winfo_exists():
            app.unbind("<Button-1>", _search_context_menu_app_binding_id)
    except (tkinter.TclError, Exception):
        pass
    _search_context_menu_app_binding_id = None
    try:
        if _search_context_menu_tree_binding_id and 'tree' in globals() and tree and tree.winfo_exists():
            tree.unbind("<ButtonRelease-1>", _search_context_menu_tree_binding_id)
    except (tkinter.TclError, Exception):
        pass
    _search_context_menu_tree_binding_id = None


def _hide_search_context_menu(event=None):
    """Hide the search context menu."""
    global _search_context_menu, _search_context_menu_wrapper
    
    _unbind_search_context_menu_hide()
    try:
        if _search_context_menu_wrapper and _search_context_menu_wrapper.winfo_exists():
            _search_context_menu_wrapper.place_forget()
    except Exception as e:
        print(f"Error hiding search context menu: {e}")

def _hide_search_context_menu_on_click(event):
    """Hide the search context menu when clicking outside of it (left-click anywhere, including on tree)."""
    global _search_context_menu_wrapper
    
    try:
        if _search_context_menu_wrapper and _search_context_menu_wrapper.winfo_exists():
            # Check if click is outside the menu (use wrapper bounds so 1px padding counts as inside)
            if 'app' in globals() and app and app.winfo_exists():
                x_root, y_root = app.winfo_pointerxy()
            else:
                return
            menu_x = _search_context_menu_wrapper.winfo_rootx()
            menu_y = _search_context_menu_wrapper.winfo_rooty()
            menu_width = _search_context_menu_wrapper.winfo_width()
            menu_height = _search_context_menu_wrapper.winfo_height()
            
            if not (menu_x <= x_root <= menu_x + menu_width and
                    menu_y <= y_root <= menu_y + menu_height):
                _hide_search_context_menu()
    except Exception:
        pass

def build_url_from_result(result_data):
    platform = result_data.get('platform'); search_type = result_data.get('type'); item_id = result_data.get('id'); raw_result_obj = result_data.get('raw_result')
    if not all([platform, search_type, item_id]): print("[URL Build] Missing data."); return None

    p_lower = platform.lower(); t_lower = search_type.lower()

    base_urls = { "qobuz": "https://open.qobuz.com", "tidal": "https://listen.tidal.com", "deezer": "https://www.deezer.com", "beatport": "https://www.beatport.com", "beatsource": "https://www.beatsource.com", "napster": "https://web.napster.com", "idagio": "https://app.idagio.com", "spotify": "https://open.spotify.com", "applemusic": "https://music.apple.com" }
    type_paths = { 
        "qobuz": {"track": "track", "album": "album", "artist": "artist", "playlist": "playlist", "label": "label"},
        "tidal": {"track": "track", "album": "album", "artist": "artist", "playlist": "playlist"},
        "deezer": {"track": "track", "album": "album", "artist": "artist", "playlist": "playlist"},
        "beatport": {"track": "track", "album": "release", "artist": "artist", "playlist": "chart", "label": "label"},
        "beatsource": {"track": "track", "album": "release", "artist": "artist", "playlist": "playlist", "label": "label"},
        "napster": {"track": "track", "album": "album", "artist": "artist", "playlist": "playlist"},
        "idagio": {"track": "recording", "album": "album", "artist": "artist"},
        "spotify": {"track": "track", "album": "album", "artist": "artist", "playlist": "playlist"},
        "applemusic": {"track": "song", "album": "album", "artist": "artist", "playlist": "playlist"}
    }

    # YouTube URL building - uses video/playlist/channel URL format
    if p_lower == "youtube":
        if t_lower == 'track':
            url = f"https://www.youtube.com/watch?v={item_id}"
            print(f"[URL Build - YouTube] Constructed video URL: {url}")
            return url
        elif t_lower == 'playlist' or t_lower == 'album':
            url = f"https://www.youtube.com/playlist?list={item_id}"
            print(f"[URL Build - YouTube] Constructed playlist URL: {url}")
            return url
        elif t_lower == 'artist' or t_lower == 'channel':
            url = f"https://www.youtube.com/channel/{item_id}"
            print(f"[URL Build - YouTube] Constructed channel URL: {url}")
            return url
        else:
            print(f"[URL Build - YouTube] Unknown type '{t_lower}'.")
            return None

    if p_lower == "soundcloud":
        if raw_result_obj:
            permalink = getattr(raw_result_obj, 'permalink_url', None)
            if permalink: print(f"[SC URL] Using permalink: {permalink}"); return permalink            
        if t_lower == 'track': sc_entity = 'tracks'
        elif t_lower == 'playlist' or t_lower == 'album': sc_entity = 'playlists'
        elif t_lower == 'artist': sc_entity = 'users'
        else: print(f"[SC URL] Unknown type '{t_lower}'."); return None
        sc_api_url = f"https://api.soundcloud.com/{sc_entity}/{item_id}"
        widget_api_url = f'https://api-widget.soundcloud.com/resolve?url={sc_api_url}&format=json&client_id=gqKBMSuBw5rbN9rDRYPqKNvF17ovlObu&app_version=1742894364'
        headers = {'Referer': 'https://w.soundcloud.com/', 'Origin': 'https://w.soundcloud.com/', 'User-Agent': 'Mozilla/5.0'}
        try:
            print(f"[SC URL] Requesting widget API: {widget_api_url}")
            response = requests.get(widget_api_url, headers=headers, timeout=10); response.raise_for_status(); data = response.json()
            permalink_from_api = data.get('permalink_url')
            if permalink_from_api: print(f"[SC URL] Resolved via API: {permalink_from_api}"); return permalink_from_api
            else: print(f"[SC URL] API Error: No permalink in response: {data}"); return None
        except requests.exceptions.RequestException as e: print(f"[SC URL] API Request Error: {e}"); return None
        except json.JSONDecodeError as e: print(f"[SC URL] API JSON Error: {e}"); return None
        except Exception as e: print(f"[SC URL] API Unexpected Error: {e}"); return None
        return None

    elif p_lower == "beatport":
        if raw_result_obj:
            permalink = getattr(raw_result_obj, 'permalink_url', None)
            if not permalink:
                permalink = getattr(raw_result_obj, 'url', None)
            
            if permalink:
                print(f"[URL Build - Beatport] Using attribute permalink/url: {permalink}")
                return permalink

            slug = getattr(raw_result_obj, 'slug', None) if not isinstance(raw_result_obj, dict) else raw_result_obj.get('slug')
            if not slug:
                name_for_slug = getattr(raw_result_obj, 'name', None) if not isinstance(raw_result_obj, dict) else raw_result_obj.get('name') or raw_result_obj.get('title')
                if name_for_slug:
                    derived_slug = _simple_slugify(name_for_slug)
                    if derived_slug:
                        print(f"[URL Build - Beatport] Derived slug '{derived_slug}' from name '{name_for_slug}'.")
                        slug = derived_slug
                    else:
                        print(f"[URL Build - Beatport] Could not derive a valid slug from name: '{name_for_slug}'.")
                else:
                    print(f"[URL Build - Beatport] No 'name' attribute to derive slug from.")

            # Fallback for release/album: derive slug from result_data title (e.g. rows from label releases view)
            if not slug and t_lower == 'album' and result_data.get('title'):
                derived_slug = _simple_slugify(result_data.get('title'))
                if derived_slug:
                    print(f"[URL Build - Beatport] Derived slug '{derived_slug}' from result_data title '{result_data.get('title')}'.")
                    slug = derived_slug

            if slug and item_id and t_lower in type_paths.get(p_lower, {}):
                url_path_segment = type_paths[p_lower][t_lower]
                slug_str = str(slug).strip()
                if slug_str: 
                    url = f"{base_urls[p_lower]}/{url_path_segment}/{slug_str}/{item_id}"
                    print(f"[URL Build - Beatport] Constructed with slug '{slug_str}': {url}")
                    return url
                else:
                    print(f"[URL Build - Beatport] Slug (original or derived) was empty after processing. Falling back.")
            else:
                print(f"[URL Build - Beatport] No valid slug, or item_id/type invalid for slug path. Slug: {slug}, ID: {item_id}, Type: {t_lower}")
        else:
            print(f"[URL Build - Beatport] raw_result_obj is None. Cannot get permalink or slug.")

        print(f"[URL Build - Beatport] Attempting fallback URL construction (slug not available/derivable or other issue).")
        if p_lower in base_urls and p_lower in type_paths and t_lower in type_paths[p_lower]:
            url_path_segment = type_paths[p_lower][t_lower]
            url = f"{base_urls[p_lower]}/{url_path_segment}/{item_id}"
            print(f"[URL Build - Beatport] Fallback (no slug/permalink found): {url}")
            return url
        else:
            print(f"[URL Build - Beatport] Fallback failed: Path construction not supported for type '{t_lower}'.")
            return None
    elif p_lower == "applemusic":
        print(f"[URL Build - Apple Music] Building URL for {t_lower} with ID {item_id}")
        country = "us"
        if raw_result_obj:
            try:
                if hasattr(raw_result_obj, 'href') and raw_result_obj.href:
                    href_parts = raw_result_obj.href.split('/')
                    if len(href_parts) > 3:
                        potential_country = href_parts[3]
                        if len(potential_country) == 2:
                            country = potential_country
                elif hasattr(raw_result_obj, 'attributes') and 'url' in raw_result_obj.attributes:
                    url_parts = raw_result_obj.attributes['url'].split('/')
                    if len(url_parts) > 3:
                        potential_country = url_parts[3]
                        if len(potential_country) == 2:
                            country = potential_country
            except Exception as e:
                print(f"[URL Build - Apple Music] Could not extract country from raw result: {e}")
        type_mapping = {
            "track": "song",
            "album": "album", 
            "artist": "artist",
            "playlist": "playlist"
        }
        
        apple_music_type = type_mapping.get(t_lower, "song")
        url_name = "unknown"
        if raw_result_obj:
            try:
                if hasattr(raw_result_obj, 'attributes') and 'name' in raw_result_obj.attributes:
                    name = raw_result_obj.attributes['name']
                    url_name = _simple_slugify(name) or "unknown"
                elif hasattr(raw_result_obj, 'name'):
                    name = raw_result_obj.name
                    url_name = _simple_slugify(name) or "unknown"
            except Exception as e:
                print(f"[URL Build - Apple Music] Could not extract name from raw result: {e}")
        apple_music_url = f"https://music.apple.com/{country}/{apple_music_type}/{url_name}/{item_id}"
        print(f"[URL Build - Apple Music] Constructed URL: {apple_music_url}")
        return apple_music_url
    
    elif p_lower == "beatsource":
        # Beatsource requires slug in URL (e.g. /track/jacky/8124762); URL without slug returns 404
        slug = None
        
        if raw_result_obj:
            permalink = getattr(raw_result_obj, 'permalink_url', None) if not isinstance(raw_result_obj, dict) else raw_result_obj.get('permalink_url')
            if not permalink and not isinstance(raw_result_obj, dict):
                permalink = getattr(raw_result_obj, 'url', None)
            if not permalink and isinstance(raw_result_obj, dict):
                permalink = raw_result_obj.get('url')
            # Only use if it's the website URL; API URLs (api.beatsource.com) must not be used for "Open link"
            if permalink and 'www.beatsource.com' in permalink and 'api.beatsource.com' not in permalink:
                print(f"[URL Build - Beatsource] Using attribute permalink/url: {permalink}")
                return permalink

            slug = getattr(raw_result_obj, 'slug', None) if not isinstance(raw_result_obj, dict) else raw_result_obj.get('slug')
            if not slug:
                # Check extra_kwargs for artist_slug (stored during search)
                extra_kwargs = getattr(raw_result_obj, 'extra_kwargs', {}) if not isinstance(raw_result_obj, dict) else raw_result_obj.get('extra_kwargs') or {}
                if isinstance(extra_kwargs, dict):
                    slug = extra_kwargs.get('artist_slug') or extra_kwargs.get('track_slug')
            if not slug:
                name_for_slug = getattr(raw_result_obj, 'name', None) if not isinstance(raw_result_obj, dict) else (raw_result_obj.get('name') or raw_result_obj.get('title'))
                if name_for_slug:
                    derived_slug = _simple_slugify(name_for_slug)
                    if derived_slug:
                        print(f"[URL Build - Beatsource] Derived slug '{derived_slug}' from name '{name_for_slug}'.")
                        slug = derived_slug

        # Fallback: derive slug from result_data (e.g. release rows from label view)
        if not slug and t_lower == 'album' and result_data.get('title'):
            derived_slug = _simple_slugify(result_data.get('title'))
            if derived_slug:
                print(f"[URL Build - Beatsource] Derived slug '{derived_slug}' from result_data title '{result_data.get('title')}'.")
                slug = derived_slug
        # Fallback: derive slug from result_data (title for tracks, artist/title for artists)
        if not slug and t_lower == 'artist':
            artist_name = result_data.get('artist') or result_data.get('title')
            if artist_name:
                derived_slug = _simple_slugify(artist_name)
                if derived_slug:
                    print(f"[URL Build - Beatsource] Derived slug '{derived_slug}' from result_data artist/title '{artist_name}'.")
                    slug = derived_slug
        if not slug and t_lower == 'track':
            title = result_data.get('title') or result_data.get('name')
            if title:
                derived_slug = _simple_slugify(title)
                if derived_slug:
                    print(f"[URL Build - Beatsource] Derived slug '{derived_slug}' from result_data title '{title}'.")
                    slug = derived_slug
        if not slug and t_lower == 'label':
            slug = result_data.get('label_slug')
            if not slug:
                label_name = result_data.get('artist') or result_data.get('title')
                if label_name:
                    derived_slug = _simple_slugify(label_name)
                    if derived_slug:
                        print(f"[URL Build - Beatsource] Derived slug '{derived_slug}' from result_data (label) '{label_name}'.")
                        slug = derived_slug

        if slug and item_id and t_lower in type_paths.get(p_lower, {}):
            url_path_segment = type_paths[p_lower][t_lower]
            slug_str = str(slug).strip()
            if slug_str: 
                url = f"{base_urls[p_lower]}/{url_path_segment}/{slug_str}/{item_id}"
                print(f"[URL Build - Beatsource] Constructed with slug '{slug_str}': {url}")
                return url

        # Fallback without slug (works for tracks/albums but not artists)
        print(f"[URL Build - Beatsource] Attempting fallback URL construction.")
        if p_lower in base_urls and p_lower in type_paths and t_lower in type_paths[p_lower]:
            url_path_segment = type_paths[p_lower][t_lower]
            url = f"{base_urls[p_lower]}/{url_path_segment}/{item_id}"
            print(f"[URL Build - Beatsource] Fallback (no slug): {url}")
            return url
        else:
            print(f"[URL Build - Beatsource] Fallback failed for type '{t_lower}'.")
            return None
    
    else:
        if p_lower in base_urls and p_lower in type_paths and t_lower in type_paths[p_lower]:
            url_path_segment = type_paths[p_lower][t_lower]; url = f"{base_urls[p_lower]}/{url_path_segment}/{item_id}"
            print(f"[URL Build - {platform}] Constructed: {url}"); return url
        else: print(f"[URL Build - {platform}] Not supported for type '{t_lower}'."); return None

def download_selected():
    global tabview, url_entry, file_download_queue, current_batch_output_path
    try:
        selected_items = get_selected_items_data()
        if not selected_items: 
            show_centered_messagebox("Error", "No items selected.", dialog_type="warning")
            return
        
        if len(selected_items) == 1:
            selected_data = selected_items[0]
            url_to_download = build_url_from_result(selected_data)
            if url_to_download:
                print(f"Switching tab and starting download for: {url_to_download}")
                if 'tabview' in globals() and tabview and tabview.winfo_exists():
                    tabview.set("Download")
                if 'url_entry' in globals() and url_entry and url_entry.winfo_exists():
                    url_entry.delete(0, "end"); url_entry.insert(0, url_to_download)
                else: print("Warning: url_entry not found.")
                start_download_thread(search_result_data=selected_data)
            else: 
                show_centered_messagebox("Error", f"Could not determine URL for selected item.", dialog_type="error")
        else:
            print(f"Starting batch download for {len(selected_items)} items")
            urls_to_download = []
            failed_items = []
            
            for item_data in selected_items:
                url = build_url_from_result(item_data)
                if url:
                    urls_to_download.append(url)
                else:
                    failed_items.append(f"{item_data.get('title', 'Unknown')} by {item_data.get('artist', 'Unknown')}")
            
            if failed_items:
                failed_list = '\n'.join(failed_items[:5])
                if len(failed_items) > 5:
                    failed_list += f'\n... and {len(failed_items) - 5} more'
                show_centered_messagebox("Warning", 
                    f"Could not build URLs for {len(failed_items)} item(s):\n{failed_list}\n\nProceeding with {len(urls_to_download)} valid items.", 
                    dialog_type="warning")
            
            if not urls_to_download:
                show_centered_messagebox("Error", "Could not build URLs for any selected items.", dialog_type="error")
                return
            if 'tabview' in globals() and tabview and tabview.winfo_exists():
                tabview.set("Download")
            global current_batch_output_path
            if 'path_var_main' in globals() and path_var_main:
                output_path = path_var_main.get().strip()
                if output_path:
                    try:
                        norm_path = os.path.normpath(output_path)
                        current_batch_output_path = os.path.join(norm_path, '')
                        if not os.path.exists(norm_path):
                            os.makedirs(norm_path, exist_ok=True)
                        print(f"Set batch output path to: {current_batch_output_path}")
                    except Exception as e:
                        print(f"Error setting up batch output path: {e}")
                        current_batch_output_path = None
                else:
                    current_batch_output_path = None
            else:
                current_batch_output_path = None
            file_download_queue.clear()
            file_download_queue.extend(urls_to_download)
            if file_download_queue:
                first_url = file_download_queue.pop(0)
                print(f"Starting batch download with first URL: {first_url}")
                print(f"Remaining in queue: {len(file_download_queue)} items")
                if 'url_entry' in globals() and url_entry and url_entry.winfo_exists():
                    url_entry.delete(0, "end")
                    url_entry.insert(0, first_url)
                else: 
                    print("Warning: url_entry not found.")
                _start_single_download(first_url, current_batch_output_path, selected_items[0])
            else:
                print("Error: Queue was empty after setup")
            
    except NameError as e: print(f"Error in download_selected (widget not ready?): {e}")
    except tkinter.TclError as e: print(f"TclError in download_selected (widget destroyed?): {e}")
    except Exception as e: print(f"Unexpected error in download_selected: {e}")

def _parse_duration_str_to_seconds(s):
    """Parse displayed duration string (e.g. '1:23:45', '45:30', '90') to integer seconds, or None."""
    if s is None: return None
    if isinstance(s, (int, float)):
        try: return int(s)
        except (TypeError, ValueError): return None
    s = str(s).strip()
    if not s: return None
    try:
        parts = [p.strip() for p in s.split(":")]
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        if len(parts) == 1 and parts[0].isdigit():
            return int(parts[0])
    except (ValueError, TypeError):
        pass
    return None

def _parse_additional_track_count(s):
    """Extract track count from Additional string (e.g. '50 tracks', '1 track', '8 tracks, Cat: X') for numeric sort. Returns (number, original_string) so we can sort by number then by string."""
    if s is None or not str(s).strip():
        return (None, str(s) if s is not None else "")
    s = str(s).strip()
    # Match "N track" or "N tracks" (optional comma and rest like ", Cat: XYZ")
    m = re.search(r"(\d+)\s*tracks?", s, re.IGNORECASE)
    if m:
        try:
            return (int(m.group(1)), s)
        except (ValueError, TypeError):
            pass
    return (None, s)

def _parse_additional_quality(s):
    """Parse quality from Additional string for sort: Qobuz 'XkHz/Ybit', Tidal 'HiFi'/'MQA'/'360 Reality Audio'/'Dolby Atmos'. Returns (numeric_score, True) if parsed else (None, False). Higher score = better quality."""
    if s is None:
        return (None, False)
    if isinstance(s, list):
        s = (s[0] if s else '') or ''
    s = str(s).strip()
    if not s:
        return (None, False)
    # Qobuz: "44.1kHz/24bit", "96kHz/24bit", "192kHz/24bit"
    m = re.search(r"(\d+(?:\.\d+)?)\s*kHz(?:\s*/\s*(\d+)\s*bit)?", s, re.IGNORECASE)
    if m:
        try:
            sr = float(m.group(1))
            bd = int(m.group(2)) if m.group(2) else 0
            return (sr * 1000 + bd, True)
        except (ValueError, TypeError):
            pass
    # Tidal: fixed labels (order = quality tier, higher = better)
    tidal_order = (
        ("dolby atmos", 100004),
        ("360 reality audio", 100003),
        ("mqa", 100002),
        ("hifi", 100001),
    )
    lower = s.lower()
    for label, score in tidal_order:
        if label in lower:
            return (score, True)
    return (None, False)

def sort_results(column):
    global sort_states, search_results_data, tree, _currently_playing_preview_iid, _cover_hover_cache, _cover_hover_iid, _expanded_album_playlist_iids
    try:
        if 'tree' not in globals() or not tree or not tree.winfo_exists(): return
        is_numeric = column in ["#", "Year"]; is_reverse = sort_states.get(column, False)
        is_duration = column == "Duration"

        def sort_key(item):
            key_map = {"#": "number", "Year": "year", "Title": "title", "Artist": "artist", "Duration": "duration", "Additional": "additional", "Explicit": "explicit", "ID": "id"}
            dict_key = key_map.get(column, column); value = item.get(dict_key, "")
            if value is None: value = ""
            if is_duration:
                sec = item.get("duration_seconds")
                if sec is None:
                    sec = _parse_duration_str_to_seconds(item.get("duration"))
                try:
                    return int(sec) if sec is not None else 0
                except (TypeError, ValueError):
                    return 0
            if column == "Additional":
                # Normalize: value may be string or list (e.g. from module)
                val_str = (value[0] if isinstance(value, list) and value else value) or ''
                if val_str is not value and not isinstance(val_str, str):
                    val_str = str(val_str) if val_str else ''
                else:
                    val_str = str(val_str) if val_str else ''
                num, _ = _parse_additional_track_count(val_str)
                if num is not None:
                    return (0, num)  # track count: sort by count
                quality_score, ok = _parse_additional_quality(val_str)
                if ok:
                    return (1, quality_score)  # quality: sort by score (Qobuz kHz/bit, Tidal tier)
                # Unknown text (e.g. Apple Music "clean"): put non-empty at one end, empty at the other
                return (2, 1 if val_str.strip() else 0)
            if is_numeric: return int(value) if str(value).isdigit() else 0
            else: return str(value).lower()
        # Sort only root-level items; keep children attached to their parent
        roots = [r for r in search_results_data if not r.get('parent_iid')]
        roots.sort(key=sort_key, reverse=is_reverse)
        ordered = []
        for r in roots:
            ordered.append(r)
            ordered.extend([c for c in search_results_data if c.get('parent_iid') == r.get('tree_iid')])
        search_results_data = ordered
        sort_states[column] = not is_reverse
        _expanded_album_playlist_iids.clear()  # Collapse all on sort
        clear_treeview()
        for idx, item_data in enumerate(ordered):
            try:
                if 'tree' in globals() and tree and tree.winfo_exists():
                    preview_url = item_data.get('preview_url')
                    tree_iid = item_data.get('tree_iid', item_data.get('id', ''))
                    parent_iid = item_data.get('parent_iid')
                    is_playing = _currently_playing_preview_iid == tree_iid
                    platform_str = item_data.get('platform', 'Unknown')
                    search_type_str = item_data.get('type', 'track')
                    is_track_search = search_type_str.lower() == "track"
                    can_lazy_load_preview = (platform_str.lower() in ('qobuz', 'soundcloud', 'spotify', 'tidal')) and is_track_search
                    is_youtube_track = (platform_str.lower() == 'youtube') and is_track_search
                    is_album_playlist = item_data.get('is_album_playlist')
                    is_artist = item_data.get('is_artist')
                    if is_album_playlist or is_artist:
                        preview_icon = PREVIEW_EXPAND_COLLAPSED
                    elif preview_url or can_lazy_load_preview or is_youtube_track:
                        preview_icon = PREVIEW_STOP_ICON if is_playing else PREVIEW_PLAY_ICON
                    else:
                        preview_icon = PREVIEW_UNAVAILABLE
                    values = ( preview_icon, item_data.get('number', ''), item_data.get('title', ''), item_data.get('artist', ''), item_data.get('duration', ''), item_data.get('year', ''), item_data.get('additional', ''), item_data.get('explicit', ''), item_data.get('id', '') )
                    row_tag = "oddrow" if (idx % 2 == 0) else "evenrow"
                    tags = (row_tag, "playing") if (is_playing and preview_url) else (row_tag,)
                    global _cover_hover_iid
                    cover_image = None
                    if _cover_hover_iid == tree_iid:
                        cover_image = _cover_hover_cache.get(tree_iid)
                    if not cover_image:
                        cover_image = _cover_image_cache.get(tree_iid)
                    insert_parent = parent_iid if parent_iid else ""
                    if cover_image:
                        tree.insert(insert_parent, "end", iid=tree_iid, values=values, image=cover_image, tags=tags)
                    else:
                        tree.insert(insert_parent, "end", iid=tree_iid, values=values, tags=tags)
                else: break
            except NameError: break
            except tkinter.TclError as e: print(f"TclError repopulating sorted treeview (widget destroyed?): {e}"); break
            except Exception as e: print(f"Error repopulating sorted treeview: {e}")
        defined_columns = ("Preview", "#", "Title", "Artist", "Duration", "Year", "Additional", "Explicit", "ID")
        for col in defined_columns:
            if 'tree' in globals() and tree and tree.winfo_exists():
                try:
                    heading_text = tree.heading(col, "text").replace(" ▲", "").replace(" ▼", "")
                    indicator = "" if col != column else (" ▼" if is_reverse else " ▲")
                    tree.heading(col, text=heading_text + indicator)
                except tkinter.TclError: pass
    except NameError: pass
    except tkinter.TclError as e: print(f"TclError sorting results (widget destroyed?): {e}")
    except Exception as e: print(f"Error sorting results by '{column}': {e}"); show_centered_messagebox("Error", f"Sort failed: {e}", dialog_type="error")

def _update_settings_tab_widgets():
    """Refreshes Global settings tab widgets AND credential tabs from current_settings."""
    global current_settings, settings_vars, path_var_main, DEFAULT_SETTINGS, credential_tabs_config, loaded_credential_tabs, app
    if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
        print("Refreshing Global Settings tab UI from current_settings...")
    try:
        for key, var in settings_vars.get("globals", {}).items():
            if key == "advanced.codec_conversions":
                current_codec_conversions_setting = current_settings.get("globals", {}).get("advanced", {}).get("codec_conversions", {})
                
                if isinstance(var, dict) and isinstance(current_codec_conversions_setting, dict):
                    for source_codec_from_settings, target_codec_from_settings in current_codec_conversions_setting.items():
                        source_var_key = f"{source_codec_from_settings}_source"
                        target_var_key = f"{source_codec_from_settings}_target"

                        if source_var_key in var and isinstance(var[source_var_key], tkinter.StringVar):
                            try: var[source_var_key].set(source_codec_from_settings)
                            except Exception as e_set_src: print(f"Error setting source var {source_var_key}: {e_set_src}")

                        if target_var_key in var and isinstance(var[target_var_key], tkinter.StringVar):
                            try: var[target_var_key].set(target_codec_from_settings)
                            except Exception as e_set_tgt: print(f"Error setting target var {target_var_key}: {e_set_tgt}")
                continue
            
            if not isinstance(var, tkinter.Variable):
                continue
            
            keys = key.split('.')
            temp_dict = current_settings.get("globals", {})
            valid_path = True
            for k_part in keys:
                if isinstance(temp_dict, dict):
                    temp_dict = temp_dict.get(k_part)
                else:
                    valid_path = False
                    break
            value_from_dict = temp_dict if valid_path else None
            
            if value_from_dict is not None:
                try:
                    if isinstance(var, tkinter.BooleanVar):
                        var.set(bool(value_from_dict))
                    else:
                        var.set(str(value_from_dict))
                except tkinter.TclError as e_set:
                    if "invalid command name" in str(e_set): pass
                    else: print(f"Error setting variable for {key}: {e_set}")
                except Exception as e_set_other:
                    print(f"Error setting variable for {key}: {e_set_other}")

        # Refresh specific advanced settings (sliders, etc.)
        aac_br_var = settings_vars.get("globals", {}).get("advanced.conversion_flags.aac.audio_bitrate")
        if aac_br_var and isinstance(aac_br_var, tkinter.StringVar):
            aac_default_val = DEFAULT_SETTINGS["globals"]["advanced"]["conversion_flags"]["aac"]["audio_bitrate"]
            aac_current_br_from_settings = str(current_settings.get("globals", {}).get("advanced", {}).get("conversion_flags", {}).get("aac", {}).get("audio_bitrate", aac_default_val))
            aac_br_var.set(aac_current_br_from_settings)
            
        flac_cl_var = settings_vars.get("globals", {}).get("advanced.conversion_flags.flac.compression_level")
        if flac_cl_var and isinstance(flac_cl_var, tkinter.StringVar):
            flac_default_val = DEFAULT_SETTINGS["globals"]["advanced"]["conversion_flags"]["flac"]["compression_level"]
            flac_current_cl_from_settings = str(current_settings.get("globals", {}).get("advanced", {}).get("conversion_flags", {}).get("flac", {}).get("compression_level", flac_default_val))
            flac_cl_var.set(flac_current_cl_from_settings)
            
        mp3_setting_var = settings_vars.get("globals", {}).get("advanced.conversion_flags.mp3.setting")
        if mp3_setting_var and isinstance(mp3_setting_var, tkinter.StringVar):
            mp3_conf_flags_loaded = current_settings.get("globals", {}).get("advanced", {}).get("conversion_flags", {}).get("mp3", {})
            mp3_default_conf_flags_loaded = DEFAULT_SETTINGS["globals"]["advanced"]["conversion_flags"]["mp3"]
            
            resolved_display_val = None
            if isinstance(mp3_conf_flags_loaded, dict):
                if "audio_bitrate" in mp3_conf_flags_loaded and isinstance(mp3_conf_flags_loaded["audio_bitrate"], str) and mp3_conf_flags_loaded["audio_bitrate"].endswith('k'):
                    resolved_display_val = mp3_conf_flags_loaded["audio_bitrate"]
                elif "qscale:a" in mp3_conf_flags_loaded and mp3_conf_flags_loaded["qscale:a"] == "0":
                    resolved_display_val = "VBR -V0"
            
            valid_mp3_ui_options = ["128k", "192k", "256k", "320k", "VBR -V0"]
            if resolved_display_val is None or resolved_display_val not in valid_mp3_ui_options:
                resolved_display_val = "VBR -V0"
            mp3_setting_var.set(resolved_display_val)
        
        if 'path_var_main' in globals() and isinstance(path_var_main, tkinter.Variable) and "general.output_path" not in settings_vars.get("globals", {}):
             main_path_val = current_settings.get("globals", {}).get("general", {}).get("output_path")
             if main_path_val is not None:
                  try: path_var_main.set(main_path_val)
                  except tkinter.TclError as e_set_main:
                      if "invalid command name" in str(e_set_main): pass
                      else: print(f"Error setting main path variable: {e_set_main}")
                  except Exception as e_set_main_other:
                      print(f"Error setting main path variable: {e_set_main_other}")

        if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
            print("Global Settings tab UI refresh finished.")
        
        # --- Credential Tabs Refresh (Merged from duplicate function) ---
        for platform_name, tab_info in credential_tabs_config.items():
            if platform_name in loaded_credential_tabs:
                tab_frame = tab_info.get('frame')
                if not tab_frame: continue
                platform_creds = current_settings.get("credentials", {}).get(platform_name, {})
                
                # Get settings from tab_info if available, otherwise use keys from current_settings
                settings_to_update = tab_info.get('settings', [])
                if not settings_to_update:
                    settings_to_update = list(platform_creds.keys())
                
                for setting_key in settings_to_update:
                    entry_attr = f"{setting_key}_entry"
                    if hasattr(tab_frame, entry_attr):
                        entry = getattr(tab_frame, entry_attr)
                        if isinstance(entry, customtkinter.CTkEntry):
                            try:
                                entry.unbind("<KeyRelease>")
                                current_val = entry.get()
                                new_val = str(platform_creds.get(setting_key, ''))
                                if current_val != new_val:
                                    entry.delete(0, "end")
                                    entry.insert(0, new_val)
                                entry.bind("<KeyRelease>", lambda event, p=platform_name, k=setting_key, w=entry: _auto_save_credential_change(p, k, w))
                            except Exception as e_cred:
                                print(f"Error updating credential widget for {platform_name}.{setting_key}: {e_cred}")
    except Exception as e: print(f"Error during Global/Credential settings UI refresh: {e}"); import traceback; traceback.print_exc()

def _create_credential_tab_content(platform_name, tab_frame):
    """Creates the labels and entry fields for a given platform's credentials."""
    global settings_vars, current_settings, DEFAULT_SETTINGS
    try:
        if 'settings_vars' not in globals() or 'credentials' not in settings_vars: settings_vars['credentials'] = {}
        if platform_name not in settings_vars['credentials']: settings_vars['credentials'][platform_name] = {}
        default_platform_fields = DEFAULT_SETTINGS.get("credentials", {}).get(platform_name, {})

        if not default_platform_fields:
            label = customtkinter.CTkLabel(tab_frame, text=f"No configurable credentials for {platform_name}.")
            label.pack(pady=10, padx=10)
            return
        
        # Deezer / Qobuz / others with "How to" help: pack creds first, then help (expand) so it shows full when maximized.
        deezer_creds_frame = None
        qobuz_creds_frame = None
        other_creds_frame = None
        _platforms_with_help = ("AppleMusic", "Beatport", "Beatsource", "SoundCloud", "Spotify", "Tidal", "YouTube")
        if platform_name == "Deezer":
            deezer_creds_frame = customtkinter.CTkFrame(tab_frame, fg_color="transparent")
            deezer_creds_frame.pack(fill="x", expand=False, anchor="nw")
        if platform_name == "Qobuz":
            qobuz_creds_frame = customtkinter.CTkFrame(tab_frame, fg_color="transparent")
            qobuz_creds_frame.pack(fill="x", expand=False, anchor="nw")
        if platform_name in _platforms_with_help:
            other_creds_frame = customtkinter.CTkFrame(tab_frame, fg_color="transparent")
            # No top pady so first input aligns with Deezer/Qobuz tabs
            other_creds_frame.pack(fill="x", expand=False, anchor="nw")
        if platform_name == "Deezer" and deezer_creds_frame:
            grid_parent = deezer_creds_frame
        elif platform_name == "Qobuz" and qobuz_creds_frame:
            grid_parent = qobuz_creds_frame
        elif other_creds_frame is not None:
            grid_parent = other_creds_frame
        else:
            grid_parent = tab_frame
        
        # Better label names for credential fields
        label_mapping = {
            'download_pause_seconds': 'Pause Between Downloads (seconds)',
            'download_mode': 'Download mode',
            'client_id': 'Client ID',
            'client_secret': 'Client Secret',
        }
        
        for i, (key, value) in enumerate(default_platform_fields.items()):
            if platform_name == "Tidal" and key in ["prefer_ac4", "fix_mqa"]:
                continue
            if platform_name == "Qobuz" and key in ("password", "user_id", "auth_token", "use_id_token"):
                continue
            if platform_name == "Deezer" and key in ("password", "arl", "use_arl"):
                continue

            if i == 0:
                # Adjust top padding for alignment: AppleMusic/YouTube are reference (15), others need +1px (16)
                top_pad = 15 if platform_name in ["AppleMusic", "YouTube"] else 16
                # Adjust bottom padding: AppleMusic needs -1px (4) to reduce gap to next row
                bottom_pad = 4 if platform_name == "AppleMusic" else 5
                # YouTube Cookies Path needs more bottom pad (10) because we hide the warning label now
                if platform_name == "YouTube" and i == 0: bottom_pad = 10
                pady_config = (top_pad, bottom_pad)
            else:
                pady_config = 5
            
            if platform_name == "YouTube" and key == "download_pause_seconds":
                pady_config = (0, 5)
            # Use custom label if available, otherwise generate from key
            label_text = label_mapping.get(key, key.replace('_', ' ').title())
            

            if platform_name == "Qobuz" and key == "username":
                label_text = "Email"

            current_value = current_settings.get("credentials", {}).get(platform_name, {}).get(key, value)

            # Qobuz: checkbox "Use ID/Token" + two rows (Email/ID, Password/Token) with same fields, labels swap by mode; persist use_id_token.
            if platform_name == "Qobuz" and key == "username":
                qobuz_creds = current_settings.get("credentials", {}).get(platform_name, {})
                var_username = tkinter.StringVar(value=str(qobuz_creds.get("username", "") or ""))
                var_password = tkinter.StringVar(value=str(qobuz_creds.get("password", "") or ""))
                var_user_id = tkinter.StringVar(value=str(qobuz_creds.get("user_id", "") or ""))
                var_auth_token = tkinter.StringVar(value=str(qobuz_creds.get("auth_token", "") or ""))
                stored = qobuz_creds.get("use_id_token")
                use_id_token = str(stored).lower() in ("true", "1") if stored not in (None, "") else bool((qobuz_creds.get("user_id") or "").strip() and (qobuz_creds.get("auth_token") or "").strip())
                var_use_id_token = tkinter.BooleanVar(value=use_id_token)
                if platform_name not in settings_vars['credentials']:
                    settings_vars['credentials'][platform_name] = {}
                settings_vars['credentials'][platform_name]["username"] = var_username
                settings_vars['credentials'][platform_name]["password"] = var_password
                settings_vars['credentials'][platform_name]["user_id"] = var_user_id
                settings_vars['credentials'][platform_name]["auth_token"] = var_auth_token
                settings_vars['credentials'][platform_name]["use_id_token"] = var_use_id_token

                # Row 1: Email or ID
                qobuz_label1 = customtkinter.CTkLabel(grid_parent, text="ID:" if use_id_token else "Email:")
                qobuz_label1.grid(row=i, column=0, sticky="w", padx=10, pady=5)
                qobuz_entry1 = customtkinter.CTkEntry(grid_parent)
                qobuz_entry1.grid(row=i, column=1, sticky="ew", padx=10, pady=5)
                qobuz_entry1.configure(textvariable=var_user_id if use_id_token else var_username)
                # Row 2: Password or Token
                qobuz_label2 = customtkinter.CTkLabel(grid_parent, text="Token:" if use_id_token else "Password:")
                qobuz_label2.grid(row=i+1, column=0, sticky="w", padx=10, pady=5)
                qobuz_entry2 = customtkinter.CTkEntry(grid_parent, show="*")
                qobuz_entry2.grid(row=i+1, column=1, sticky="ew", padx=10, pady=5)
                qobuz_entry2.configure(textvariable=var_auth_token if use_id_token else var_password)
                for _entry in (qobuz_entry1, qobuz_entry2):
                    _entry.bind("<Button-3>", show_context_menu)
                    _entry.bind("<Button-2>", show_context_menu)
                    _entry.bind("<Control-Button-1>", show_context_menu)
                    _entry.bind("<Control-c>", _handle_ctrl_c_copy)
                    _entry.bind("<Control-C>", _handle_ctrl_c_copy)
                    if _entry is qobuz_entry2:
                        _entry.bind("<FocusIn>", lambda e, w=_entry: _masked_entry_focus_in(w))
                        _entry.bind("<FocusOut>", lambda e, w=_entry: _masked_entry_focus_out(w))
                    else:
                        _entry.bind("<FocusIn>", lambda e, w=_entry: handle_focus_in(w))
                        _entry.bind("<FocusOut>", lambda e, w=_entry: handle_focus_out(w))
                # Checkbox below help section (packed in Qobuz help block)
                chk_container = customtkinter.CTkFrame(tab_frame, fg_color="transparent")
                chk_qobuz_id_token = customtkinter.CTkCheckBox(chk_container, text="Use ID/Token (instead of Email/Password)", variable=var_use_id_token)

                def _qobuz_toggle_id_token():
                    use_id = var_use_id_token.get()
                    qobuz_label1.configure(text="ID:" if use_id else "Email:")
                    qobuz_label2.configure(text="Token:" if use_id else "Password:")
                    qobuz_entry2.configure(show="" if use_id else "*")
                    qobuz_entry1.configure(textvariable=var_user_id if use_id else var_username)
                    qobuz_entry2.configure(textvariable=var_auth_token if use_id else var_password)
                    if hasattr(tab_frame, "qobuz_help_update"):
                        tab_frame.qobuz_help_update(use_id)

                chk_qobuz_id_token.pack(side="left")
                chk_qobuz_id_token.configure(command=_qobuz_toggle_id_token)
                tab_frame.qobuz_chk_frame = chk_container
                grid_parent.grid_columnconfigure(1, weight=1)
                continue

            # Deezer: checkbox "Use ARL" + Email/Password vs ARL. Hide Password only when Use ARL checked; persist use_arl.
            if platform_name == "Deezer" and key == "email":
                deezer_creds = current_settings.get("credentials", {}).get(platform_name, {})
                var_email = tkinter.StringVar(value=str(deezer_creds.get("email", "") or ""))
                var_password = tkinter.StringVar(value=str(deezer_creds.get("password", "") or ""))
                var_arl = tkinter.StringVar(value=str(deezer_creds.get("arl", "") or ""))
                stored = deezer_creds.get("use_arl")
                use_arl = str(stored).lower() in ("true", "1") if stored not in (None, "") else bool((deezer_creds.get("arl") or "").strip())
                var_use_arl = tkinter.BooleanVar(value=use_arl)
                if platform_name not in settings_vars['credentials']:
                    settings_vars['credentials'][platform_name] = {}
                settings_vars['credentials'][platform_name]["email"] = var_email
                settings_vars['credentials'][platform_name]["password"] = var_password
                settings_vars['credentials'][platform_name]["arl"] = var_arl
                settings_vars['credentials'][platform_name]["use_arl"] = var_use_arl

                deezer_label1 = customtkinter.CTkLabel(grid_parent, text="ARL:" if use_arl else "Email:")
                deezer_label1.grid(row=i, column=0, sticky="w", padx=10, pady=5)
                deezer_entry1 = customtkinter.CTkEntry(grid_parent, show="*" if use_arl else "")
                deezer_entry1.grid(row=i, column=1, sticky="ew", padx=10, pady=5)
                deezer_entry1.configure(textvariable=var_arl if use_arl else var_email)
                deezer_label2 = customtkinter.CTkLabel(grid_parent, text="Password:")
                deezer_label2.grid(row=i+1, column=0, sticky="w", padx=10, pady=5)
                deezer_entry2 = customtkinter.CTkEntry(grid_parent, show="*")
                deezer_entry2.grid(row=i+1, column=1, sticky="ew", padx=10, pady=5)
                deezer_entry2.configure(textvariable=var_password)
                def _deezer_entry1_focus_in(e):
                    if var_use_arl.get():
                        _masked_entry_focus_in(deezer_entry1)
                    else:
                        handle_focus_in(deezer_entry1)
                def _deezer_entry1_focus_out(e):
                    if var_use_arl.get():
                        _masked_entry_focus_out(deezer_entry1)
                    else:
                        handle_focus_out(deezer_entry1)
                for _entry in (deezer_entry1, deezer_entry2):
                    _entry.bind("<Button-3>", show_context_menu)
                    _entry.bind("<Button-2>", show_context_menu)
                    _entry.bind("<Control-Button-1>", show_context_menu)
                    _entry.bind("<Control-c>", _handle_ctrl_c_copy)
                    _entry.bind("<Control-C>", _handle_ctrl_c_copy)
                    if _entry is deezer_entry2:
                        _entry.bind("<FocusIn>", lambda e, w=_entry: _masked_entry_focus_in(w))
                        _entry.bind("<FocusOut>", lambda e, w=_entry: _masked_entry_focus_out(w))
                    else:
                        _entry.bind("<FocusIn>", _deezer_entry1_focus_in)
                        _entry.bind("<FocusOut>", _deezer_entry1_focus_out)
                chk_deezer_arl = customtkinter.CTkFrame(tab_frame, fg_color="transparent")
                chk_use_arl = customtkinter.CTkCheckBox(chk_deezer_arl, text="Use ARL (instead of Email/Password)", variable=var_use_arl)

                def _deezer_toggle_arl():
                    use_a = var_use_arl.get()
                    deezer_label1.configure(text="ARL:" if use_a else "Email:")
                    deezer_entry1.configure(textvariable=var_arl if use_a else var_email, show="*" if use_a else "")
                    if use_a:
                        deezer_label2.grid_remove()
                        deezer_entry2.grid_remove()
                    else:
                        deezer_entry2.configure(show="*", textvariable=var_password)
                        deezer_label2.grid(row=i+1, column=0, sticky="w", padx=10, pady=5)
                        deezer_entry2.grid(row=i+1, column=1, sticky="ew", padx=10, pady=5)
                    if hasattr(tab_frame, "deezer_help_update"):
                        tab_frame.deezer_help_update(use_a)

                chk_use_arl.pack(side="left")
                chk_use_arl.configure(command=_deezer_toggle_arl)
                tab_frame.deezer_chk_frame = chk_deezer_arl
                grid_parent.grid_columnconfigure(1, weight=1)
                if use_arl:
                    _deezer_toggle_arl()
                continue

            label = customtkinter.CTkLabel(grid_parent, text=f"{label_text}")
            label.grid(row=i, column=0, sticky="w", padx=10, pady=pady_config)

            if platform_name == "Tidal" and key == "enable_mobile":
                # Create container for horizontal checkboxes
                container = customtkinter.CTkFrame(grid_parent, fg_color="transparent")
                # Increased top padding as requested by user
                container.grid(row=i, column=1, sticky="w", padx=10, pady=(5, 5))
                
                # Enable Mobile
                var_mobile = tkinter.BooleanVar(value=current_value)
                chk_mobile = customtkinter.CTkCheckBox(container, text="Enable Mobile", variable=var_mobile)
                chk_mobile.pack(side="left", padx=(0, 15))
                
                # Prefer Ac4 (unchecked = E-AC-3 JOC, plays in VLC/Audacity; checked = AC-4, may need special player)
                val_ac4 = current_settings.get("credentials", {}).get(platform_name, {}).get("prefer_ac4", False)
                var_ac4 = tkinter.BooleanVar(value=val_ac4)
                chk_ac4 = customtkinter.CTkCheckBox(container, text="Prefer Ac4", variable=var_ac4)
                chk_ac4.pack(side="left", padx=(0, 15))
                CTkToolTip(chk_ac4, message="Unchecked: E-AC-3 JOC (Dolby Atmos), plays in VLC and Audacity.\nChecked: AC-4, may require a player with AC-4 support.", bg_color=TOOLTIP_MENU_BG, text_color=LIGHT_TEXT_COLOR)
                
                # Fix MQA
                val_mqa = current_settings.get("credentials", {}).get(platform_name, {}).get("fix_mqa", True)
                var_mqa = tkinter.BooleanVar(value=val_mqa)
                chk_mqa = customtkinter.CTkCheckBox(container, text="Fix MQA", variable=var_mqa)
                chk_mqa.pack(side="left")
                
                # Register variables
                if platform_name not in settings_vars['credentials']:
                    settings_vars['credentials'][platform_name] = {}
                
                settings_vars['credentials'][platform_name]["enable_mobile"] = var_mobile
                settings_vars['credentials'][platform_name]["prefer_ac4"] = var_ac4
                settings_vars['credentials'][platform_name]["fix_mqa"] = var_mqa
                
                # Hide the label for this row since we have internal labels
                label.grid_forget()
                
                # Bind events for all
                for w in [chk_mobile, chk_ac4, chk_mqa]:
                    w.bind("<Button-3>", show_context_menu)
                    w.bind("<Button-2>", show_context_menu)
                    w.bind("<Control-Button-1>", show_context_menu)
                
                continue

            if platform_name == "YouTube" and key == "download_mode":
                # Radio buttons for Sequential vs Concurrent downloads
                download_options = ["sequential", "concurrent"]
                current_value = current_settings.get("credentials", {}).get(platform_name, {}).get(key, value)
                # Handle migration from boolean to string
                if current_value is True or str(current_value).lower() == "true":
                    current_value = "sequential"
                elif current_value is False or str(current_value).lower() == "false":
                    current_value = "concurrent"
                
                if str(current_value) not in download_options:
                    current_value = "sequential"
                
                var = tkinter.StringVar(value=str(current_value))
                
                radio_frame = customtkinter.CTkFrame(grid_parent, fg_color="transparent")
                radio_frame.grid(row=i, column=1, sticky="w", padx=10, pady=pady_config)
                
                sequential_radio = customtkinter.CTkRadioButton(radio_frame, text="Sequential", variable=var, value="sequential")
                sequential_radio.pack(side="left", padx=(0, 10))
                
                concurrent_radio = customtkinter.CTkRadioButton(radio_frame, text="Concurrent", variable=var, value="concurrent")
                concurrent_radio.pack(side="left")
                
                widget = radio_frame
                
                # Add tooltip explaining the options
                CTkToolTip(radio_frame, message="Sequential: Downloads one track at a time with pause between tracks (safer, shows pause messages)\nConcurrent: Downloads multiple tracks at once (faster, higher rate limiting risk)", bg_color=TOOLTIP_MENU_BG, text_color=LIGHT_TEXT_COLOR)
                
                if platform_name not in settings_vars['credentials']:
                    settings_vars['credentials'][platform_name] = {}
                settings_vars['credentials'][platform_name]["download_mode"] = var
                continue
                
            elif isinstance(value, bool):
                var = tkinter.BooleanVar(value=current_value)
                widget = customtkinter.CTkCheckBox(grid_parent, text="", variable=var)
                widget.grid(row=i, column=1, sticky="w", padx=10, pady=pady_config)


            elif platform_name == "YouTube" and key == "cookies_path":
                # Fix alignment for tall row (due to warning label)
                # Align to top (nw) to match the input field which is at the top of the container
                # User requested 1px lower for label and input
                current_pady_top = pady_config[0] if isinstance(pady_config, tuple) else pady_config
                current_pady_bottom = pady_config[1] if isinstance(pady_config, tuple) else pady_config
                adjusted_pady = (current_pady_top + 1, current_pady_bottom)
                
                label.grid_configure(sticky="nw", pady=adjusted_pady)

                # Check for default cookies file if current value is empty
                if not current_value:
                    current_value = "./config/youtube-cookies.txt"
                
                var = tkinter.StringVar(value=str(current_value))
                
                # Container for entry and warning label
                container = customtkinter.CTkFrame(grid_parent, fg_color="transparent")
                container.grid(row=i, column=1, sticky="ew", padx=(10, 5), pady=adjusted_pady)
                container.grid_columnconfigure(0, weight=1)

                widget = customtkinter.CTkEntry(container)
                widget.configure(textvariable=var)
                widget.grid(row=0, column=0, sticky="ew")
                widget.bind("<Button-3>", show_context_menu)
                widget.bind("<Button-2>", show_context_menu)
                widget.bind("<Control-Button-1>", show_context_menu)
                widget.bind("<Control-c>", _handle_ctrl_c_copy)
                widget.bind("<Control-C>", _handle_ctrl_c_copy)
                widget.bind("<FocusIn>", lambda e, w=widget: handle_focus_in(w))
                widget.bind("<FocusOut>", lambda e, w=widget: handle_focus_out(w))
                
                warning_label = customtkinter.CTkLabel(container, text="", text_color=ERROR_COLOR, font=("Segoe UI", 10), anchor="w", height=12)
                warning_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

                def check_cookies_path(*args, var_ref=var):
                    path = var_ref.get()
                    exists = False
                    if path:
                        if os.path.exists(path):
                            exists = True
                        elif not os.path.isabs(path):
                            # Try resolving relative to CWD/config if not explicitly ./ or .\
                            if not (path.startswith('./') or path.startswith('.\\')):
                                config_path = os.path.join("config", path)
                                if os.path.exists(config_path):
                                    exists = True
                            
                            # Also try absolute resolution of the raw path
                            abs_path = os.path.abspath(path)
                            if os.path.exists(abs_path):
                                exists = True

                    if not exists:
                        warning_label.configure(text="File not found")
                        warning_label.grid() # Show label
                    else:
                        warning_label.configure(text="")
                        warning_label.grid_remove() # Hide label to save space
                
                var.trace_add("write", check_cookies_path)
                check_cookies_path()

                # Store the check function so it can be called externally (e.g. on save)
                if platform_name not in settings_vars['credentials']:
                    settings_vars['credentials'][platform_name] = {}
                settings_vars['credentials'][platform_name]['_check_cookies_func'] = check_cookies_path

                # For Apple Music and YouTube cookies_path, add Open button like Browse in Global settings
                def open_cookies_folder():
                    """Open the config folder in file explorer (uses CONFIG_DIR so macOS opens Application Support, not .app bundle)."""
                    config_dir = os.path.dirname(CONFIG_FILE_PATH)
                    if not os.path.exists(config_dir):
                        try:
                            os.makedirs(config_dir, exist_ok=True)
                        except Exception as e:
                            show_centered_messagebox("Error", f"Could not create config directory:\n{e}", dialog_type="error")
                            return
                    try:
                        if platform.system() == "Windows":
                            os.startfile(config_dir)
                        elif platform.system() == "Darwin":  # macOS
                            subprocess.run(["open", config_dir])
                        else:  # Linux
                            subprocess.run(["xdg-open", config_dir])
                    except Exception as e:
                        show_centered_messagebox("Error", f"Could not open config folder:\n{e}", dialog_type="error")

                open_button = customtkinter.CTkButton(
                    grid_parent,
                    text="Open",
                    width=100,
                    height=30,
                    command=open_cookies_folder,
                    fg_color=BUTTON_COLOR,
                    hover_color="#1F6AA5",
                    border_width=0,
                    border_color=None
                )
                open_button.grid(row=i, column=2, sticky="ne", padx=(5, 5), pady=pady_config)
                
                # Ensure column 1 expands
                grid_parent.grid_columnconfigure(1, weight=1)
                
                # Register variable for saving
                if platform_name not in settings_vars['credentials']:
                    settings_vars['credentials'][platform_name] = {}
                settings_vars['credentials'][platform_name][key] = var
                
                continue # Skip default widget creation
            else:
                var = tkinter.StringVar(value=str(current_value))
                widget = customtkinter.CTkEntry(grid_parent)
                widget.configure(textvariable=var)
                _is_masked_field = key == "password" or (key == "client_secret" and platform_name == "Spotify") or (key == "web_access_token" and platform_name == "SoundCloud")
                if _is_masked_field:
                    widget.configure(show="*")
                
                # For Apple Music and YouTube cookies_path, add Open button like Browse in Global settings
                if (platform_name == "AppleMusic" or platform_name == "YouTube") and key == "cookies_path":
                    # Use padx=(10, 5) to align left with other fields (10) and spacing for button
                    widget.grid(row=i, column=1, sticky="ew", padx=(10, 5), pady=pady_config)
                    def open_cookies_folder():
                        """Open the config folder in file explorer (uses CONFIG_DIR so macOS opens Application Support, not .app bundle)."""
                        config_dir = os.path.dirname(CONFIG_FILE_PATH)
                        if not os.path.exists(config_dir):
                            try:
                                os.makedirs(config_dir, exist_ok=True)
                            except Exception as e:
                                show_centered_messagebox("Error", f"Could not create config directory:\n{e}", dialog_type="error")
                                return
                        try:
                            if platform.system() == "Windows":
                                os.startfile(config_dir)
                            elif platform.system() == "Darwin":  # macOS
                                subprocess.run(["open", config_dir])
                            else:  # Linux
                                subprocess.run(["xdg-open", config_dir])
                        except Exception as e:
                            show_centered_messagebox("Error", f"Could not open config folder:\n{e}", dialog_type="error")
                    
                    open_button = customtkinter.CTkButton(
                        grid_parent,
                        text="Open",
                        width=100,
                        height=30,
                        command=open_cookies_folder,
                        fg_color=widget._fg_color,
                        hover_color="#1F6AA5",
                        border_width=0,
                        border_color=None
                    )
                    # Align right with Save button (same 5px right padding as save_controls_frame)
                    open_button.grid(row=i, column=2, sticky="e", padx=(5, 5), pady=pady_config)
                elif platform_name == "AppleMusic":
                    # Match cookies_path width by using same column and padding layout
                    widget.grid(row=i, column=1, sticky="ew", padx=(10, 5), pady=pady_config)
                elif platform_name == "YouTube" and key == "download_pause_seconds":
                     # Match padding of Cookies Path (10, 5) so widths align
                     widget.grid(row=i, column=1, sticky="ew", padx=(10, 5), pady=pady_config)
                else:
                    # For all other fields/platforms, use default layout (just under each other)
                    widget.grid(row=i, column=1, sticky="ew", padx=10, pady=pady_config)
                
                grid_parent.grid_columnconfigure(1, weight=1)
                widget.bind("<Button-3>", show_context_menu)
                widget.bind("<Button-2>", show_context_menu)
                widget.bind("<Control-Button-1>", show_context_menu)
                widget.bind("<Control-c>", _handle_ctrl_c_copy)
                widget.bind("<Control-C>", _handle_ctrl_c_copy)
                if _is_masked_field:
                    widget.bind("<FocusIn>", lambda e, w=widget: _masked_entry_focus_in(w))
                    widget.bind("<FocusOut>", lambda e, w=widget: _masked_entry_focus_out(w))
                else:
                    widget.bind("<FocusIn>", lambda e, w=widget: handle_focus_in(w))
                    widget.bind("<FocusOut>", lambda e, w=widget: handle_focus_out(w))
            
            if platform_name not in settings_vars['credentials']:
                settings_vars['credentials'][platform_name] = {}
            settings_vars['credentials'][platform_name][key] = var
            # Auto-save disabled - settings only save when user clicks "Save" button
            # if isinstance(var, (tkinter.StringVar, tkinter.BooleanVar)):
            #     var.trace_add('write', _auto_save_credential_change)
        
        # Add help text for Spotify module
        if platform_name == "Spotify":
            # Helper function to copy URL to clipboard with feedback (persistent)
            def _copy_url_to_clipboard(url, button):
                try:
                    # Use persistent clipboard so it survives app close
                    if not _copy_to_system_clipboard(url):
                        # Fall back to Tkinter clipboard
                        app.clipboard_clear()
                        app.clipboard_append(url)
                        app.update()
                    # Show "Copied" feedback
                    original_text = button.cget("text")
                    button.configure(text="✓")
                    button.after(1500, lambda: button.configure(text=original_text))
                except Exception as e:
                    print(f"Error copying to clipboard: {e}")
            
            help_frame = customtkinter.CTkFrame(tab_frame, fg_color="#1D1E1E", corner_radius=5)
            help_frame.pack(fill="both", expand=True, padx=3, pady=(10, 5), anchor="nw")
            help_frame.grid_columnconfigure(0, weight=1)
            
            # --- Single Column: How to set up ---
            left_col = customtkinter.CTkFrame(help_frame, fg_color="transparent")
            left_col.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            
            # Header
            left_header = customtkinter.CTkFrame(left_col, fg_color="transparent")
            left_header.pack(anchor="w", pady=(0, 15))
            
            icon_label = customtkinter.CTkLabel(
                left_header, 
                text="💡", 
                font=("Segoe UI", 20), 
                text_color=WARNING_COLOR
            )
            icon_label.pack(side="left", padx=(5, 10))
            
            title_label = customtkinter.CTkLabel(
                left_header, 
                text="How to set up", 
                font=("Segoe UI", 16, "bold"), 
                text_color="#DCE4EE"
            )
            title_label.pack(side="left")
            
            # Instructions
            # Step 1
            step1_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step1_frame.pack(anchor="w", pady=(0, 5))
            
            customtkinter.CTkLabel(step1_frame, text="1.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            
            step1_text_frame = customtkinter.CTkFrame(step1_frame, fg_color="transparent")
            step1_text_frame.pack(side="left")
            
            customtkinter.CTkLabel(step1_text_frame, text="Log in to ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            dashboard_link = customtkinter.CTkLabel(step1_text_frame, text="Spotify Dashboard", font=("Segoe UI", 12, "underline"), text_color=LINK_COLOR, cursor=HAND_CURSOR)
            dashboard_link.pack(side="left")
            dashboard_link.bind("<Button-1>", lambda e: webbrowser.open("https://developer.spotify.com/dashboard"))
            dashboard_link.bind("<Enter>", lambda e: dashboard_link.configure(text_color=LINK_HOVER_COLOR))
            dashboard_link.bind("<Leave>", lambda e: dashboard_link.configure(text_color=LINK_COLOR))
            
            customtkinter.CTkLabel(step1_text_frame, text=" ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            customtkinter.CTkLabel(step1_text_frame, text="(active Premium subscription required)", font=("Segoe UI", 12, "italic"), text_color="gray").pack(side="left")
            
            # Step 2
            step2_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step2_frame.pack(anchor="w", pady=(0, 5))
            
            customtkinter.CTkLabel(step2_frame, text="2.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step2_frame, text="Take over username & fill in above", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            # Step 3
            step3_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step3_frame.pack(anchor="w", pady=(0, 5))
            
            customtkinter.CTkLabel(step3_frame, text="3.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step3_frame, text="In the dashboard, create an app (or use existing one)", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            # Step 4
            step4_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step4_frame.pack(anchor="w", pady=(0, 5))
            
            customtkinter.CTkLabel(step4_frame, text="4.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            
            step4_text_frame = customtkinter.CTkFrame(step4_frame, fg_color="transparent")
            step4_text_frame.pack(side="left")
            
            customtkinter.CTkLabel(step4_text_frame, text="Add Redirect URI ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            copy_url = "http://127.0.0.1:4381/login"
            url_label = customtkinter.CTkLabel(step4_text_frame, text=copy_url, font=("Segoe UI", 11), text_color=LINK_COLOR)
            url_label.pack(side="left", padx=(0, 4))
            
            copy_button = customtkinter.CTkButton(
                step4_text_frame,
                text="⧉",
                width=24,
                height=24,
                font=("Segoe UI", 14),
                fg_color="#2B2B2B",
                hover_color="#3B3B3B",
                text_color="gray",
                corner_radius=3,
                command=lambda: _copy_url_to_clipboard(copy_url, copy_button)
            )
            copy_button.pack(side="left")
            copy_button.bind("<Enter>", lambda e: copy_button.configure(text_color=WHITE_TEXT_COLOR))
            copy_button.bind("<Leave>", lambda e: copy_button.configure(text_color="gray"))

            # Step 5
            step5_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step5_frame.pack(anchor="w", pady=0)
            
            customtkinter.CTkLabel(step5_frame, text="5.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="s")
            
            step5_text_frame = customtkinter.CTkFrame(step5_frame, fg_color="transparent")
            step5_text_frame.pack(side="left", anchor="w")
            # Use anchor="s" so labels share the same baseline (avoids vertical drift)
            customtkinter.CTkLabel(step5_text_frame, text="Save → Copy ", font=("Segoe UI", 12), text_color="gray").pack(side="left", anchor="s")
            customtkinter.CTkLabel(step5_text_frame, text="Client ID", font=("Segoe UI", 12), text_color=LINK_COLOR).pack(side="left", anchor="s")
            customtkinter.CTkLabel(step5_text_frame, text=" + ", font=("Segoe UI", 12), text_color="gray").pack(side="left", anchor="s")
            customtkinter.CTkLabel(step5_text_frame, text="Secret", font=("Segoe UI", 12), text_color=LINK_COLOR).pack(side="left", anchor="s")
            customtkinter.CTkLabel(step5_text_frame, text=", paste them above — Save.", font=("Segoe UI", 12), text_color="gray").pack(side="left", anchor="s")
            
            _add_clear_session_icon(help_frame, "Spotify")
        
        # Add help text for Apple Music module
        if platform_name == "AppleMusic":
            help_frame = customtkinter.CTkFrame(tab_frame, fg_color="#1D1E1E", corner_radius=5)
            help_frame.pack(fill="both", expand=True, padx=3, pady=(10, 5), anchor="nw")
            help_frame.grid_columnconfigure(0, weight=1)
            
            # --- Single Column: How to set up ---
            left_col = customtkinter.CTkFrame(help_frame, fg_color="transparent")
            left_col.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            
            # Header
            left_header = customtkinter.CTkFrame(left_col, fg_color="transparent")
            left_header.pack(anchor="w", pady=(0, 15))
            
            icon_label = customtkinter.CTkLabel(
                left_header, 
                text="💡", 
                font=("Segoe UI", 20), 
                text_color=WARNING_COLOR
            )
            icon_label.pack(side="left", padx=(5, 10))
            
            title_label = customtkinter.CTkLabel(
                left_header, 
                text="How to set up", 
                font=("Segoe UI", 16, "bold"), 
                text_color="#DCE4EE"
            )
            title_label.pack(side="left")
            
            # Instructions
            # Step 1
            step1_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step1_frame.pack(anchor="w", pady=0)
            
            customtkinter.CTkLabel(step1_frame, text="1.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step1_frame, text="Install extension", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            # Step 1 bullets
            step1_bullets_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step1_bullets_frame.pack(anchor="w", pady=(0, 5))
            customtkinter.CTkLabel(step1_bullets_frame, text="", width=35).pack(side="left") # Indent
            
            customtkinter.CTkLabel(step1_bullets_frame, text="• Chrome / Edge → ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            chrome_link = customtkinter.CTkLabel(step1_bullets_frame, text="Get cookies.txt", font=("Segoe UI", 12, "underline"), text_color=LINK_COLOR, cursor=HAND_CURSOR)
            chrome_link.pack(side="left")
            chrome_link.bind("<Button-1>", lambda e: webbrowser.open("https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc?pli=1"))
            chrome_link.bind("<Enter>", lambda e: chrome_link.configure(text_color=LINK_HOVER_COLOR))
            chrome_link.bind("<Leave>", lambda e: chrome_link.configure(text_color=LINK_COLOR))
            
            customtkinter.CTkLabel(step1_bullets_frame, text=" or Firefox → ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            firefox_link = customtkinter.CTkLabel(step1_bullets_frame, text="cookies.txt", font=("Segoe UI", 12, "underline"), text_color=LINK_COLOR, cursor=HAND_CURSOR)
            firefox_link.pack(side="left")
            firefox_link.bind("<Button-1>", lambda e: webbrowser.open("https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/"))
            firefox_link.bind("<Enter>", lambda e: firefox_link.configure(text_color=LINK_HOVER_COLOR))
            firefox_link.bind("<Leave>", lambda e: firefox_link.configure(text_color=LINK_COLOR))

            # Step 2
            step2_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step2_frame.pack(anchor="w", pady=0)
            
            customtkinter.CTkLabel(step2_frame, text="2.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            
            step2_text_frame = customtkinter.CTkFrame(step2_frame, fg_color="transparent")
            step2_text_frame.pack(side="left")
            
            customtkinter.CTkLabel(step2_text_frame, text="Log in to ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            apple_link = customtkinter.CTkLabel(step2_text_frame, text="Apple Music", font=("Segoe UI", 12, "underline"), text_color=LINK_COLOR, cursor=HAND_CURSOR)
            apple_link.pack(side="left")
            apple_link.bind("<Button-1>", lambda e: webbrowser.open("https://music.apple.com"))
            apple_link.bind("<Enter>", lambda e: apple_link.configure(text_color=LINK_HOVER_COLOR))
            apple_link.bind("<Leave>", lambda e: apple_link.configure(text_color=LINK_COLOR))
            
            customtkinter.CTkLabel(step2_text_frame, text=" ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            customtkinter.CTkLabel(step2_text_frame, text="(active subscription required)", font=("Segoe UI", 12, "italic"), text_color="gray").pack(side="left")

            # Step 3
            step3_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step3_frame.pack(anchor="w", pady=(5, 0))
            
            customtkinter.CTkLabel(step3_frame, text="3.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step3_frame, text="Export & save as cookies.txt", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            # Step 3 Path
            step3_path_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step3_path_frame.pack(anchor="w", pady=(0, 5))
            customtkinter.CTkLabel(step3_path_frame, text="", width=35).pack(side="left") # Indent
            customtkinter.CTkLabel(step3_path_frame, text="Path: ", font=("Segoe UI", 12, "italic"), text_color="gray").pack(side="left")
            customtkinter.CTkLabel(step3_path_frame, text="./config/cookies.txt", font=("Segoe UI", 12, "italic"), text_color="gray").pack(side="left")
            
            _add_clear_session_icon(help_frame, "AppleMusic")
        
        # Add help text for YouTube module
        if platform_name == "YouTube":
            help_frame = customtkinter.CTkFrame(tab_frame, fg_color="#1D1E1E", corner_radius=5)
            help_frame.pack(fill="both", expand=True, padx=3, pady=(10, 5), anchor="nw")
            help_frame.grid_columnconfigure(0, weight=1, uniform="help_cols")
            help_frame.grid_columnconfigure(1, weight=1, uniform="help_cols")
            
            # --- Header (Spans both columns) ---
            header_frame = customtkinter.CTkFrame(help_frame, fg_color="transparent")
            header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))
            
            icon_label = customtkinter.CTkLabel(
                header_frame, 
                text="💡", 
                font=("Segoe UI", 20), 
                text_color=WARNING_COLOR
            )
            icon_label.pack(side="left", padx=(5, 10), anchor="n")
            
            # Text Frame for Title + Subtitle
            header_text_frame = customtkinter.CTkFrame(header_frame, fg_color="transparent")
            header_text_frame.pack(side="left", anchor="w")
            
            title_label = customtkinter.CTkLabel(
                header_text_frame, 
                text="How to set up", 
                font=("Segoe UI", 16, "bold"), 
                text_color="#DCE4EE"
            )
            title_label.pack(anchor="w")

            subtitle_label = customtkinter.CTkLabel(
                header_text_frame, 
                text="(Recommended: to prevent 403 errors / for age-restricted content)", 
                font=("Segoe UI", 12), 
                text_color="#DCE4EE"
            )
            subtitle_label.pack(anchor="w")

            # --- Left Column: Steps 1 & 2 ---
            left_col = customtkinter.CTkFrame(help_frame, fg_color="transparent")
            left_col.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
            
            # Instructions
            
            # Step 1: Install extension
            step1_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step1_frame.pack(anchor="w", pady=0)
            
            customtkinter.CTkLabel(step1_frame, text="1.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step1_frame, text="Install extension", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            # Step 1 bullets
            step1_bullets_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step1_bullets_frame.pack(anchor="w", pady=(0, 5))
            customtkinter.CTkLabel(step1_bullets_frame, text="", width=35).pack(side="left") # Indent
            
            customtkinter.CTkLabel(step1_bullets_frame, text="• Chrome / Edge → ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            chrome_link = customtkinter.CTkLabel(step1_bullets_frame, text="Get cookies.txt", font=("Segoe UI", 12, "underline"), text_color=LINK_COLOR, cursor=HAND_CURSOR)
            chrome_link.pack(side="left")
            chrome_link.bind("<Button-1>", lambda e: webbrowser.open("https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc?pli=1"))
            chrome_link.bind("<Enter>", lambda e: chrome_link.configure(text_color=LINK_HOVER_COLOR))
            chrome_link.bind("<Leave>", lambda e: chrome_link.configure(text_color=LINK_COLOR))
            
            customtkinter.CTkLabel(step1_bullets_frame, text=" or Firefox → ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            firefox_link = customtkinter.CTkLabel(step1_bullets_frame, text="cookies.txt", font=("Segoe UI", 12, "underline"), text_color=LINK_COLOR, cursor=HAND_CURSOR)
            firefox_link.pack(side="left")
            firefox_link.bind("<Button-1>", lambda e: webbrowser.open("https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/"))
            firefox_link.bind("<Enter>", lambda e: firefox_link.configure(text_color=LINK_HOVER_COLOR))
            firefox_link.bind("<Leave>", lambda e: firefox_link.configure(text_color=LINK_COLOR))

            # Step 2: Open Private / Incognito
            step2_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step2_frame.pack(anchor="w", pady=0)
            
            customtkinter.CTkLabel(step2_frame, text="2.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step2_frame, text='Manage extension → Enable \'Allow in incognito / private window\'', font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            # Step 3: Open a new private / incognito window
            step3_incognito_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step3_incognito_frame.pack(anchor="w", pady=0)
            customtkinter.CTkLabel(step3_incognito_frame, text="3.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step3_incognito_frame, text="Open a new private / incognito window", font=("Segoe UI", 12), text_color="gray").pack(side="left")

            # Helper function to copy value to clipboard with feedback (persistent)
            def _copy_youtube_value(value, button):
                try:
                    # Use persistent clipboard so it survives app close
                    if not _copy_to_system_clipboard(value):
                        # Fall back to Tkinter clipboard
                        app.clipboard_clear()
                        app.clipboard_append(value)
                        app.update()
                    # Show "Copied" feedback
                    original_text = button.cget("text")
                    button.configure(text="✓")
                    button.after(1500, lambda: button.configure(text=original_text))
                except Exception as e:
                    print(f"Error copying to clipboard: {e}")

            # --- Right Column: Steps 4, 5, 6 ---
            right_col = customtkinter.CTkFrame(help_frame, fg_color="transparent")
            right_col.grid(row=1, column=1, sticky="nsew", padx=20, pady=(0, 20))

            # Step 4: Log in to YouTube
            step4_frame = customtkinter.CTkFrame(right_col, fg_color="transparent")
            step4_frame.pack(anchor="w", pady=0)
            
            customtkinter.CTkLabel(step4_frame, text="4.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            
            step4_text_frame = customtkinter.CTkFrame(step4_frame, fg_color="transparent")
            step4_text_frame.pack(side="left")
            
            customtkinter.CTkLabel(step4_text_frame, text="Log in to ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            youtube_link = customtkinter.CTkLabel(step4_text_frame, text="YouTube", font=("Segoe UI", 12, "underline"), text_color=LINK_COLOR, cursor=HAND_CURSOR)
            youtube_link.pack(side="left", padx=(0, 4))
            youtube_link.bind("<Button-1>", lambda e: show_centered_messagebox("YouTube", "Open https://youtube.com in a private / incognito window of your browser.", dialog_type="info"))
            youtube_link.bind("<Enter>", lambda e: youtube_link.configure(text_color=LINK_HOVER_COLOR))
            youtube_link.bind("<Leave>", lambda e: youtube_link.configure(text_color=LINK_COLOR))
            
            youtube_copy_btn = customtkinter.CTkButton(
                step4_text_frame,
                text="⧉",
                width=24,
                height=24,
                font=("Segoe UI", 14),
                fg_color="#2B2B2B",
                hover_color="#3B3B3B",
                text_color="gray",
                corner_radius=3,
                command=lambda: _copy_youtube_value("https://youtube.com", youtube_copy_btn)
            )
            youtube_copy_btn.pack(side="left")
            youtube_copy_btn.bind("<Enter>", lambda e: youtube_copy_btn.configure(text_color=WHITE_TEXT_COLOR))
            youtube_copy_btn.bind("<Leave>", lambda e: youtube_copy_btn.configure(text_color="gray"))
            
            # Step 4 sub-point (robots.txt)
            step4_sub_frame = customtkinter.CTkFrame(right_col, fg_color="transparent")
            step4_sub_frame.pack(anchor="w", pady=(0, 5))
            customtkinter.CTkLabel(step4_sub_frame, text="", width=35).pack(side="left") # Indent
            
            customtkinter.CTkLabel(step4_sub_frame, text="In same tab open: ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            step4_value = "youtube.com/robots.txt"
            customtkinter.CTkLabel(step4_sub_frame, text=step4_value, font=("Segoe UI", 12), text_color=LINK_COLOR).pack(side="left", padx=(0, 4))
            
            step4_copy_btn = customtkinter.CTkButton(
                step4_sub_frame,
                text="⧉",
                width=24,
                height=24,
                font=("Segoe UI", 14),
                fg_color="#2B2B2B",
                hover_color="#3B3B3B",
                text_color="gray",
                corner_radius=3,
                command=lambda: _copy_youtube_value("https://www.youtube.com/robots.txt", step4_copy_btn)
            )
            step4_copy_btn.pack(side="left")
            step4_copy_btn.bind("<Enter>", lambda e: step4_copy_btn.configure(text_color=WHITE_TEXT_COLOR))
            step4_copy_btn.bind("<Leave>", lambda e: step4_copy_btn.configure(text_color="gray"))

            # Step 5: Export & save
            step5_frame = customtkinter.CTkFrame(right_col, fg_color="transparent")
            step5_frame.pack(anchor="w", pady=0)
            
            customtkinter.CTkLabel(step5_frame, text="5.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step5_frame, text="Export & save as youtube-cookies.txt", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            # Step 5 Path
            step5_path_frame = customtkinter.CTkFrame(right_col, fg_color="transparent")
            step5_path_frame.pack(anchor="w", pady=(0, 5))
            customtkinter.CTkLabel(step5_path_frame, text="", width=35).pack(side="left") # Indent
            customtkinter.CTkLabel(step5_path_frame, text="Path: ", font=("Segoe UI", 12, "italic"), text_color="gray").pack(side="left")
            customtkinter.CTkLabel(step5_path_frame, text="./config/youtube-cookies.txt", font=("Segoe UI", 12, "italic"), text_color="gray").pack(side="left")

            # Step 6: Close window
            step6_frame = customtkinter.CTkFrame(right_col, fg_color="transparent")
            step6_frame.pack(anchor="w", pady=0)
            
            customtkinter.CTkLabel(step6_frame, text="6.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step6_frame, text="Close the private window immediately — Save.", font=("Segoe UI", 12), text_color="gray").pack(side="left")

            # See Demo Button (YouTube setup demo video)
            demo_btn = customtkinter.CTkButton(
                help_frame,
                text="See demo",
                width=80,
                height=24,
                font=("Segoe UI", 11),
                fg_color=BUTTON_COLOR if 'BUTTON_COLOR' in globals() else ("#E0E0E0", "#303030"),
                hover_color="#1F6AA5",
                command=lambda: webbrowser.open("https://youtu.be/FHGLlox6Das")
            )
            # Use place for absolute positioning within the relative frame
            # x=-15, y=15 gives it some padding from the top-right corner
            demo_btn.place(relx=1.0, y=20, anchor="ne", x=-15)

            _add_clear_session_icon(help_frame, "YouTube")

        # Add help text for Deezer module
        if platform_name == "Deezer":
            # Helper function to copy value to clipboard with feedback (persistent)
            def _copy_deezer_value(value, button):
                try:
                    # Use persistent clipboard so it survives app close
                    if not _copy_to_system_clipboard(value):
                        # Fall back to Tkinter clipboard
                        app.clipboard_clear()
                        app.clipboard_append(value)
                        app.update()
                    # Show "Copied" feedback
                    original_text = button.cget("text")
                    button.configure(text="✓")
                    button.after(1500, lambda: button.configure(text=original_text))
                except Exception as e:
                    print(f"Error copying to clipboard: {e}")
            
            help_frame = customtkinter.CTkFrame(tab_frame, fg_color="#1D1E1E", corner_radius=5)
            deezer_help_row = 6 if platform_name == "Deezer" else len(default_platform_fields)
            if platform_name == "Deezer":
                help_frame.pack(fill="both", expand=True, padx=3, pady=(10, 5), anchor="nw")
                if hasattr(tab_frame, "deezer_chk_frame"):
                    tab_frame.deezer_chk_frame.pack(fill="x", anchor="w", padx=10, pady=(5, 5))
            else:
                help_frame.grid(row=deezer_help_row, column=0, columnspan=2, sticky="ew", padx=3, pady=(10, 5))
            help_frame.grid_columnconfigure(0, weight=1, uniform="help_cols")
            help_frame.grid_columnconfigure(1, weight=1, uniform="help_cols")
            deezer_use_arl = settings_vars.get("credentials", {}).get("Deezer", {}).get("use_arl")
            deezer_use_arl = deezer_use_arl.get() if hasattr(deezer_use_arl, "get") else False

            left_col = customtkinter.CTkFrame(help_frame, fg_color="transparent")
            left_col.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            
            left_header = customtkinter.CTkFrame(left_col, fg_color="transparent")
            left_header.pack(anchor="w", pady=(0, 15))
            icon_label = customtkinter.CTkLabel(left_header, text="💡", font=("Segoe UI", 20), text_color=WARNING_COLOR)
            icon_label.pack(side="left", padx=(5, 10))
            title_label = customtkinter.CTkLabel(left_header, text="How to set up", font=("Segoe UI", 16, "bold"), text_color="#DCE4EE")
            title_label.pack(side="left")
            # See demo: same position as Qobuz ID/Token (top-right of help_frame when ARL)
            deezer_see_demo_btn = customtkinter.CTkButton(
                help_frame,
                text="See demo",
                width=80,
                height=24,
                font=("Segoe UI", 11),
                fg_color=BUTTON_COLOR if 'BUTTON_COLOR' in globals() else ("#E0E0E0", "#303030"),
                hover_color="#1F6AA5",
                command=lambda: webbrowser.open("https://youtu.be/wmpF94D-S4U")
            )
            if not deezer_use_arl:
                deezer_see_demo_btn.place_forget()
            
            # Email/Password instructions
            left_col_email = customtkinter.CTkFrame(left_col, fg_color="transparent")
            left_col_email.pack(anchor="w", pady=0)
            step1_frame = customtkinter.CTkFrame(left_col_email, fg_color="transparent")
            step1_frame.pack(anchor="w", pady=0)
            customtkinter.CTkLabel(step1_frame, text="1.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            step1_text_frame = customtkinter.CTkFrame(step1_frame, fg_color="transparent")
            step1_text_frame.pack(side="left")
            customtkinter.CTkLabel(step1_text_frame, text="Fill in the email & password created, when signed up to " + (" " if platform.system() == "Darwin" else ""), font=("Segoe UI", 12), text_color="gray", justify="left", wraplength=HELP_CONTENT_WIDTH).pack(side="left")
            deezer_link = customtkinter.CTkLabel(step1_text_frame, text="Deezer", font=("Segoe UI", 12, "underline"), text_color=LINK_COLOR, cursor=HAND_CURSOR)
            deezer_link.pack(side="left", padx=(2, 0) if platform.system() == "Darwin" else (0, 0))
            deezer_link.bind("<Button-1>", lambda e: webbrowser.open("https://www.deezer.com"))
            deezer_link.bind("<Enter>", lambda e: deezer_link.configure(text_color=LINK_HOVER_COLOR))
            deezer_link.bind("<Leave>", lambda e: deezer_link.configure(text_color=LINK_COLOR))
            note_frame = customtkinter.CTkFrame(left_col_email, fg_color="transparent")
            note_frame.pack(anchor="w", pady=(0, 5))
            customtkinter.CTkLabel(note_frame, text="", width=35).pack(side="left")
            customtkinter.CTkLabel(note_frame, text="(active subscription required)", font=("Segoe UI", 12, "italic"), text_color="gray").pack(side="left")
            customtkinter.CTkLabel(note_frame, text=" — Save.", font=("Segoe UI", 12), text_color="gray").pack(side="left")

            # ARL instructions
            def _deezer_step(parent, num, text):
                f = customtkinter.CTkFrame(parent, fg_color="transparent")
                f.pack(anchor="w", pady=(0, 5))
                customtkinter.CTkLabel(f, text=f"{num}.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
                customtkinter.CTkLabel(f, text=text, font=("Segoe UI", 12), text_color="gray", justify="left", wraplength=HELP_CONTENT_WIDTH).pack(side="left")
                return f
            left_col_arl = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step1_arl = customtkinter.CTkFrame(left_col_arl, fg_color="transparent")
            step1_arl.pack(anchor="w", pady=(0, 5))
            customtkinter.CTkLabel(step1_arl, text="1.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step1_arl, text="Log in to ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            deezer_arl_link = customtkinter.CTkLabel(step1_arl, text="Deezer", font=("Segoe UI", 12, "underline"), text_color=LINK_COLOR, cursor=HAND_CURSOR)
            deezer_arl_link.pack(side="left")
            deezer_arl_link.bind("<Button-1>", lambda e: webbrowser.open("https://www.deezer.com"))
            deezer_arl_link.bind("<Enter>", lambda e: deezer_arl_link.configure(text_color=LINK_HOVER_COLOR))
            deezer_arl_link.bind("<Leave>", lambda e: deezer_arl_link.configure(text_color=LINK_COLOR))
            _deezer_step(left_col_arl, 2, "Hit F12 to open DevTools in your browser")
            _deezer_step(left_col_arl, 3, "Go to Storage/Application → Cookies → www.deezer.com")
            step4_arl = customtkinter.CTkFrame(left_col_arl, fg_color="transparent")
            step4_arl.pack(anchor="w", pady=(0, 5))
            customtkinter.CTkLabel(step4_arl, text="4.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step4_arl, text="Seek for ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            customtkinter.CTkLabel(step4_arl, text="arl", font=("Segoe UI", 12), text_color=LINK_COLOR).pack(side="left")
            customtkinter.CTkLabel(step4_arl, text=" → copy & paste above — Save.", font=("Segoe UI", 12), text_color="gray").pack(side="left")

            def _deezer_help_update(use_arl):
                if use_arl:
                    left_col_email.pack_forget()
                    left_col_arl.pack(anchor="w", pady=0)
                    deezer_see_demo_btn.place(relx=1.0, y=20, anchor="ne", x=-15)
                    deezer_see_demo_btn.lift()
                else:
                    left_col_arl.pack_forget()
                    left_col_email.pack(anchor="w", pady=0)
                    deezer_see_demo_btn.place_forget()
            tab_frame.deezer_help_update = _deezer_help_update
            if deezer_use_arl:
                left_col_email.pack_forget()
                left_col_arl.pack(anchor="w", pady=0)
                # Defer placement so help_frame has correct size (avoids See Demo button partly hidden on reopen)
                def _place_deezer_demo_btn():
                    deezer_see_demo_btn.place(relx=1.0, y=20, anchor="ne", x=-15)
                    deezer_see_demo_btn.lift()
                help_frame.after_idle(_place_deezer_demo_btn)
            else:
                left_col_arl.pack_forget()
                left_col_email.pack(anchor="w", pady=0)
                deezer_see_demo_btn.place_forget()

            # --- Right Column: Recommended Values ---
            right_col = customtkinter.CTkFrame(help_frame, fg_color="transparent")
            right_col.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            
            # Header
            right_header = customtkinter.CTkFrame(right_col, fg_color="transparent")
            right_header.pack(anchor="w", pady=(0, 15))
            
            key_icon = customtkinter.CTkLabel(
                right_header, 
                text="🔑", 
                font=("Segoe UI", 20), 
                text_color="gray"
            )
            key_icon.pack(side="left", padx=(0, 10))
            
            rec_title = customtkinter.CTkLabel(
                right_header, 
                text="Recommended Values", 
                font=("Segoe UI", 16, "bold"), 
                text_color="#DCE4EE"
            )
            rec_title.pack(side="left")
            
            # Values List
            def create_value_row(parent, label, value):
                row = customtkinter.CTkFrame(parent, fg_color="transparent")
                row.pack(anchor="w", pady=(0, 5))
                
                customtkinter.CTkLabel(row, text=f"{label}: ", font=("Segoe UI", 11), text_color="gray").pack(side="left")
                customtkinter.CTkLabel(row, text=value, font=("Segoe UI", 11), text_color=LINK_COLOR).pack(side="left", padx=(0, 5))
                
                copy_btn = customtkinter.CTkButton(
                    row, text="⧉", width=24, height=24, font=("Segoe UI", 14),
                    fg_color="#2B2B2B", hover_color="#3B3B3B", text_color="gray", corner_radius=3
                )
                copy_btn.configure(command=lambda b=copy_btn, v=value: _copy_deezer_value(v, b))
                
                copy_btn.pack(side="left")
                copy_btn.bind("<Enter>", lambda e: copy_btn.configure(text_color=WHITE_TEXT_COLOR))
                copy_btn.bind("<Leave>", lambda e: copy_btn.configure(text_color="gray"))
            
            create_value_row(right_col, "client_id", "447462")
            create_value_row(right_col, "client_secret", "a83bf7f38ad2f137e444727cfc3775cf")
            create_value_row(right_col, "bf_secret", "g4el58wc0zvf9na1")
            _add_clear_session_icon(help_frame, "Deezer")

        
        # Add help text for Qobuz module
        if platform_name == "Qobuz":
            # Helper function to copy value to clipboard with feedback (persistent)
            def _copy_qobuz_value(value, button):
                try:
                    # Use persistent clipboard so it survives app close
                    if not _copy_to_system_clipboard(value):
                        # Fall back to Tkinter clipboard
                        app.clipboard_clear()
                        app.clipboard_append(value)
                        app.update()
                    # Show "Copied" feedback
                    original_text = button.cget("text")
                    button.configure(text="✓")
                    button.after(1500, lambda: button.configure(text=original_text))
                except Exception as e:
                    print(f"Error copying to clipboard: {e}")
            
            help_frame = customtkinter.CTkFrame(tab_frame, fg_color="#1D1E1E", corner_radius=5)
            help_frame.pack(fill="both", expand=True, padx=3, pady=(10, 5), anchor="nw")
            help_frame.grid_columnconfigure(0, weight=1, uniform="help_cols")
            help_frame.grid_columnconfigure(1, weight=1, uniform="help_cols")
            if hasattr(tab_frame, "qobuz_chk_frame"):
                tab_frame.qobuz_chk_frame.pack(fill="x", anchor="w", padx=10, pady=(5, 5))

            qobuz_use_id = settings_vars.get("credentials", {}).get("Qobuz", {}).get("use_id_token")
            qobuz_use_id = qobuz_use_id.get() if hasattr(qobuz_use_id, "get") else False

            # --- Left Column: "How to set up" header + instructions ---
            left_col = customtkinter.CTkFrame(help_frame, fg_color="transparent")
            left_col.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            left_header = customtkinter.CTkFrame(left_col, fg_color="transparent")
            left_header.pack(anchor="w", pady=(0, 15))
            icon_label = customtkinter.CTkLabel(left_header, text="💡", font=("Segoe UI", 20), text_color=WARNING_COLOR)
            icon_label.pack(side="left", padx=(5, 10))
            title_label = customtkinter.CTkLabel(left_header, text="How to set up", font=("Segoe UI", 16, "bold"), text_color="#DCE4EE")
            title_label.pack(side="left")
            # See demo: same size/position as Spotify/YouTube (place on help_frame top-right when ID/Token)
            qobuz_see_demo_btn = customtkinter.CTkButton(
                help_frame,
                text="See demo",
                width=80,
                height=24,
                font=("Segoe UI", 11),
                fg_color=BUTTON_COLOR if 'BUTTON_COLOR' in globals() else ("#E0E0E0", "#303030"),
                hover_color="#1F6AA5",
                command=lambda: webbrowser.open("https://youtu.be/O9HX6_UkWvo")
            )
            if not qobuz_use_id:
                qobuz_see_demo_btn.place_forget()

            # --- Email/Password instructions ---
            left_col_email = customtkinter.CTkFrame(left_col, fg_color="transparent")
            left_col_email.pack(anchor="w", pady=0)
            step1_frame = customtkinter.CTkFrame(left_col_email, fg_color="transparent")
            step1_frame.pack(anchor="w", pady=0)
            customtkinter.CTkLabel(step1_frame, text="1.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            step1_text_frame = customtkinter.CTkFrame(step1_frame, fg_color="transparent")
            step1_text_frame.pack(side="left")
            customtkinter.CTkLabel(step1_text_frame, text="Fill in the email & password created, when signed up to " + (" " if platform.system() == "Darwin" else ""), font=("Segoe UI", 12), text_color="gray", justify="left", wraplength=HELP_CONTENT_WIDTH).pack(side="left")
            qobuz_link = customtkinter.CTkLabel(step1_text_frame, text="Qobuz", font=("Segoe UI", 12, "underline"), text_color=LINK_COLOR, cursor=HAND_CURSOR)
            qobuz_link.pack(side="left", padx=(2, 0) if platform.system() == "Darwin" else (0, 0))
            qobuz_link.bind("<Button-1>", lambda e: webbrowser.open("https://www.qobuz.com"))
            qobuz_link.bind("<Enter>", lambda e: qobuz_link.configure(text_color=LINK_HOVER_COLOR))
            qobuz_link.bind("<Leave>", lambda e: qobuz_link.configure(text_color=LINK_COLOR))
            note_frame = customtkinter.CTkFrame(left_col_email, fg_color="transparent")
            note_frame.pack(anchor="w", pady=(0, 5))
            customtkinter.CTkLabel(note_frame, text="", width=35).pack(side="left")
            customtkinter.CTkLabel(note_frame, text="(active subscription required)", font=("Segoe UI", 12, "italic"), text_color="gray").pack(side="left")
            customtkinter.CTkLabel(note_frame, text=" — Save.", font=("Segoe UI", 12), text_color="gray").pack(side="left")

            # --- ID/Token instructions: left = steps 1–3, right = steps 4–5 (no Recommended Values header) ---
            left_col_idtoken = customtkinter.CTkFrame(left_col, fg_color="transparent")
            def _qobuz_step(parent, num, text):
                f = customtkinter.CTkFrame(parent, fg_color="transparent")
                f.pack(anchor="w", pady=(0, 5))
                customtkinter.CTkLabel(f, text=f"{num}.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
                customtkinter.CTkLabel(f, text=text, font=("Segoe UI", 12), text_color="gray", justify="left", wraplength=HELP_CONTENT_WIDTH).pack(side="left")
                return f
            step1_id_frame = customtkinter.CTkFrame(left_col_idtoken, fg_color="transparent")
            step1_id_frame.pack(anchor="w", pady=(0, 5))
            customtkinter.CTkLabel(step1_id_frame, text="1.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step1_id_frame, text="Log in to Qobuz (", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            qobuz_play_link = customtkinter.CTkLabel(step1_id_frame, text="https://play.qobuz.com", font=("Segoe UI", 12, "underline"), text_color=LINK_COLOR, cursor=HAND_CURSOR)
            qobuz_play_link.pack(side="left")
            qobuz_play_link.bind("<Button-1>", lambda e: webbrowser.open("https://play.qobuz.com"))
            qobuz_play_link.bind("<Enter>", lambda e: qobuz_play_link.configure(text_color=LINK_HOVER_COLOR))
            qobuz_play_link.bind("<Leave>", lambda e: qobuz_play_link.configure(text_color=LINK_COLOR))
            customtkinter.CTkLabel(step1_id_frame, text=")", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            _qobuz_step(left_col_idtoken, 2, "Hit F12 to open DevTools in your browser")
            # Step 3: one-liner (no wrap)
            step3_id_frame = customtkinter.CTkFrame(left_col_idtoken, fg_color="transparent")
            step3_id_frame.pack(anchor="w", pady=(0, 5))
            customtkinter.CTkLabel(step3_id_frame, text="3.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step3_id_frame, text="Go to Storage/Application → Local storage → play.qobuz.com", font=("Segoe UI", 12), text_color="gray", justify="left", wraplength=HELP_CONTENT_WIDTH).pack(side="left")

            # --- Right Column: "Recommended Values" header (same height as "How to set up") + app_id / app_secret ---
            right_col = customtkinter.CTkFrame(help_frame, fg_color="transparent")
            right_col.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            right_header = customtkinter.CTkFrame(right_col, fg_color="transparent")
            right_header.pack(anchor="w", pady=(0, 15))
            key_icon = customtkinter.CTkLabel(right_header, text="🔑", font=("Segoe UI", 20), text_color="gray")
            key_icon.pack(side="left", padx=(0, 10))
            rec_title = customtkinter.CTkLabel(right_header, text="Recommended Values", font=("Segoe UI", 16, "bold"), text_color="#DCE4EE")
            rec_title.pack(side="left")
            
            def create_value_row(parent, label, value):
                row = customtkinter.CTkFrame(parent, fg_color="transparent")
                row.pack(anchor="w", pady=(0, 5))
                
                customtkinter.CTkLabel(row, text=f"{label}: ", font=("Segoe UI", 11), text_color="gray").pack(side="left")
                customtkinter.CTkLabel(row, text=value, font=("Segoe UI", 11), text_color=LINK_COLOR).pack(side="left", padx=(0, 5))
                
                copy_btn = customtkinter.CTkButton(
                    row, text="⧉", width=24, height=24, font=("Segoe UI", 14),
                    fg_color="#2B2B2B", hover_color="#3B3B3B", text_color="gray", corner_radius=3
                )
                copy_btn.configure(command=lambda b=copy_btn, v=value: _copy_qobuz_value(v, b))
                
                copy_btn.pack(side="left")
                copy_btn.bind("<Enter>", lambda e: copy_btn.configure(text_color=WHITE_TEXT_COLOR))
                copy_btn.bind("<Leave>", lambda e: copy_btn.configure(text_color="gray"))
            
            create_value_row(right_col, "app_id", "798273057")
            create_value_row(right_col, "app_secret", "abb21364945c0583309667d13ca3d93a")

            # Right column for ID/Token: steps 4 and 5, same left alignment as app_id; style "local user", "ID", "Token" like SoundCloud oauth_token
            right_col_idtoken = customtkinter.CTkFrame(help_frame, fg_color="transparent")
            _qobuz_spacer = customtkinter.CTkLabel(right_col_idtoken, text="", height=0)
            _qobuz_spacer.pack(anchor="w", pady=(28, 0))
            step4_right = customtkinter.CTkFrame(right_col_idtoken, fg_color="transparent")
            step4_right.pack(anchor="w", pady=(0, 5))
            customtkinter.CTkLabel(step4_right, text="4.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step4_right, text="Seek for ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            customtkinter.CTkLabel(step4_right, text="local user", font=("Segoe UI", 12), text_color=LINK_COLOR).pack(side="left")
            step5_right = customtkinter.CTkFrame(right_col_idtoken, fg_color="transparent")
            step5_right.pack(anchor="w", pady=(0, 5))
            customtkinter.CTkLabel(step5_right, text="5.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step5_right, text="Copy ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            customtkinter.CTkLabel(step5_right, text="ID", font=("Segoe UI", 12), text_color=LINK_COLOR).pack(side="left")
            customtkinter.CTkLabel(step5_right, text=" + ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            customtkinter.CTkLabel(step5_right, text="Token", font=("Segoe UI", 12), text_color=LINK_COLOR).pack(side="left")
            customtkinter.CTkLabel(step5_right, text=" & paste above — Save.", font=("Segoe UI", 12), text_color="gray").pack(side="left")

            def _qobuz_help_update(use_id):
                if use_id:
                    left_col_email.pack_forget()
                    left_col_idtoken.pack(anchor="w", pady=0)
                    right_col.grid_remove()
                    right_col_idtoken.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
                    # Same position as YouTube: top-right of help_frame, then lift so it's not covered
                    qobuz_see_demo_btn.place(relx=1.0, y=20, anchor="ne", x=-15)
                    qobuz_see_demo_btn.lift()
                else:
                    left_col_idtoken.pack_forget()
                    left_col_email.pack(anchor="w", pady=0)
                    right_col_idtoken.grid_remove()
                    right_col.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
                    qobuz_see_demo_btn.place_forget()
            tab_frame.qobuz_help_update = _qobuz_help_update
            if qobuz_use_id:
                left_col_email.pack_forget()
                left_col_idtoken.pack(anchor="w", pady=0)
                right_col.grid_remove()
                right_col_idtoken.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
                qobuz_see_demo_btn.place(relx=1.0, y=20, anchor="ne", x=-15)
                qobuz_see_demo_btn.lift()
            else:
                left_col_idtoken.pack_forget()
                left_col_email.pack(anchor="w", pady=0)
                right_col_idtoken.grid_remove()
                right_col.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
                qobuz_see_demo_btn.place_forget()
            _add_clear_session_icon(help_frame, "Qobuz")

        
        # Add help text for SoundCloud module
        if platform_name == "SoundCloud":
            help_frame = customtkinter.CTkFrame(tab_frame, fg_color="#1D1E1E", corner_radius=5)
            help_frame.pack(fill="both", expand=True, padx=3, pady=(10, 5), anchor="nw")
            help_frame.grid_columnconfigure(0, weight=1)
            
            # --- Single Column: How to set up ---
            left_col = customtkinter.CTkFrame(help_frame, fg_color="transparent")
            left_col.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            
            # Header
            left_header = customtkinter.CTkFrame(left_col, fg_color="transparent")
            left_header.pack(anchor="w", pady=(0, 15))
            
            icon_label = customtkinter.CTkLabel(
                left_header, 
                text="💡", 
                font=("Segoe UI", 20), 
                text_color=WARNING_COLOR
            )
            icon_label.pack(side="left", padx=(5, 10))
            
            title_label = customtkinter.CTkLabel(
                left_header, 
                text="How to set up", 
                font=("Segoe UI", 16, "bold"), 
                text_color="#DCE4EE"
            )
            title_label.pack(side="left")
            
            # Instructions
            # Step 1
            step1_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step1_frame.pack(anchor="w", pady=(0, 5))
            
            customtkinter.CTkLabel(step1_frame, text="1.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            
            step1_text_frame = customtkinter.CTkFrame(step1_frame, fg_color="transparent")
            step1_text_frame.pack(side="left")
            
            customtkinter.CTkLabel(step1_text_frame, text="Log in to ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            soundcloud_link = customtkinter.CTkLabel(step1_text_frame, text="SoundCloud", font=("Segoe UI", 12, "underline"), text_color=LINK_COLOR, cursor=HAND_CURSOR)
            soundcloud_link.pack(side="left")
            soundcloud_link.bind("<Button-1>", lambda e: webbrowser.open("https://soundcloud.com"))
            soundcloud_link.bind("<Enter>", lambda e: soundcloud_link.configure(text_color=LINK_HOVER_COLOR))
            soundcloud_link.bind("<Leave>", lambda e: soundcloud_link.configure(text_color=LINK_COLOR))
            
            customtkinter.CTkLabel(step1_text_frame, text=" ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            customtkinter.CTkLabel(step1_text_frame, text="(active SoundCloud Go+ subscription required)", font=("Segoe UI", 12, "italic"), text_color="gray").pack(side="left")
            
            # Step 2
            step2_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step2_frame.pack(anchor="w", pady=(0, 5))
            
            customtkinter.CTkLabel(step2_frame, text="2.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step2_frame, text="Hit F12 to open DevTools in your browser", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            # Step 3
            step3_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step3_frame.pack(anchor="w", pady=(0, 5))
            
            customtkinter.CTkLabel(step3_frame, text="3.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step3_frame, text="Go to Storage/Application → Cookies → https://soundcloud.com", font=("Segoe UI", 12), text_color="gray").pack(side="left")

            # Step 4
            step4_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step4_frame.pack(anchor="w", pady=(0, 5))
            
            customtkinter.CTkLabel(step4_frame, text="4.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            
            step4_text_frame = customtkinter.CTkFrame(step4_frame, fg_color="transparent")
            step4_text_frame.pack(side="left")
            
            customtkinter.CTkLabel(step4_text_frame, text="Seek for ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            customtkinter.CTkLabel(step4_text_frame, text="oauth_token", font=("Segoe UI", 12), text_color=LINK_COLOR).pack(side="left")
            customtkinter.CTkLabel(step4_text_frame, text=" which looks like: ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            customtkinter.CTkLabel(step4_text_frame, text="2-000000-0000000000-xxxxxxxxxxxxx", font=("Segoe UI", 11), text_color=LINK_COLOR).pack(side="left")
            
            # Step 5
            step5_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step5_frame.pack(anchor="w", pady=(0, 5))
            
            customtkinter.CTkLabel(step5_frame, text="5.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step5_frame, text="Copy & paste above — Save.", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            _add_clear_session_icon(help_frame, "SoundCloud")
        
        # Add help text for Tidal module
        if platform_name == "Tidal":
            # Helper function to copy value to clipboard with feedback (persistent)
            def _copy_tidal_value(value, button):
                try:
                    # Use persistent clipboard so it survives app close
                    if not _copy_to_system_clipboard(value):
                        # Fall back to Tkinter clipboard
                        app.clipboard_clear()
                        app.clipboard_append(value)
                        app.update()
                    # Show "Copied" feedback
                    original_text = button.cget("text")
                    button.configure(text="✓")
                    button.after(1500, lambda: button.configure(text=original_text))
                except Exception as e:
                    print(f"Error copying to clipboard: {e}")
            
            help_frame = customtkinter.CTkFrame(tab_frame, fg_color="#1D1E1E", corner_radius=5)
            help_frame.pack(fill="both", expand=True, padx=3, pady=(10, 5), anchor="nw")
            help_frame.grid_columnconfigure(0, weight=1)
            help_frame.grid_columnconfigure(1, weight=1)
            
            # --- Left Column: How to set up ---
            left_col = customtkinter.CTkFrame(help_frame, fg_color="transparent")
            left_col.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            
            # Header
            left_header = customtkinter.CTkFrame(left_col, fg_color="transparent")
            left_header.pack(anchor="w", pady=(0, 15))
            
            icon_label = customtkinter.CTkLabel(
                left_header, 
                text="💡", 
                font=("Segoe UI", 20), 
                text_color="#F2C94C"
            )
            icon_label.pack(side="left", padx=(5, 10))
            
            title_label = customtkinter.CTkLabel(
                left_header, 
                text="How to set up", 
                font=("Segoe UI", 16, "bold"), 
                text_color="#DCE4EE"
            )
            title_label.pack(side="left")
            
            # Instructions
            # Step 1
            step1_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step1_frame.pack(anchor="w", pady=(0, 5))
            
            customtkinter.CTkLabel(step1_frame, text="1.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step1_frame, text="Just enter url to download or use search function", font=("Segoe UI", 12), text_color="gray", justify="left", wraplength=HELP_CONTENT_WIDTH).pack(side="left")
            
            # Step 2
            step2_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step2_frame.pack(anchor="w", pady=(0, 5))
            
            customtkinter.CTkLabel(step2_frame, text="2.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            
            step2_text_frame = customtkinter.CTkFrame(step2_frame, fg_color="transparent")
            step2_text_frame.pack(side="left")
            
            customtkinter.CTkLabel(step2_text_frame, text="In the browser window that opens, fill in the email & password", font=("Segoe UI", 12), text_color="gray", justify="left", wraplength=HELP_CONTENT_WIDTH).pack(anchor="w")
            
            step2_line2 = customtkinter.CTkFrame(step2_text_frame, fg_color="transparent")
            step2_line2.pack(anchor="w")
            customtkinter.CTkLabel(step2_line2, text="created, when signed up to ", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            
            tidal_link = customtkinter.CTkLabel(step2_line2, text="Tidal", font=("Segoe UI", 12, "underline"), text_color="#1F6AA5", cursor=HAND_CURSOR)
            tidal_link.pack(side="left")
            tidal_link.bind("<Button-1>", lambda e: webbrowser.open("https://tidal.com"))
            tidal_link.bind("<Enter>", lambda e: tidal_link.configure(text_color="#4A9EFF"))
            tidal_link.bind("<Leave>", lambda e: tidal_link.configure(text_color="#1F6AA5"))
            
            # Step 3
            step3_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step3_frame.pack(anchor="w", pady=(0, 5))
            
            customtkinter.CTkLabel(step3_frame, text="3.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            customtkinter.CTkLabel(step3_frame, text="Hit continue to link your device & close the browser", font=("Segoe UI", 12), text_color="gray", justify="left", wraplength=HELP_CONTENT_WIDTH).pack(side="left")
            
            
            # --- Right Column: Recommended Values ---
            right_col = customtkinter.CTkFrame(help_frame, fg_color="transparent")
            right_col.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            
            # Header
            right_header = customtkinter.CTkFrame(right_col, fg_color="transparent")
            right_header.pack(anchor="w", pady=(0, 15))
            
            key_icon = customtkinter.CTkLabel(
                right_header, 
                text="🔑", 
                font=("Segoe UI", 20), 
                text_color="gray"
            )
            key_icon.pack(side="left", padx=(0, 10))
            
            rec_title = customtkinter.CTkLabel(
                right_header, 
                text="Recommended Values", 
                font=("Segoe UI", 16, "bold"), 
                text_color="#DCE4EE"
            )
            rec_title.pack(side="left")
            
            # Values List
            def create_value_row(parent, label, value):
                row = customtkinter.CTkFrame(parent, fg_color="transparent")
                row.pack(anchor="w", pady=(0, 5))
                
                customtkinter.CTkLabel(row, text=f"{label}: ", font=("Segoe UI", 11), text_color="gray").pack(side="left")
                customtkinter.CTkLabel(row, text=value, font=("Segoe UI", 11), text_color="#1F6AA5").pack(side="left", padx=(0, 5))
                
                copy_btn = customtkinter.CTkButton(
                    row, text="⧉", width=24, height=24, font=("Segoe UI", 14),
                    fg_color="#2B2B2B", hover_color="#3B3B3B", text_color="gray", corner_radius=3
                )
                copy_btn.configure(command=lambda b=copy_btn, v=value: _copy_tidal_value(v, b))
                
                copy_btn.pack(side="left")
                copy_btn.bind("<Enter>", lambda e: copy_btn.configure(text_color="#FFFFFF"))
                copy_btn.bind("<Leave>", lambda e: copy_btn.configure(text_color="gray"))
            
            create_value_row(right_col, "tv_atmos_token", "4N3n6Q1x95LL5K7p")
            create_value_row(right_col, "tv_atmos_secret", "oKOXfJW371cX6xaZ0PyhgGNBdNLlBZd4AKKYougMjik=")
            create_value_row(right_col, "mobile_atmos_hires_token", "km8T1xS355y7dd3H")
            create_value_row(right_col, "mobile_hires_token", "6BDSRdpK9hqEBTgU")
            _add_clear_session_icon(help_frame, "Tidal")

        # Add help text for Beatport module
        if platform_name == "Beatport":
            help_frame = customtkinter.CTkFrame(tab_frame, fg_color="#1D1E1E", corner_radius=5)
            help_frame.pack(fill="both", expand=True, padx=3, pady=(10, 5), anchor="nw")
            help_frame.grid_columnconfigure(0, weight=1)
            
            # --- Single Column: How to set up ---
            left_col = customtkinter.CTkFrame(help_frame, fg_color="transparent")
            left_col.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            
            # Header
            left_header = customtkinter.CTkFrame(left_col, fg_color="transparent")
            left_header.pack(anchor="w", pady=(0, 15))
            
            icon_label = customtkinter.CTkLabel(
                left_header, 
                text="💡", 
                font=("Segoe UI", 20), 
                text_color="#F2C94C"
            )
            icon_label.pack(side="left", padx=(5, 10))
            
            title_label = customtkinter.CTkLabel(
                left_header, 
                text="How to set up", 
                font=("Segoe UI", 16, "bold"), 
                text_color="#DCE4EE"
            )
            title_label.pack(side="left")
            
            # Instructions
            # Step 1
            step1_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step1_frame.pack(anchor="w", pady=0)
            
            customtkinter.CTkLabel(step1_frame, text="1.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            
            step1_text_frame = customtkinter.CTkFrame(step1_frame, fg_color="transparent")
            step1_text_frame.pack(side="left")
            
            customtkinter.CTkLabel(step1_text_frame, text="Fill in the username & password created, when signed up to " + (" " if platform.system() == "Darwin" else ""), font=("Segoe UI", 12), text_color="gray", justify="left", wraplength=HELP_CONTENT_WIDTH).pack(side="left")
            
            beatport_link = customtkinter.CTkLabel(step1_text_frame, text="Beatport", font=("Segoe UI", 12, "underline"), text_color="#1F6AA5", cursor=HAND_CURSOR)
            beatport_link.pack(side="left", padx=(2, 0) if platform.system() == "Darwin" else (0, 0))
            beatport_link.bind("<Button-1>", lambda e: webbrowser.open("https://www.beatport.com"))
            beatport_link.bind("<Enter>", lambda e: beatport_link.configure(text_color="#4A9EFF"))
            beatport_link.bind("<Leave>", lambda e: beatport_link.configure(text_color="#1F6AA5"))
            
            # Note
            note_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            note_frame.pack(anchor="w", pady=(0, 5))
            customtkinter.CTkLabel(note_frame, text="", width=35).pack(side="left") # Indent
            customtkinter.CTkLabel(note_frame, text="(active Beatport Professional subscription required)", font=("Segoe UI", 12, "italic"), text_color="gray").pack(side="left")
            customtkinter.CTkLabel(note_frame, text=" — Save.", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            _add_clear_session_icon(help_frame, "Beatport")

        # Add help text for Beatsource module
        if platform_name == "Beatsource":
            help_frame = customtkinter.CTkFrame(tab_frame, fg_color="#1D1E1E", corner_radius=5)
            help_frame.pack(fill="both", expand=True, padx=3, pady=(10, 5), anchor="nw")
            help_frame.grid_columnconfigure(0, weight=1)
            
            # --- Single Column: How to set up ---
            left_col = customtkinter.CTkFrame(help_frame, fg_color="transparent")
            left_col.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            
            # Header
            left_header = customtkinter.CTkFrame(left_col, fg_color="transparent")
            left_header.pack(anchor="w", pady=(0, 15))
            
            icon_label = customtkinter.CTkLabel(
                left_header, 
                text="💡", 
                font=("Segoe UI", 20), 
                text_color="#F2C94C"
            )
            icon_label.pack(side="left", padx=(5, 10))
            
            title_label = customtkinter.CTkLabel(
                left_header, 
                text="How to set up", 
                font=("Segoe UI", 16, "bold"), 
                text_color="#DCE4EE"
            )
            title_label.pack(side="left")
            
            # Instructions
            # Step 1
            step1_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            step1_frame.pack(anchor="w", pady=0)
            
            customtkinter.CTkLabel(step1_frame, text="1.", font=("Segoe UI", 12, "bold"), text_color="#DCE4EE", width=35).pack(side="left", anchor="n")
            
            step1_text_frame = customtkinter.CTkFrame(step1_frame, fg_color="transparent")
            step1_text_frame.pack(side="left")
            
            customtkinter.CTkLabel(step1_text_frame, text="Fill in the username & password created, when signed up to " + (" " if platform.system() == "Darwin" else ""), font=("Segoe UI", 12), text_color="gray", justify="left", wraplength=HELP_CONTENT_WIDTH).pack(side="left")
            
            beatsource_link = customtkinter.CTkLabel(step1_text_frame, text="Beatsource", font=("Segoe UI", 12, "underline"), text_color="#1F6AA5", cursor=HAND_CURSOR)
            beatsource_link.pack(side="left", padx=(2, 0) if platform.system() == "Darwin" else (0, 0))
            beatsource_link.bind("<Button-1>", lambda e: webbrowser.open("https://www.beatsource.com"))
            beatsource_link.bind("<Enter>", lambda e: beatsource_link.configure(text_color="#4A9EFF"))
            beatsource_link.bind("<Leave>", lambda e: beatsource_link.configure(text_color="#1F6AA5"))
            
            # Note
            note_frame = customtkinter.CTkFrame(left_col, fg_color="transparent")
            note_frame.pack(anchor="w", pady=(0, 5))
            customtkinter.CTkLabel(note_frame, text="", width=35).pack(side="left") # Indent
            customtkinter.CTkLabel(note_frame, text="(active Beatsource Pro subscription required)", font=("Segoe UI", 12, "italic"), text_color="gray").pack(side="left")
            customtkinter.CTkLabel(note_frame, text=" — Save.", font=("Segoe UI", 12), text_color="gray").pack(side="left")
            _add_clear_session_icon(help_frame, "Beatsource")

        # --- "See demo" button for ALL platforms ---
        # Positioned in the top-right corner of the help section.
        
        # Ensure help_frame exists (create it if it doesn't, e.g. for Beatport/Beatsource)
        if 'help_frame' not in locals():
             help_frame = customtkinter.CTkFrame(tab_frame, fg_color="#1D1E1E", corner_radius=5)
             help_frame.grid(row=len(default_platform_fields), column=0, columnspan=2, sticky="ew", padx=3, pady=(20, 10))
             help_frame.grid_columnconfigure(0, weight=1)
             
             # If we just created it, it's empty. We might want to add a minimal title or just leave it for the button.
             # The button is absolute positioned, so it won't affect grid layout inside.
             # To ensure the frame has height if empty, we might need a dummy label or minsize.
             # However, if it's empty, a height=0 frame might not show.
             # Let's add a generic title if it's a new frame to give it context.
             if platform_name not in ["Spotify", "AppleMusic", "YouTube", "Deezer", "Qobuz", "SoundCloud", "Tidal", "Beatport", "Beatsource"]:
                 help_container = customtkinter.CTkFrame(help_frame, fg_color="transparent")
                 help_container.pack(anchor="w", padx=15, pady=12)
                 
                 title_text = f"{platform_name} Help:"
                 if platform_name in ["Beatport", "Beatsource"]:
                     title_text = "How to set up:"
                 
                 help_title = customtkinter.CTkLabel(
                    help_container, 
                    text=title_text,
                    font=("Segoe UI", 11),
                    text_color="gray"
                 )
                 help_title.grid(row=0, column=0, sticky="ne", padx=(0, 20), pady=0)

        # Add the "See demo" button to the top-right of the help_frame
        # Each platform has its own demo video URL (platforms with their own See demo in-help are excluded here)
        SEE_DEMO_URLS = {
            "AppleMusic": "https://youtu.be/HbV4Fx2Is2I",
            "SoundCloud": "https://youtu.be/9YFPsEWk6ZY",
            "Spotify": "https://youtu.be/7A3cZ5ELtZY",
        }
        if platform_name in SEE_DEMO_URLS:
            demo_url = SEE_DEMO_URLS[platform_name]
            demo_btn = customtkinter.CTkButton(
                help_frame,
                text="See demo",
                width=80,
                height=24,
                font=("Segoe UI", 11),
                fg_color=BUTTON_COLOR if 'BUTTON_COLOR' in globals() else ("#E0E0E0", "#303030"),
                hover_color="#1F6AA5",
                command=lambda u=demo_url: webbrowser.open(u)
            )
            # Use place for absolute positioning within the relative frame
            # x=-15, y=15 gives it some padding from the top-right corner
            demo_btn.place(relx=1.0, y=20, anchor="ne", x=-15)

    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.__stderr__)

def _handle_settings_tab_change():
    global loaded_credential_tabs, settings_tabview, credential_tabs_config, settings_bottom_frame
    selected_tab_name = settings_tabview.get()
    
    if selected_tab_name not in loaded_credential_tabs:
        for tab_name, tab_info in credential_tabs_config.items():
            if tab_name == selected_tab_name:
                _create_credential_tab_content(tab_name, tab_info['frame'])
                loaded_credential_tabs.add(tab_name)
                break

    # When switching to Deezer, re-apply help layout so See Demo button is placed correctly (fixes partly hidden button on reopen)
    if selected_tab_name == "Deezer":
        tab_frame = credential_tabs_config.get(selected_tab_name, {}).get("frame")
        if tab_frame and hasattr(tab_frame, "deezer_help_update"):
            deezer_use_arl_var = settings_vars.get("credentials", {}).get("Deezer", {}).get("use_arl")
            if deezer_use_arl_var is not None and hasattr(deezer_use_arl_var, "get"):
                use_arl = deezer_use_arl_var.get()
                tab_frame.after_idle(lambda u=use_arl: tab_frame.deezer_help_update(u))

    # Deezer/Qobuz: minimal space; Global: less space above Save; other platform tabs: match Download tab (20px above)
    if 'settings_bottom_frame' in globals() and settings_bottom_frame and settings_bottom_frame.winfo_exists():
        parent = settings_bottom_frame.master  # settings_tab
        if selected_tab_name in ("Deezer", "Qobuz"):
            pady_top = (0, 5)
            parent.grid_rowconfigure(1, weight=0, minsize=35)  # tighter row so no visible gap above Save
        elif selected_tab_name == "Global":
            pady_top = (5, 5)
            parent.grid_rowconfigure(1, weight=0, minsize=40)
        else:
            pady_top = (9, 5)
            parent.grid_rowconfigure(1, weight=0, minsize=40)
        settings_bottom_frame.grid_configure(pady=pady_top)

def update_search_platform_dropdown():
    """Updates the platform dropdown in the Search tab based on current settings AND installed modules."""
    global platform_combo, platform_var, current_settings, DEFAULT_SETTINGS, installed_platform_keys
    if not all(var in globals() for var in ['platform_combo', 'platform_var', 'current_settings', 'DEFAULT_SETTINGS', 'installed_platform_keys']):
        if not getattr(sys, 'frozen', False):
            print("[Update Platforms] Critical variables not found. Skipping update.")
        return

    if not platform_combo or not platform_combo.winfo_exists():
        if not getattr(sys, 'frozen', False):
            print("[Update Platforms] Platform combo widget not available. Skipping update.")
        return

    try:
        if not getattr(sys, 'frozen', False) and current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
            print("[Update Platforms] Refreshing Search tab platform dropdown...")
        
        base_available_platforms = [pk for pk in installed_platform_keys if pk != "Musixmatch"]
        configured_platforms = []

        # Platforms where credentials are completely optional (work without any credentials)
        platforms_with_optional_credentials = ["YouTube", "AppleMusic", "Deezer", "Qobuz"]

        for platform_name_iter in base_available_platforms:
            # YouTube, Apple Music, Deezer (public API) always show - no credential check
            if platform_name_iter in platforms_with_optional_credentials:
                configured_platforms.append(platform_name_iter)
                continue
                
            default_platform_fields = DEFAULT_SETTINGS.get("credentials", {}).get(platform_name_iter, {})
            if not default_platform_fields:
                configured_platforms.append(platform_name_iter)
                continue

            current_platform_creds = current_settings.get("credentials", {}).get(platform_name_iter, {})
            # Qobuz: valid if (username and password) OR (user_id and auth_token)
            if platform_name_iter == "Qobuz":
                has_email_pass = bool(str(current_platform_creds.get("username", "") or "").strip() and str(current_platform_creds.get("password", "") or "").strip())
                has_id_token = bool(str(current_platform_creds.get("user_id", "") or "").strip() and str(current_platform_creds.get("auth_token", "") or "").strip())
                is_fully_filled = has_email_pass or has_id_token
            elif platform_name_iter == "Deezer":
                has_email_pass = bool(str(current_platform_creds.get("email", "") or "").strip() and str(current_platform_creds.get("password", "") or "").strip())
                has_arl = bool(str(current_platform_creds.get("arl", "") or "").strip())
                is_fully_filled = has_email_pass or has_arl
            else:
                is_fully_filled = True
                for field_key in default_platform_fields.keys():
                    field_value = current_platform_creds.get(field_key, "")
                    if isinstance(default_platform_fields[field_key], bool):
                        pass
                    elif not str(field_value).strip():
                        is_fully_filled = False
                        break

            # Tidal: always show in dropdown so user can select and log in; session check only
            # applies to "Search All" (get_searchable_platforms) so All doesn't hang on Tidal.

            if is_fully_filled:
                configured_platforms.append(platform_name_iter)
        
        platforms_to_show = ["All"] + sorted(configured_platforms)
        
        current_selection = platform_var.get()
        platform_combo.configure(values=platforms_to_show)

        if platforms_to_show:
            if current_selection in platforms_to_show:
                platform_var.set(current_selection)
            else:
                platform_var.set(platforms_to_show[0])
        else:
            platform_var.set("")
        
        on_platform_change()

        if not getattr(sys, 'frozen', False) and current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
            print(f"[Update Platforms] Dropdown updated with: {platforms_to_show}. Selected: {platform_var.get()}")

    except tkinter.TclError as e:
        if "invalid command name" in str(e):
            if not getattr(sys, 'frozen', False):
                print(f"[Update Platforms] TclError (widget likely destroyed): {e}")
        else:
            if not getattr(sys, 'frozen', False):
                print(f"[Update Platforms] TclError: {e}")
    except Exception as e:
        if not getattr(sys, 'frozen', False):
            print(f"[Update Platforms] Unexpected error: {e}")
        import traceback
        if not getattr(sys, 'frozen', False):
            traceback.print_exc()

def _on_hyperlink_click(event):
    global log_textbox
    if 'log_textbox' not in globals() or not log_textbox or not log_textbox.winfo_exists():
        return
    try:
        index = log_textbox.index(f"@{event.x},{event.y}")
        
        tag_ranges = log_textbox.tag_ranges("hyperlink")
        
        clicked_url = None
        for i in range(0, len(tag_ranges), 2):
            start = tag_ranges[i]
            end = tag_ranges[i+1]
            if log_textbox.compare(index, ">=", start) and log_textbox.compare(index, "<", end):
                clicked_url = log_textbox.get(start, end)
                break
        
        if clicked_url:            
            if clicked_url.endswith('.') or clicked_url.endswith(')'):
                 if not any(char.isalnum() for char in clicked_url[-3:]):
                    clicked_url = clicked_url[:-1]

            print(f"Opening URL: {clicked_url}")
            webbrowser.open_new_tab(clicked_url)
    except Exception as e:
        print(f"Error opening hyperlink: {e}")

def _on_gui_exit():
    """Handles cleanup when the GUI is closing."""
    global app, _mutex_handle
    print("[Exit] GUI closing. Cleaning up temp directory...")
    try:
        shutil.rmtree('temp', ignore_errors=True)
        print("[Exit] Temp directory removed.")
    except Exception as e:
        print(f"[Exit] Error removing temp directory: {e}")
    if platform.system() == "Windows" and _mutex_handle:
        try:
            from ctypes import windll, wintypes
            CloseHandle = windll.kernel32.CloseHandle
            CloseHandle.argtypes = [wintypes.HANDLE]
            CloseHandle.restype = wintypes.BOOL
            if CloseHandle(_mutex_handle):
                print("[Instance Check] Released mutex.")
            else:
                print("[Instance Check] Failed to release mutex.")
            _mutex_handle = None
        except Exception as e:
            print(f"[Instance Check] Error releasing mutex: {e}")

    if 'app' in globals() and app and app.winfo_exists():
        # On macOS, CustomTkinter CTkLabels fire _update_dimensions_event during destroy;
        # their canvases may already be gone, causing "invalid command name" TclError.
        # Suppress those callback exceptions during shutdown.
        if platform.system() == "Darwin":
            def _silence_shutdown_callbacks(exc_type, exc_val, exc_tb):
                if exc_type is tkinter.TclError and "invalid command name" in str(exc_val):
                    return  # expected during teardown
                # re-raise or use default handler for unexpected errors
                import traceback
                traceback.print_exception(exc_type, exc_val, exc_tb)
            app.report_callback_exception = _silence_shutdown_callbacks
        try:
            app.withdraw()  # hide first to reduce Configure events
            app.update_idletasks()
        except tkinter.TclError:
            pass
        try:
            app.destroy()
        except tkinter.TclError:
            pass
    print("[Exit] Application shutdown complete.")
    os._exit(0)

def _setup_macos_window_management():
    """Sets up macOS-specific window management to handle minimize behavior."""
    global app
    
    if platform.system() != "Darwin":
        return
    global _is_window_minimized, _restore_timer_id
    _is_window_minimized = False
    _restore_timer_id = None
    
    def restore_window():
        """Restore the window from minimized state."""
        global _is_window_minimized, _restore_timer_id
        try:
            if _is_window_minimized:
                _is_window_minimized = False
                if _restore_timer_id:
                    app.after_cancel(_restore_timer_id)
                    _restore_timer_id = None
                app.deiconify()
                app.lift()
                app.focus_force()
        except Exception as e:
            print(f"[macOS] Error restoring window: {e}")
    
    def on_window_unmap(event=None):
        """Handle window unmap events (minimize/hide)."""
        global _is_window_minimized, _restore_timer_id
        
        if event and event.widget != app:
            return
        
        try:
            current_state = app.state()
            if current_state == 'iconic' and not _is_window_minimized:
                _is_window_minimized = True
                app.after_idle(lambda: app.withdraw())
                def check_for_restore():
                    global _restore_timer_id
                    if _is_window_minimized:
                        _restore_timer_id = app.after(200, check_for_restore)
                
                check_for_restore()
                
        except Exception as e:
            print(f"[macOS] Error in window unmap handler: {e}")
    
    def on_window_map(event=None):
        """Handle window map events (restore/show)."""
        global _is_window_minimized, _restore_timer_id
        
        if event and event.widget != app:
            return
            
        if _is_window_minimized:
            _is_window_minimized = False
            if _restore_timer_id:
                app.after_cancel(_restore_timer_id)
                _restore_timer_id = None
    
    def on_focus_in(event=None):
        """Handle window focus events."""
        global _is_window_minimized
        if _is_window_minimized and event and event.widget == app:
            restore_window()
    
    try:
        app.bind('<Unmap>', on_window_unmap)
        app.bind('<Map>', on_window_map)
        app.bind('<FocusIn>', on_focus_in)
        try:
            app.createcommand('::tk::mac::ReopenApplication', restore_window)
        except Exception as menu_e:
            pass  # Normal on non-bundled apps
        
    except Exception as e:
        print(f"[macOS] Error setting up window management: {e}")

def validate_codec_conversions():
    """Validate codec conversions to prevent circular references and duplicates."""
    global settings_vars
    
    try:
        codec_vars = settings_vars.get("globals", {}).get("advanced.codec_conversions", {})
        if not isinstance(codec_vars, dict):
            return True
        conversions = {}
        sources_used = set()
        
        for key, var in codec_vars.items():
            if key.endswith("_source") and isinstance(var, tkinter.StringVar):
                source_codec = var.get().lower().strip()
                target_key = key.replace("_source", "_target")
                
                if target_key in codec_vars and isinstance(codec_vars[target_key], tkinter.StringVar):
                    target_codec = codec_vars[target_key].get().lower().strip()
                    if not source_codec or not target_codec:
                        continue
                    if source_codec in sources_used:
                        show_centered_messagebox("Codec Conversion Error", 
                                                f"Duplicate source format '{source_codec}' detected!\nEach source format can only have one conversion rule.", 
                                                "error")
                        return False
                    
                    sources_used.add(source_codec)
                    conversions[source_codec] = target_codec
        for source, target in conversions.items():
            if target in conversions and conversions[target] == source and source != target:
                show_centered_messagebox("Codec Conversion Error", 
                                        f"Circular conversion detected!\n'{source}' → '{target}' and '{target}' → '{source}'\n\nThis would create an infinite loop. Please remove one of these conversions.", 
                                        "error")
                return False
        
        return True
        
    except Exception as e:
        print(f"Error validating codec conversions: {e}")
        return True

def browse_ffmpeg_path(path_variable):
    filetypes = [("All files", "*.*")]
    if platform.system() == "Windows":
        filetypes.insert(0, ("Executable files", "*.exe"))

    # Determine initial directory - use app directory if ffmpeg_path is default "ffmpeg"
    current_path = path_variable.get() if path_variable.get() else ""
    if current_path and current_path.lower() != "ffmpeg" and os.path.exists(os.path.dirname(current_path)):
        initial_dir = os.path.dirname(current_path)
    else:
        # Open the app's installation directory where ffmpeg.exe should be
        initial_dir = get_script_directory()
        if not initial_dir or not os.path.isdir(initial_dir):
            initial_dir = os.path.expanduser("~")

    filepath = tkinter.filedialog.askopenfilename(
        initialdir=initial_dir,
        filetypes=filetypes,
        title="Select FFmpeg Executable"
    )
    if filepath:
        path_variable.set(filepath)

def run_download_in_subprocess(url, output_path, gui_settings, search_result_data, output_queue_mp):
    """Runs the download in a separate subprocess for complete GUI isolation."""
    import sys
    import os
    try:
        # Use data directory for CWD (handles macOS Application Support)
        data_dir = get_data_directory()
        script_dir = get_script_directory()
        
        if data_dir and os.path.isdir(data_dir):
            os.chdir(data_dir)
            # Add modules from data directory to sys.path
            modules_dir = os.path.join(data_dir, 'modules')
            if os.path.isdir(modules_dir) and modules_dir not in sys.path:
                sys.path.insert(0, modules_dir)
        elif script_dir and os.path.isdir(script_dir):
            os.chdir(script_dir)
            
        # Add script_dir to sys.path for imports
        if script_dir and script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        import orpheus.core
        from orpheus.core import Orpheus
        from orpheus.music_downloader import Downloader
        from utils.models import Oprinter
        orpheus_subprocess = Orpheus()
        class SubprocessQueueWriter:
            def __init__(self, queue_ref):
                self.queue = queue_ref
            
            def write(self, msg):
                try:
                    self.queue.put(msg, timeout=1)
                except:
                    pass
            
            def flush(self):
                pass
        queue_writer = SubprocessQueueWriter(output_queue_mp)
        sys.stdout = queue_writer
        fresh_subprocess_settings = orpheus_subprocess.settings
        run_download_in_thread(orpheus_subprocess, url, output_path, fresh_subprocess_settings, search_result_data)
        
    except Exception as e:
        try:
            output_queue_mp.put(f"Subprocess error: {e}\n", timeout=1)
        except:
            pass

def final_download_cleanup(success=False):
    """Handles UI cleanup when download process completes."""
    global download_process_active, file_download_queue, current_batch_output_path, app
    
    try:
        download_process_active = False
        set_ui_state_downloading(False)
        if file_download_queue:
            next_url = file_download_queue.pop(0)
            print(f"Queueing next download from file: {next_url} ({len(file_download_queue)} remaining)")
            if current_batch_output_path:
                # Determine pause duration based on platform
                pause_ms = 100  # Default 100ms
                try:
                    # Detect platform from URL
                    if 'youtube.com' in next_url or 'youtu.be' in next_url:
                        pause_seconds = current_settings.get('credentials', {}).get('YouTube', {}).get('download_pause_seconds', 0)
                    elif 'spotify.com' in next_url:
                        pause_seconds = current_settings.get('credentials', {}).get('Spotify', {}).get('download_pause_seconds', 30)
                    else:
                        pause_seconds = 0
                    
                    if pause_seconds and int(pause_seconds) > 0:
                        pause_ms = int(pause_seconds) * 1000
                        print(f"Pausing for {pause_seconds} seconds before next download...")
                except Exception as e:
                    print(f"[Warning] Could not read pause setting: {e}")
                
                app.after(pause_ms, lambda u=next_url, p=current_batch_output_path: _start_single_download(u, p, None))
            else:
                print("[Error] Batch path missing.")
                file_download_queue.clear()
        else:
            if current_batch_output_path:
                print("File download queue is empty. Batch finished.")
                current_batch_output_path = None
        
        print(f"Download process completed. Success: {success}")
        
    except Exception as e:
        print(f"Error in download cleanup: {e}")
        download_process_active = False
        set_ui_state_downloading(False)

def run_download_in_thread_responsive(orpheus, url, output_path, gui_settings, search_result_data=None):
    """Runs the download with aggressive yielding to keep GUI responsive."""
    global output_queue, stop_event, app, download_process_active, DEFAULT_SETTINGS, _queue_log_handler_instance
    import time
    
    if _queue_log_handler_instance:
        _queue_log_handler_instance.reset_ffmpeg_state_for_current_download()

    if orpheus is None:
        logging.error("Orpheus instance not available. Cannot start download.")
        try:
            if 'app' in globals() and app and app.winfo_exists():
                 app.after(0, lambda: set_ui_state_downloading(False))
        except NameError: pass
        except Exception as e: logging.error(f"Error scheduling UI reset after Orpheus instance error: {e}")
        return
    def yield_to_gui(duration=0.001):
        time.sleep(duration)
        if 'app' in globals() and app:
            try:
                app.update_idletasks()
            except:
                pass

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    dummy_stderr = DummyStderr()
    is_cancelled = False
    download_exception_occurred = False
    start_time = datetime.datetime.now()
    media_type = None
    yield_to_gui(0.01)

    try:
        queue_writer = QueueWriter(output_queue, media_type=media_type)
        sys.stdout = queue_writer
        sys.stderr = dummy_stderr
        yield_to_gui()
        fresh_orpheus_settings = orpheus.settings
        downloader_settings = {
            "general": {
                "download_path": fresh_orpheus_settings.get("globals", {}).get("general", {}).get("output_path", DEFAULT_SETTINGS["globals"]["general"]["output_path"]),
                "download_quality": fresh_orpheus_settings.get("globals", {}).get("general", {}).get("quality", DEFAULT_SETTINGS["globals"]["general"]["quality"]),
                "search_limit": fresh_orpheus_settings.get("globals", {}).get("general", {}).get("search_limit", DEFAULT_SETTINGS["globals"]["general"]["search_limit"]),
                "progress_bar": False
            },
            **{k: v for k, v in fresh_orpheus_settings.get("globals", {}).items() if k != "general"}
        }
        
        yield_to_gui()
        def yielding_download():
            return run_download_in_thread(orpheus, url, output_path, fresh_orpheus_settings, search_result_data)
        download_result = yielding_download()
        
    except Exception as e:
        print(f"Error in responsive download: {e}")
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        def final_cleanup():
            global download_process_active
            download_process_active = False
            set_ui_state_downloading(False)
        
        try:
            if 'app' in globals() and app and app.winfo_exists():
                app.after(0, final_cleanup)
        except:
            final_cleanup()

def _auto_save_credential_change(*args):
    """Callback to save settings when a credential value changes."""
    save_settings(show_confirmation=False)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    _mutex_handle = None
    if platform.system() == "Windows":
        try:
            from ctypes import windll, wintypes

            ERROR_ALREADY_EXISTS = 183
            mutex_name = "OrpheusDL_GUI_Instance_Mutex_8E1D3B4C_A5F8_4B9A_8D7C_6F0A1B3E4D5C"
            CreateMutexW = windll.kernel32.CreateMutexW
            CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
            CreateMutexW.restype = wintypes.HANDLE
            GetLastError = windll.kernel32.GetLastError
            GetLastError.restype = wintypes.DWORD
            _mutex_handle = CreateMutexW(None, True, mutex_name)

            last_error = GetLastError()

            if last_error == ERROR_ALREADY_EXISTS:
                print("[Instance Check] Mutex already exists. Another instance is running. Exiting.")
                sys.exit()
            elif _mutex_handle is None or _mutex_handle == 0:
                print(f"[Instance Check] Failed to create mutex. Error code: {last_error}")
                sys.exit("Error creating application mutex.")
            else:
                print("[Instance Check] Acquired mutex. This is the first instance.")

        except ImportError:
             print("[Instance Check] Warning: Could not import ctypes/windll. Single instance check skipped.")
        except Exception as e:
            print(f"[Instance Check] Error during single instance check: {e}")
            sys.exit("Failed single instance check.")
    if multiprocessing.parent_process() is None:
        print(f"[Main Process {os.getpid()}] Starting application...")
        _SCRIPT_DIR = get_script_directory()
        _DATA_DIR = get_data_directory()
        print(f"[Init] Script directory: {_SCRIPT_DIR}")
        print(f"[Init] Data directory: {_DATA_DIR}")
        try:
            # Ensure data directory exists
            if _DATA_DIR:
                os.makedirs(_DATA_DIR, exist_ok=True)
                print(f"[Init] Ensured data directory exists: {_DATA_DIR}")
            
            # Create temp directory
            temp_dir = os.path.join(_DATA_DIR if _DATA_DIR else os.getcwd(), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            print(f"[Init] Ensured temp directory exists: {temp_dir}")
            
            # Change to data directory for writable operations
            if _DATA_DIR:
                os.chdir(_DATA_DIR)
                print(f"[CWD] Changed working directory to: {_DATA_DIR}")
                print(f"[CWD] Verified CWD is now: {os.getcwd()}")
                
                # Copy bundled resources (modules, ffmpeg) to data directory
                copy_bundled_resources_to_data_dir(_DATA_DIR)
            else:
                print(f"[CWD] FATAL: _DATA_DIR could not be determined. Application will likely fail.")
                if 'show_centered_messagebox' in globals() and callable(show_centered_messagebox):
                    show_centered_messagebox("Critical Path Error", "Could not determine application data directory. Cannot continue.", dialog_type="error")
                else:
                    tkinter.messagebox.showerror("Critical Path Error", "Could not determine application data directory. Cannot continue.")
                sys.exit(1)
        except Exception as e_chdir:
            print(f"[CWD] Error during directory setup: {e_chdir}")
            import traceback
            traceback.print_exc()

        # Use _DATA_DIR for writable directories (config, modules)
        CONFIG_DIR = os.path.join(_DATA_DIR, 'config')
        MODULES_DIR = os.path.join(_DATA_DIR, 'modules')
        CONFIG_FILE_NAME = 'settings.json'
        CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, CONFIG_FILE_NAME)
        if os.path.isdir(MODULES_DIR):
            if MODULES_DIR not in sys.path:
                sys.path.insert(0, MODULES_DIR)
                print(f"[SysPath] Added external modules directory: {MODULES_DIR}")
            else:
                print(f"[SysPath] External modules directory already in sys.path: {MODULES_DIR}")
        else:
            print(f"[SysPath] External modules directory not found: {MODULES_DIR}")
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            os.makedirs(MODULES_DIR, exist_ok=True)
            print(f"[Init] Ensured config directory exists: {CONFIG_DIR}")
            print(f"[Init] Ensured modules directory exists: {MODULES_DIR}")
        except OSError as e:
            print(f"[Error] Could not create config/data/modules directories: {e}")
        DEFAULT_SETTINGS = {
            "globals": {
                "general": {
                    "output_path": os.path.join(_DATA_DIR if _DATA_DIR else _SCRIPT_DIR, "Downloads"),
                    "quality": "hifi",
                    "search_limit": 25,
                    "concurrent_downloads": 5,
                    "play_sound_on_finish": True
                },
                "artist_downloading": { "return_credited_albums": True, "separate_tracks_skip_downloaded": True },
                "formatting": { "album_format": "{artist}/{name}", "playlist_format": "{name}", "track_filename_format": "{artist} - {name}", "single_full_path_format": "{artist} - {name}", "enable_zfill": True, "force_album_format": False },
                "codecs": {
                    "proprietary_codecs": False,
                    "spatial_codecs": True
                },
                "module_defaults": { "lyrics": "default", "covers": "default", "credits": "default" },
                "lyrics": { "embed_lyrics": True, "embed_synced_lyrics": False, "save_synced_lyrics": True },
                "covers": { "embed_cover": True, "main_compression": "high", "main_resolution": 1400, "save_external": False, "external_format": "png", "external_compression": "low", "external_resolution": 3000, "save_animated_cover": True },
                "playlist": { "save_m3u": True, "paths_m3u": "absolute", "extended_m3u": True },
                "advanced": {
                    "advanced_login_system": False,
                    "codec_conversions": { "alac": "flac", "wav": "flac", "vorbis": "vorbis" }, 
                    "conversion_flags": {
                        "flac": { "compression_level": 5 },
                        "mp3": { "qscale:a": "0" },
                        "aac": { "audio_bitrate": "256k" }
                    },
                    "conversion_keep_original": False,
                    "ffmpeg_path": "ffmpeg",
                    "cover_variance_threshold": 8,
                    "debug_mode": False,
                    "disable_subscription_checks": False,
                    "enable_undesirable_conversions": False,
                    "ignore_existing_files": False,
                    "ignore_different_artists": True,
                    "hide_ffmpeg_warning": False
                }
            },
            "credentials": {
                "AppleMusic": { "cookies_path": "./config/cookies.txt", "language": "en-US", "codec": "aac", "quality": "high" },
                "Beatport": { "username": "", "password": "" },
                "Beatsource": { "username": "", "password": "" },
                "Bugs": { "username": "", "password": "" },
                "Deezer": { "client_id": "447462", "client_secret": "a83bf7f38ad2f137e444727cfc3775cf", "bf_secret": "g4el58wc0zvf9na1", "email": "", "password": "", "arl": "", "use_arl": "false" },
                "Idagio": { "username": "", "password": "" }, 
                "KKBOX": { "kc1_key": "", "secret_key": "", "email": "", "password": "" },
                "Musixmatch": { "token_limit": 10, "lyrics_format": "standard", "custom_time_decimals": False },
                "Napster": { "api_key": "", "customer_secret": "", "requested_netloc": "", "username": "", "password": "" },
                "Nugs": { "username": "", "password": "", "client_id": "", "dev_key": "" },
                "Qobuz": { "app_id": "798273057", "app_secret": "abb21364945c0583309667d13ca3d93a", "quality_format": "{sample_rate}kHz {bit_depth}bit", "username": "", "password": "", "user_id": "", "auth_token": "", "use_id_token": "false" },
                "SoundCloud": { "web_access_token": "" },
                "Spotify": { "username": "", "download_pause_seconds": 30, "client_id": "", "client_secret": "" },
                "Tidal": { "tv_atmos_token": "4N3n6Q1x95LL5K7p", "tv_atmos_secret": "oKOXfJW371cX6xaZ0PyhgGNBdNLlBZd4AKKYougMjik=", "mobile_atmos_hires_token": "km8T1xS355y7dd3H", "mobile_hires_token": "6BDSRdpK9hqEBTgU", "enable_mobile": True, "prefer_ac4": False, "fix_mqa": True },
                "YouTube": { "cookies_path": "./config/youtube-cookies.txt", "download_pause_seconds": 5, "download_mode": "sequential" }
            }
        }
        installed_platform_keys = []
        if os.path.isdir(MODULES_DIR):
            try:                
                module_subdirs_in_dir = [d.lower() for d in os.listdir(MODULES_DIR) if os.path.isdir(os.path.join(MODULES_DIR, d))]
                
                default_credential_platform_names = list(DEFAULT_SETTINGS.get("credentials", {}).keys())

                for platform_key in default_credential_platform_names:
                    expected_subdir_name = platform_key.lower()
                    
                    if expected_subdir_name in module_subdirs_in_dir:
                        installed_platform_keys.append(platform_key)
                
                installed_platform_keys = sorted(list(set(installed_platform_keys)))
                print(f"[Module Check] Detected installed platform keys based on './modules/' subfolders: {installed_platform_keys}")
            except Exception as e:
                print(f"[Module Check] Error scanning './modules/' subdirectories: {e}. Proceeding with empty list.")
                installed_platform_keys = []
        else:
            print(f"[Module Check] Modules directory '{MODULES_DIR}' not found. No external modules will be loaded.")
            installed_platform_keys = []        
        output_queue = queue.Queue()
        stop_event = threading.Event()
        search_results_data = []
        sort_states = {}
        search_process_active = False
        download_process_active = False
        _last_message_was_empty = False
        _download_cancelled = False
        _created_credential_tabs = set()
        credential_tab_frames = {}
        _context_menu = None
        _target_widget = None
        patch_download_file_for_cancellation()
        print("[Patch] Enabled improved download cancellation")
        _hide_menu_binding_id = None
        BUTTON_COLOR = ("#E0E0E0", "#343638")
        BORDER = "#565B5E"
        current_settings = {}
        settings_vars = {"globals": {}, "credentials": {}}
        orpheus_instance = None
        _settings_just_created = False
        try:
            # Check if this is first run (settings file doesn't exist yet)
            _settings_just_created = not os.path.exists(CONFIG_FILE_PATH)
            load_settings()
            if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                print(f"[DEBUG] After load_settings: output_path = {current_settings.get('globals', {}).get('general', {}).get('output_path')}")
            
            # Initialization moved to background thread to speed up startup
            pass
        except FileNotFoundError as e:
             print(f"Initialization failed: {e}")
             sys.exit(1)
        except Exception as e:
             print(f"Unexpected error during initialization: {e}")
        if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
            print(f"[DEBUG] Before GUI setup: output_path = {current_settings.get('globals', {}).get('general', {}).get('output_path')}")
        customtkinter.set_appearance_mode("dark")
        
        # Pass className directly to constructor to set WM_CLASS correctly on Linux
        if platform.system() == "Linux":
            app = customtkinter.CTk(className="orpheusdl_gui")
        else:
            app = customtkinter.CTk()
            
        # Use alpha to hide window instead of withdraw, as withdraw can cause issues on some systems
        app.attributes('-alpha', 0)
        app.title("OrpheusDL GUI")
        app.geometry("940x600")
        
        # Set initial size
        app.geometry("940x600")
        app.update() # Force update to ensure window is created and resized
        
        scaling = app._get_window_scaling()
        screen_width = app.winfo_screenwidth()
        screen_height = app.winfo_screenheight()
        
        # Get actual window dimensions (physical pixels)
        actual_width = app.winfo_width()
        actual_height = app.winfo_height()
        
        # Calculate center position in physical pixels
        x_phys = (screen_width - actual_width) // 2
        y_phys = (screen_height - actual_height) // 2
        
        # On Windows with Per-Monitor DPI awareness, geometry() position (+x+y) 
        # is often interpreted as physical pixels, while size (WxH) is logical.
        if platform.system() == "Windows":
            app.geometry(f"+{x_phys}+{y_phys}")
        else:
            # On other platforms, convert physical position to logical points
            x_logical = int(x_phys / scaling)
            y_logical = int(y_phys / scaling)
            app.geometry(f"+{x_logical}+{y_logical}")
        
        # Set icon after window geometry is established
        try:
            # On Linux, use PNG and wm_iconphoto
            if platform.system() == "Linux":
                icon_filename = "icon.png"
                icon_path = resource_path(icon_filename)
                print(f"[Icon] Linux detected. Looking for icon at: {icon_path}")
                
                if os.path.exists(icon_path):
                    try:
                        icon_image = tkinter.PhotoImage(file=icon_path)
                        # Use wm_iconphoto(True, ...) to set it for all future toplevels too
                        app.wm_iconphoto(True, icon_image)
                        print(f"[Icon] Successfully set Linux icon using app.wm_iconphoto")
                    except Exception as e_linux:
                        print(f"[Icon] Linux wm_iconphoto failed: {e_linux}")
            else:
                # Windows/macOS logic
                icon_filename = "icon.icns" if platform.system() == "Darwin" else "icon.ico"
                icon_path = resource_path(icon_filename)
                
                # Always print icon path for debugging this issue
                print(f"[Icon] Looking for icon at: {icon_path}")
                print(f"[Icon] File exists: {os.path.exists(icon_path)}")
                print(f"[Icon] Absolute path: {os.path.abspath(icon_path)}")
                
                if os.path.exists(icon_path):
                    if platform.system() != "Darwin":
                        # Try multiple methods to set the icon
                        try:
                            app.iconbitmap(icon_path)
                            print(f"[Icon] Successfully set icon using app.iconbitmap")
                            # Also set as default for child windows (Toplevel inheritance)
                            try:
                                app.iconbitmap(default=icon_path)
                            except Exception:
                                pass
                        except Exception as e1:
                            print(f"[Icon] app.iconbitmap failed: {e1}")
                            try:
                                # Try accessing the underlying tk window
                                app.tk.call('wm', 'iconbitmap', app._w, icon_path)
                                print(f"[Icon] Successfully set icon using tk.call")
                                # Also set as default for child windows
                                try:
                                    app.tk.call('wm', 'iconbitmap', app._w, '-default', icon_path)
                                except Exception:
                                    pass
                            except Exception as e2:
                                print(f"[Icon] tk.call failed: {e2}")
                else:
                    print(f"[Icon] ERROR: Icon file not found at: {icon_path}")
        except Exception as e:
            print(f"[Icon] ERROR setting window icon: {e}")
            import traceback
            traceback.print_exc()

        global loaded_credential_tabs, credential_tabs_config
        loaded_credential_tabs = {"Global"}
        credential_tabs_config = {}

        def _on_tab_change():
            selected_tab = tabview.get()
            if selected_tab == "Search":
                pass
            elif selected_tab == "Settings":
                if 'settings_tabview' in globals() and settings_tabview and settings_tabview.winfo_exists() and '_handle_settings_tab_change' in globals() and callable(_handle_settings_tab_change):
                     app.after(10, _handle_settings_tab_change)

        tabview = customtkinter.CTkTabview(master=app, command=_on_tab_change)
        tabview.pack(padx=10, pady=10, expand=True, fill="both")
        download_tab = tabview.add("Download")
        download_tab.grid_columnconfigure(1, weight=1); download_tab.grid_rowconfigure(2, weight=1)
        url_frame = customtkinter.CTkFrame(download_tab, fg_color="transparent"); url_frame.grid(row=0, column=0, columnspan=4, sticky="ew", padx=10, pady=(15,5)); url_frame.grid_columnconfigure(1, weight=1)
        url_label = customtkinter.CTkLabel(url_frame, text="Input"); url_label.grid(row=0, column=0, sticky="w", padx=5)
        url_entry = customtkinter.CTkEntry(url_frame, placeholder_text="Enter URL or text-file (e.g. urls.txt)...", height=30, placeholder_text_color="#7F7F7F"); url_entry.grid(row=0, column=1, sticky="ew", padx=5)
        url_entry.bind("<Return>", lambda event: start_download_thread()); url_entry.bind("<Button-3>", show_context_menu); url_entry.bind("<Button-2>", show_context_menu); url_entry.bind("<Control-Button-1>", show_context_menu)
        url_entry.bind("<Control-c>", _handle_ctrl_c_copy); url_entry.bind("<Control-C>", _handle_ctrl_c_copy)
        url_entry.bind("<FocusIn>", lambda e, w=url_entry: handle_focus_in(w))
        url_entry.bind("<FocusOut>", lambda e, w=url_entry: handle_focus_out(w))
        clear_url_button = customtkinter.CTkButton(url_frame, text="Clear", width=100, height=30, command=clear_url_entry, fg_color="#343638", hover_color="#1F6AA5"); clear_url_button.grid(row=0, column=2, sticky="e", padx=5)
        download_button = customtkinter.CTkButton(url_frame, text="Download", width=100, height=30, command=start_download_thread, fg_color="#343638", hover_color="#1F6AA5", state="disabled"); download_button.grid(row=0, column=3, sticky="e", padx=5)
        path_frame = customtkinter.CTkFrame(download_tab, fg_color="transparent"); path_frame.grid(row=1, column=0, columnspan=4, sticky="ew", padx=10, pady=5); path_frame.grid_columnconfigure(1, weight=1)
        path_label = customtkinter.CTkLabel(path_frame, text="Output Path"); path_label.grid(row=0, column=0, sticky="w", padx=5)
        path_var_main = tkinter.StringVar(value=current_settings.get("globals", {}).get("general", {}).get("output_path", DEFAULT_SETTINGS["globals"]["general"]["output_path"]))
        path_var_main.trace_add("write", _auto_save_path_change)
        path_entry = customtkinter.CTkEntry(path_frame, textvariable=path_var_main, height=30); path_entry.grid(row=0, column=1, sticky="ew", padx=5)
        path_entry.bind("<Button-3>", show_context_menu); path_entry.bind("<Button-2>", show_context_menu); path_entry.bind("<Control-Button-1>", show_context_menu)
        path_entry.bind("<Control-c>", _handle_ctrl_c_copy); path_entry.bind("<Control-C>", _handle_ctrl_c_copy)
        path_entry.bind("<FocusIn>", lambda e, w=path_entry: handle_focus_in(w))
        path_entry.bind("<FocusOut>", lambda e, w=path_entry: handle_focus_out(w))
        path_button = customtkinter.CTkButton(path_frame, text="Browse", width=100, height=30, command=lambda: browse_output_path(path_var_main), fg_color="#343638", hover_color="#1F6AA5"); path_button.grid(row=0, column=2, sticky="e", padx=5)
        open_path_button = customtkinter.CTkButton(path_frame, text="Open", width=100, height=30, command=open_download_path, fg_color="#343638", hover_color="#1F6AA5"); open_path_button.grid(row=0, column=3, sticky="e", padx=5)
        output_frame = customtkinter.CTkFrame(download_tab, fg_color="transparent"); output_frame.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=15, pady=(15, 15)); output_frame.grid_rowconfigure(1, weight=1); output_frame.grid_columnconfigure(0, weight=1)
        output_label = customtkinter.CTkLabel(output_frame, text="OUTPUT", text_color="#898c8d", font=("Segoe UI", 11)); output_label.grid(row=0, column=0, sticky="w", pady=(0, 3)) 
        textbox_container = customtkinter.CTkFrame(output_frame, fg_color="#1D1E1E"); textbox_container.grid(row=1, column=0, sticky="nsew"); textbox_container.grid_columnconfigure(0, weight=1); textbox_container.grid_rowconfigure(0, weight=1); textbox_container.grid_columnconfigure(1, weight=0)  
        current_os = platform.system()
        if current_os == "Windows":
            log_font_family = "Consolas"
            log_font_size = 10
        elif current_os == "Darwin":
            log_font_family = "Menlo"
            log_font_size = 12
        else:
            log_font_family = "DejaVu Sans Mono"
            log_font_size = 11
        log_font = (log_font_family, log_font_size)

        log_textbox = tkinter.Text(textbox_container, wrap=tkinter.WORD, state='disabled', font=log_font, 
                                   bg="#1D1E1E", fg="#DCE4EE", insertbackground="#DCE4EE", 
                                   selectbackground="#1F6AA5", selectforeground="#FFFFFF",
                                   relief="flat", borderwidth=0, highlightthickness=0)
        log_textbox.grid(row=0, column=0, sticky="nsew", padx=(5,0), pady=3)
        log_scrollbar = customtkinter.CTkScrollbar(textbox_container, command=log_textbox.yview); log_textbox.configure(yscrollcommand=log_scrollbar.set)
        log_textbox.bind("<Configure>", lambda event: _check_and_toggle_text_scrollbar(log_textbox, log_scrollbar) if 'log_textbox' in globals() and log_textbox and log_textbox.winfo_exists() and 'log_scrollbar' in globals() and log_scrollbar and log_scrollbar.winfo_exists() else None)
        bottom_frame = customtkinter.CTkFrame(download_tab, fg_color="transparent"); bottom_frame.grid(row=3, column=0, columnspan=4, sticky="ew", padx=10, pady=(5, 10)); bottom_frame.grid_columnconfigure(0, weight=1)
        progress_bar = customtkinter.CTkProgressBar(bottom_frame); progress_bar.set(0); progress_bar.grid(row=0, column=0, sticky="ew", padx=(5, 5))
        clear_output_button = customtkinter.CTkButton(bottom_frame, text="Clear Output", width=100, height=30, command=clear_output_log, fg_color="#343638", hover_color="#1F6AA5"); clear_output_button.grid(row=0, column=1, sticky="e", padx=(5, 10))
        stop_button = customtkinter.CTkButton(bottom_frame, text="Stop", width=100, height=30, command=stop_download, fg_color="#343638", hover_color="#1F6AA5", state=tkinter.DISABLED); stop_button.grid(row=0, column=2, sticky="e", padx=(0, 5))
        search_tab = tabview.add("Search"); search_main_frame = customtkinter.CTkFrame(search_tab, fg_color="transparent"); search_main_frame.pack(fill="both", expand=True, padx=9, pady=(10,0))
        # Add extra top padding to align with download tab (which has 2 input rows)
        controls_frame = customtkinter.CTkFrame(search_main_frame, fg_color="transparent"); controls_frame.pack(fill="x", pady=(5, 20)); controls_frame.grid_columnconfigure(4, weight=1)
        customtkinter.CTkLabel(controls_frame, text="Platform").grid(row=0, column=0, padx=(5,1), sticky="w")
        search_tab_initial_platforms = [pk for pk in installed_platform_keys if pk != "Musixmatch"]
        platform_var = tkinter.StringVar(value=search_tab_initial_platforms[0] if search_tab_initial_platforms else ""); 
        platform_combo = customtkinter.CTkComboBox(controls_frame, values=search_tab_initial_platforms, variable=platform_var, width=140, state="readonly", height=30, dropdown_fg_color="#2B2B2B"); 
        platform_combo.grid(row=0, column=1, padx=(5, 6)); 
        platform_var.trace_add("write", on_platform_change)

        customtkinter.CTkLabel(controls_frame, text="Type").grid(row=0, column=2, padx=(5,5), sticky="w")
        type_var = tkinter.StringVar()
        type_combo = customtkinter.CTkComboBox(controls_frame, values=[], variable=type_var, width=100, state="readonly", height=30, dropdown_fg_color="#2B2B2B")
        type_combo.grid(row=0, column=3, padx=(2, 1), sticky="w")
        type_var.trace_add("write", _update_search_placeholder)
        search_input_frame = customtkinter.CTkFrame(controls_frame, fg_color="transparent"); search_input_frame.grid(row=0, column=4, sticky="ew", padx=(10, 5))
        search_entry = customtkinter.CTkEntry(search_input_frame, placeholder_text="Enter search query...", height=30, placeholder_text_color="#7F7F7F"); search_entry.pack(side="left", fill="x", expand=True, padx=(0, 0))
        search_entry.bind("<Return>", lambda e: start_search()); search_entry.bind("<Button-3>", show_context_menu); search_entry.bind("<Button-2>", show_context_menu); search_entry.bind("<Control-Button-1>", show_context_menu)
        search_entry.bind("<Control-c>", _handle_ctrl_c_copy); search_entry.bind("<Control-C>", _handle_ctrl_c_copy)
        search_entry.bind("<FocusIn>", lambda e, w=search_entry: handle_focus_in(w))
        search_entry.bind("<FocusOut>", lambda e, w=search_entry: handle_focus_out(w))
        clear_search_button = customtkinter.CTkButton(search_input_frame, text="Clear", command=clear_search_entry, width=100, height=30, fg_color="#343638", hover_color="#1F6AA5"); clear_search_button.pack(side="left", padx=(10, 0))
        button_search_frame = customtkinter.CTkFrame(controls_frame, fg_color="transparent"); button_search_frame.grid(row=0, column=5, padx=(5,0))
        search_button = customtkinter.CTkButton(button_search_frame, text="Search", command=start_search, width=100, height=30, fg_color="#343638", hover_color="#1F6AA5", state="disabled"); search_button.pack(side="left", padx=(0, 6))
        update_search_types(platform_var.get())
        # Pack selection frame FIRST (at bottom) so it reserves space before the expanding results frame
        selection_label_var = tkinter.StringVar(value="Selection: None")
        selection_frame = customtkinter.CTkFrame(search_main_frame, fg_color="transparent"); selection_frame.pack(fill="x", pady=(5, 10), side="bottom")
        search_progress_bar = customtkinter.CTkProgressBar(selection_frame); search_progress_bar.pack(side="left", fill="x", expand=True, padx=(6, 5)); search_progress_bar.set(0)
        selection_controls_frame = customtkinter.CTkFrame(selection_frame, fg_color="transparent"); selection_controls_frame.pack(side="right")
        customtkinter.CTkLabel(selection_controls_frame, text="Selection").pack(side="left", padx=(8, 6)); selection_var = tkinter.StringVar(); selection_entry = customtkinter.CTkEntry(selection_controls_frame, textvariable=selection_var, width=35, height=30); selection_entry.pack(side="left", padx=4); selection_var.trace_add("write", on_selection_change)
        selection_entry.bind("<FocusIn>", lambda e, w=selection_entry: handle_focus_in(w))
        selection_entry.bind("<FocusOut>", lambda e, w=selection_entry: handle_focus_out(w))
        search_download_button = customtkinter.CTkButton(selection_controls_frame, text="Download", command=download_selected, width=100, height=30, state="disabled", fg_color="#343638", hover_color="#1F6AA5"); search_download_button.pack(side="left", padx=(5, 6))
        # Now pack the results frame which will expand to fill remaining space
        results_outer_frame = customtkinter.CTkFrame(search_main_frame, fg_color="transparent"); results_outer_frame.pack(fill="both", expand=True, pady=(8,15))
        # Results header: optional "← Back" (left), then RESULTS / Album: ... label, then volume
        results_header_frame = customtkinter.CTkFrame(results_outer_frame, fg_color="transparent"); results_header_frame.pack(fill="x", padx=0, pady=0)
        _back_to_search_button = customtkinter.CTkButton(
            results_header_frame,
            text="← Back",
            width=80,
            height=24,
            font=("Segoe UI", 11),
            fg_color=BUTTON_COLOR,
            hover_color="#1F6AA5",
            command=_back_to_search_results
        )
        _back_to_search_button.pack(side="left", anchor="w", padx=(6, 12), pady=0)
        _back_to_search_button.pack_forget()  # Hidden until user opens an album/playlist track list
        results_label = customtkinter.CTkLabel(results_header_frame, text="RESULTS", text_color="#898c8d", font=("Segoe UI", 11)); results_label.pack(side="left", anchor="w", padx=6, pady=0)
        # Label shown after 8s when expand takes long (walking dots + "(this can take up to ~1 minute)")
        globals()["_expand_loading_label"] = customtkinter.CTkLabel(results_header_frame, text="", text_color="#898c8d", font=("Segoe UI", 11))
        _expand_loading_label.pack_forget()
        # Content-type badge (Album / Playlist / Artist) with border; tight padding so border sits close to text
        _content_type_badge = customtkinter.CTkFrame(results_header_frame, fg_color="transparent", border_width=1, border_color="#565B5E", corner_radius=6, width=50, height=22)
        try:
            _content_type_badge.pack_propagate(False)  # keep fixed size
        except AttributeError:
            pass
        _content_type_badge_label = customtkinter.CTkLabel(_content_type_badge, text="Album", text_color="#898c8d", font=("Segoe UI", 11))
        _content_type_badge_label.pack(padx=8, pady=1)  # tight horizontal padding so border is close to text
        # Badge is not packed here; _update_results_header_context() packs it when showing album/playlist/artist view
        # Volume control frame (Windows only; macOS/Linux cannot regulate volume from GUI)
        if platform.system() == "Windows":
            _volume_frame = customtkinter.CTkFrame(results_header_frame, fg_color="transparent")
            _volume_label = customtkinter.CTkLabel(_volume_frame, text="VOLUME", text_color="#898c8d", font=("Segoe UI", 10)); _volume_label.pack(side="left", padx=(0, 8))
            _volume_slider = customtkinter.CTkSlider(_volume_frame, from_=0, to=100, number_of_steps=100, width=120, height=16, command=on_volume_change); _volume_slider.set(_current_volume); _volume_slider.pack(side="left", padx=(0, 0))
        else:
            _volume_frame = None
            _volume_slider = None
            _volume_label = None
        treeview_container = customtkinter.CTkFrame(results_outer_frame, fg_color="#1D1E1E"); treeview_container.pack(fill="both", expand=True, padx=6, pady=(3,0)); treeview_container.grid_columnconfigure(0, weight=1); treeview_container.grid_rowconfigure(0, weight=1); treeview_container.grid_columnconfigure(1, weight=0)
        style = ttk.Style();
        try: style.theme_use('clam')
        except Exception: print("Clam theme not available.")
        heading_font_config = None

        if platform.system() == "Windows":
            try:
                scaling_factor = app.tk.call('tk', 'scaling')
                if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                    print(f"[Style] Detected scaling factor: {scaling_factor}")
            except Exception as e:
                print(f"[Style] Error getting scaling factor: {e}. Defaulting to 1.0")
                scaling_factor = 1.0
            if scaling_factor > 1.5:
                base_font_size = 6
            else:
                base_font_size = 7

            scaled_font_size = max(8, round(base_font_size * scaling_factor))
            if scaling_factor > 1.5:
                row_height_multiplier = 3.4
            else:
                row_height_multiplier = 2.9

            scaled_row_height = max(COVER_SIZE + 4, round(scaled_font_size * row_height_multiplier))  # Ensure row fits cover image
            tree_font_family = "Segoe UI"
            if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                print(f"[Style Windows] Using font: {tree_font_family} {scaled_font_size}pt (Scaled from {base_font_size}pt), Row height: {scaled_row_height}px")
            heading_font_config = (tree_font_family, scaled_font_size)

        else:
            scaled_font_size = 13
            scaled_row_height = max(COVER_SIZE + 4, round(scaled_font_size * 2.2))  # Ensure row fits cover image
            tree_font_family = None
            if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                print(f"[Style Non-Windows] Using system default font, Row height: {scaled_row_height}px")
            heading_font_config = (None, 10, 'normal')
        tree_bg_color = "#1D1E1E"; tree_fg_color = "#DCE4EE"; tree_header_bg = "#1D1E1E"; tree_header_fg = "gray"; tree_selected_bg = "#1F6AA5"; tree_selected_fg = "#FFFFFF"
        style.configure("Custom.Treeview",
                        background=tree_bg_color,
                        foreground=tree_fg_color,
                        fieldbackground=tree_bg_color,
                        borderwidth=0,
                        relief="flat",
                        rowheight=scaled_row_height)
        if platform.system() == "Windows":
            style.configure("Custom.Treeview", font=(tree_font_family, scaled_font_size))
        style.configure("Custom.Treeview.Heading",
                        background=tree_header_bg,
                        foreground=tree_header_fg,
                        borderwidth=0,
                        relief="flat",
                        padding=(5, 3))
        if heading_font_config:
            style.configure("Custom.Treeview.Heading", font=heading_font_config)

        # Custom layout to minimize all padding
        style.layout("Custom.Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
        style.layout("Custom.Treeview.Item", [
            ('Treeitem.padding', {'sticky': 'nswe', 'children': [
                ('Treeitem.image', {'side': 'left', 'sticky': ''}),
                ('Treeitem.text', {'side': 'left', 'sticky': ''})
            ]})
        ])
        # Minimize indent/padding for cover column
        style.configure("Custom.Treeview", indent=0, padding=0)
        style.configure("Custom.Treeview.Item", padding=0)
        style.map("Custom.Treeview", background=[('selected', tree_selected_bg)], foreground=[('selected', tree_selected_fg)])
        style.map("Custom.Treeview.Heading", background=[('active', "#1F6AA5"), ('!active', tree_header_bg)], foreground=[('active', tree_selected_fg), ('!active', tree_header_fg)])
        columns = ("Preview", "#", "Title", "Artist", "Duration", "Year", "Additional", "Explicit", "ID"); tree = ttk.Treeview(treeview_container, columns=columns, show="tree headings", selectmode="extended", style="Custom.Treeview"); tree.grid(row=0, column=0, sticky="nsew", padx=(4,0), pady=3)
        # Configure tree column (#0) for cover images (tight fit, left-aligned)
        tree.column("#0", width=COVER_SIZE + 6, minwidth=COVER_SIZE + 6, stretch=False, anchor="w")
        tree.heading("#0", text="", anchor="center")
        col_configs = {"#": {"text": "#", "width": 40, "anchor": "w"}, "Preview": {"text": "▶", "width": 56, "anchor": "center"}, "Title": {"text": "Title", "width": 300, "anchor": "w"}, "Artist": {"text": "Artist", "width": 200, "anchor": "w"}, "Duration": {"text": "Time", "width": 65, "anchor": "center"}, "Year": {"text": "Year", "width": 60, "anchor": "center"}, "Additional": {"text": "Additional", "width": 120, "anchor": "w"}, "Explicit": {"text": "🅴", "width": 30, "anchor": "center"}, "ID": {"text": "ID", "width": 0, "anchor": "w"}}
        for col in columns: cfg = col_configs[col]; tree.heading(col, text=cfg["text"], anchor=cfg["anchor"], command=lambda c=col: sort_results(c) if c not in ("Preview",) else None); tree.column(col, width=cfg["width"], anchor=cfg["anchor"], stretch=False)
        tree.column("Title", stretch=True); tree.column("Artist", stretch=True)
        # Omit ID from display so theme never draws zero-width slot (avoids right-edge streak)
        tree["displaycolumns"] = _TREE_DISPLAYCOLUMNS
        # Custom scroll handler to trigger lazy loading and refresh platform icon overlay
        def tree_scroll_handler(*args):
            tree.yview(*args)
            on_tree_scroll()  # Trigger lazy loading
        scrollbar = customtkinter.CTkScrollbar(treeview_container, command=tree_scroll_handler); tree.configure(yscrollcommand=scrollbar.set)
        def _on_tree_configure_refresh(event=None):
            if 'tree' not in globals() or not tree or not tree.winfo_exists():
                return
            _check_and_toggle_scrollbar(tree, scrollbar) if 'scrollbar' in globals() and scrollbar and scrollbar.winfo_exists() else None
        tree.bind("<<TreeviewSelect>>", on_tree_select); tree.bind("<Configure>", _on_tree_configure_refresh)
        # Bind mousewheel for lazy loading on scroll
        tree.bind("<MouseWheel>", lambda e: on_tree_scroll())  # Windows
        tree.bind("<Button-4>", lambda e: on_tree_scroll())    # Linux scroll up
        tree.bind("<Button-5>", lambda e: on_tree_scroll())    # Linux scroll down
        # Setup preview button tags for colored icons
        setup_preview_tags(tree)
        tree.bind("<Button-1>", lambda event: on_tree_click(event), add="+")
        # Preview column hover handlers for cursor change
        tree.bind("<Motion>", on_tree_motion)
        tree.bind("<Leave>", on_tree_leave)
        # Right-click context menu bindings for search results
        tree.bind("<Button-3>", show_search_context_menu)  # Windows/Linux right-click
        tree.bind("<Button-2>", show_search_context_menu)  # macOS right-click (some configs)
        if platform.system() == "Darwin":
            tree.bind("<Control-Button-1>", show_search_context_menu)  # macOS Ctrl+click
        if platform.system() == "Darwin":
            def handle_macos_click(event):
                """Handle macOS-specific multi-selection with Command/Shift keys."""
                # First, check if this is a click on the Preview column or Cover column
                column = tree.identify_column(event.x)
                if column == "#1" or column == "#0":  # Preview column or Cover column
                    on_tree_click(event)
                    return "break"
                
                item = tree.identify_row(event.y)
                if not item:
                    return
                if event.state & 0x8:
                    if item in tree.selection():
                        tree.selection_remove(item)
                    else:
                        tree.selection_add(item)
                    return "break"
                elif event.state & 0x1:
                    current_selection = tree.selection()
                    if current_selection:
                        all_items = tree.get_children()
                        try:
                            last_selected = current_selection[-1]
                            start_idx = all_items.index(last_selected)
                            end_idx = all_items.index(item)
                            if start_idx > end_idx:
                                start_idx, end_idx = end_idx, start_idx
                            tree.selection_set(all_items[start_idx:end_idx + 1])
                        except (ValueError, IndexError):
                            tree.selection_set(item)
                    else:
                        tree.selection_set(item)
                    return "break"
                tree.selection_set(item)
                return "break"
            tree.bind("<Button-1>", handle_macos_click)
        settings_tab = tabview.add("Settings")
        settings_tabview = customtkinter.CTkTabview(master=settings_tab, command=_handle_settings_tab_change)
        settings_tabview.pack(expand=True, fill="both", padx=5, pady=5)
        global_settings_tab = settings_tabview.add("Global")
        global_settings_frame = customtkinter.CTkScrollableFrame(global_settings_tab)
        global_settings_frame.pack(expand=True, fill="both", padx=5, pady=(0, 5))
        global_settings_frame.grid_columnconfigure(1, weight=1)
        global_settings_frame.grid_columnconfigure(0, uniform="settings_label_column")
        global_settings_frame.grid_columnconfigure(2, weight=0)
        row = 0
        tooltip_texts = {
            "general.output_path": "The main folder where all downloads will be saved.",
            "general.quality": "Select the desired audio quality preference.",
            "general.search_limit": "Maximum number of results to display in the Search tab.",
            "general.concurrent_downloads": "Number of tracks to download simultaneously (1-10).\n\nRecommended values:\n• 1-3: Slower systems, limited bandwidth\n• 4-6: Most systems (balanced speed/stability)\n• 7-10: High-end systems, fast internet.",
            "general.play_sound_on_finish": "Play a notification sound when a download completes.",
            "artist_downloading.return_credited_albums": "Include albums where the artist is credited but not the main artist.",
            "artist_downloading.separate_tracks_skip_downloaded": "When downloading artists, skip tracks that are part of albums already downloaded.",
            "formatting.album_format": """Folder structure for albums. Variables:
 {name}, {id}, {artist}, {artist_id}, {release_year}, {upc}, {explicit}, {quality}, {artist_initials}""",
            "formatting.playlist_format": """Folder structure for playlists. Variables:
 {name}, {creator}, {tracks}, {release_year}, {explicit}, {creator_id}""",
            "formatting.track_filename_format": """Filename format for tracks. Variables:
 {track_number}, {total_tracks}, {disc_number}, {total_discs}, {name}, {id}, {album},
 {album_id}, {artist}, {artist_id}, {isrc}, {release_year}, {explicit}, {quality}, {artist_initials}""",
            "formatting.single_full_path_format": """Full path format (folder + filename) for single tracks not part of an album download.\nUses same variables as Track Filename Format.""",
            "formatting.enable_zfill": "Pads track/disc numbers with leading zeros (e.g., 01, 02).",
            "formatting.force_album_format": "Use the album_format structure even for single track downloads.",
            "codecs.proprietary_codecs": "Enable potentially proprietary codecs like MQA (if supported by module).",
            "codecs.spatial_codecs": "Enable spatial audio codecs like Dolby Atmos (if supported by module).",
            "module_defaults.lyrics": "Default module to use for fetching lyrics.",
            "module_defaults.covers": "Default module to use for fetching cover art.",
            "module_defaults.credits": "Default module to use for fetching track credits.",
            "lyrics.embed_lyrics": "Embed standard (unsynced) lyrics into the audio file.",
            "lyrics.embed_synced_lyrics": "Embed synced (LRC) lyrics into the audio file (requires embed_lyrics).",
            "lyrics.save_synced_lyrics": "Save synced lyrics as a separate .lrc file alongside the track.",
            "covers.embed_cover": "Embed the main cover art into the audio file.",
            "covers.main_compression": "Compression level for embedded/saved main cover art.",
            "covers.main_resolution": "Maximum resolution (pixels) for the main cover art.",
            "covers.save_external": "Save cover art from a third-party module (if configured).",
            "covers.external_format": "Format for the saved external cover art.",
            "covers.external_compression": "Compression level for the saved external cover art.",
            "covers.external_resolution": "Maximum resolution (pixels) for the saved external cover art.",
            "covers.save_animated_cover": "Save animated cover art (GIF/MP4) if available.",
            "playlist.save_m3u": "Create an M3U playlist file for playlist downloads.",
            "playlist.paths_m3u": "Select 'relative' or 'absolute' paths in M3U file.",
            "playlist.extended_m3u": "Include extended info like track length in M3U file.",
            "advanced.advanced_login_system": "Enable advanced login system (Use only if instructed by module documentation).",
            "advanced.ffmpeg_path": "Full path to the ffmpeg executable \nIf set to just 'ffmpeg', it's assumed to be in the system PATH.\nThis is used for codec conversions.",
            "advanced.codec_conversions": "Defines custom codec conversions (e.g., alac to flac). Enter source format on the left, target on the right.",
            "advanced.conversion_keep_original": "Keep the original file after successful codec conversion.",
            "advanced.cover_variance_threshold": "Tolerance for accepting covers with slightly different sizes (0-100).",
            "advanced.debug_mode": "Allows various detailed informational and diagnostic messages to be printed to the console.\nIntended for troubleshooting issues only.",
            "advanced.disable_subscription_checks": "Prevents from checking if subscription for music service you are trying to download from is active.",
            "advanced.enable_undesirable_conversions": """Controls allowance to perform codec conversions that might result in quality loss or are not recommended.
Examples:
Lossy-to-Lossy
Lossless-to-Lossy (if not preferred)
Unnecessary Lossless-to-Lossless""",
            "advanced.ignore_existing_files": "Skips downloading files, if a file with the target name already exists in the output directory.",
            "advanced.ignore_different_artists": "When downloading albums, ignore tracks where the artist differs from the main album artist.",
            "advanced.hide_ffmpeg_warning": "Hide the warning message that appears when FFmpeg is not found on the system.",
            "advanced.conversion_flags.aac.audio_bitrate": "Set AAC audio bitrate. Higher is better quality but larger file. Options: 128k, 192k, 256k, 320k.",
            "advanced.conversion_flags.flac.compression_level": "Set FLAC compression level (0-8). Higher level means smaller file but slower encoding, 0 is fastest, 8 is smallest."
        }
        for section_key, section_value in DEFAULT_SETTINGS["globals"].items():
            if isinstance(section_value, dict):
                customtkinter.CTkLabel(global_settings_frame, text=section_key.replace("_", " ").upper(), text_color="#898c8d", font=("Segoe UI", 11)).grid(row=row, column=0, columnspan=3, sticky="w", padx=(0, 10), pady=(10, 5)); row += 1
                for field, default_value in section_value.items():
                    current_value = current_settings["globals"].get(section_key, {}).get(field, default_value); full_key = f"{section_key}.{field}"
                    if full_key == "advanced.conversion_flags":
                        aac_label_text = "AAC Audio Bitrate"
                        aac_full_key = "advanced.conversion_flags.aac.audio_bitrate"
                        aac_default_val = DEFAULT_SETTINGS["globals"]["advanced"]["conversion_flags"]["aac"]["audio_bitrate"]
                        aac_current_val = str(current_settings["globals"].get("advanced", {}).get("conversion_flags", {}).get("aac", {}).get("audio_bitrate", aac_default_val))
                        
                        customtkinter.CTkLabel(global_settings_frame, text=aac_label_text).grid(row=row, column=0, sticky="w", padx=(20, 10), pady=2)
                        aac_slider_frame = customtkinter.CTkFrame(global_settings_frame, fg_color="transparent")
                        aac_slider_frame.grid(row=row, column=1, sticky="ew", padx=(5, 5), pady=2)
                        aac_slider_frame.grid_columnconfigure(0, weight=1)

                        aac_options_list = ["128k", "192k", "256k", "320k"]
                        aac_options_map = {val: i for i, val in enumerate(aac_options_list)}
                        
                        aac_var = tkinter.StringVar(value=aac_current_val)
                        if "globals" not in settings_vars: settings_vars["globals"] = {}
                        settings_vars["globals"][aac_full_key] = aac_var
                        
                        # Value label in column 2 (like Browse button position)
                        aac_value_disp_label = customtkinter.CTkLabel(global_settings_frame, text=aac_current_val, width=100, anchor="center")
                        aac_value_disp_label.grid(row=row, column=2, sticky="e", padx=(5, 5))

                        def _update_aac_slider_display(slider_value_idx, var=aac_var, disp_label=aac_value_disp_label):
                            selected_bitrate = aac_options_list[int(slider_value_idx)]
                            var.set(selected_bitrate)
                            disp_label.configure(text=selected_bitrate)

                        aac_slider_pos = aac_options_map.get(aac_current_val, aac_options_map.get(aac_default_val, 2))
                        aac_slider_widget = customtkinter.CTkSlider(aac_slider_frame, from_=0, to=len(aac_options_list)-1, number_of_steps=len(aac_options_list)-1, command=_update_aac_slider_display)
                        aac_slider_widget.set(aac_slider_pos)
                        aac_slider_widget.grid(row=0, column=0, sticky="ew")
                        CTkToolTip(aac_slider_frame, message=tooltip_texts.get(aac_full_key, ""), bg_color=TOOLTIP_MENU_BG, text_color="#dddddd")
                        row += 1
                        flac_label_text = "FLAC Compression Level"
                        flac_full_key = "advanced.conversion_flags.flac.compression_level"
                        flac_default_val = DEFAULT_SETTINGS["globals"]["advanced"]["conversion_flags"]["flac"]["compression_level"]
                        flac_current_val = int(current_settings["globals"].get("advanced", {}).get("conversion_flags", {}).get("flac", {}).get("compression_level", flac_default_val))

                        customtkinter.CTkLabel(global_settings_frame, text=flac_label_text).grid(row=row, column=0, sticky="w", padx=(20, 10), pady=2)
                        flac_slider_frame = customtkinter.CTkFrame(global_settings_frame, fg_color="transparent")
                        flac_slider_frame.grid(row=row, column=1, sticky="ew", padx=(5, 5), pady=2)
                        flac_slider_frame.grid_columnconfigure(0, weight=1)
                        
                        flac_var = tkinter.StringVar(value=str(flac_current_val))
                        settings_vars["globals"][flac_full_key] = flac_var

                        # Value label in column 2 (like Browse button position)
                        flac_value_disp_label = customtkinter.CTkLabel(global_settings_frame, text=str(flac_current_val), width=100, anchor="center")
                        flac_value_disp_label.grid(row=row, column=2, sticky="e", padx=(5, 5))

                        def _update_flac_slider_display(slider_value, var=flac_var, disp_label=flac_value_disp_label):
                            val_int = int(slider_value)
                            var.set(str(val_int))
                            disp_label.configure(text=str(val_int))
                        
                        flac_slider_widget = customtkinter.CTkSlider(flac_slider_frame, from_=0, to=8, number_of_steps=8, command=_update_flac_slider_display)
                        flac_slider_widget.set(flac_current_val)
                        flac_slider_widget.grid(row=0, column=0, sticky="ew")
                        CTkToolTip(flac_slider_frame, message=tooltip_texts.get(flac_full_key, ""), bg_color=TOOLTIP_MENU_BG, text_color="#dddddd")
                        row += 1
                        mp3_label_text = "MP3 Encoding"
                        mp3_setting_key = "advanced.conversion_flags.mp3.setting"
                        mp3_conf_flags = current_settings["globals"].get("advanced", {}).get("conversion_flags", {}).get("mp3", {})
                        mp3_default_conf_flags = DEFAULT_SETTINGS["globals"]["advanced"]["conversion_flags"]["mp3"]

                        mp3_options_list = ["128k", "192k", "256k", "320k", "VBR -V0"]
                        mp3_options_map = {val: i for i, val in enumerate(mp3_options_list)}
                        
                        current_mp3_display_val = "VBR -V0"
                        if "audio_bitrate" in mp3_conf_flags:
                            current_mp3_display_val = mp3_conf_flags["audio_bitrate"]
                        elif "qscale:a" in mp3_conf_flags and mp3_conf_flags["qscale:a"] == "0":
                            current_mp3_display_val = "VBR -V0"
                        
                        customtkinter.CTkLabel(global_settings_frame, text=mp3_label_text).grid(row=row, column=0, sticky="w", padx=(20, 10), pady=5)
                        mp3_slider_frame = customtkinter.CTkFrame(global_settings_frame, fg_color="transparent")
                        mp3_slider_frame.grid(row=row, column=1, sticky="ew", padx=(5, 5), pady=5)
                        mp3_slider_frame.grid_columnconfigure(0, weight=1)

                        mp3_var = tkinter.StringVar(value=current_mp3_display_val)
                        settings_vars["globals"][mp3_setting_key] = mp3_var
                        settings_vars["globals"].pop("advanced.conversion_flags.mp3.qscale:a", None)
                        settings_vars["globals"].pop("advanced.conversion_flags.mp3.audio_bitrate", None)

                        # Value label in column 2 (like Browse button position)
                        mp3_value_disp_label = customtkinter.CTkLabel(global_settings_frame, text=current_mp3_display_val, width=100, anchor="center")
                        mp3_value_disp_label.grid(row=row, column=2, sticky="e", padx=(5, 5))

                        def _update_mp3_slider_display(slider_value_idx, var=mp3_var, disp_label=mp3_value_disp_label):
                            selected_text = mp3_options_list[int(slider_value_idx)]
                            var.set(selected_text)
                            disp_label.configure(text=selected_text)

                        mp3_slider_pos = mp3_options_map.get(current_mp3_display_val, len(mp3_options_list)-1)
                        mp3_slider_widget = customtkinter.CTkSlider(mp3_slider_frame, from_=0, to=len(mp3_options_list)-1, number_of_steps=len(mp3_options_list)-1, command=_update_mp3_slider_display)
                        mp3_slider_widget.set(mp3_slider_pos)
                        mp3_slider_widget.grid(row=0, column=0, sticky="ew")
                        tooltip_mp3_text = tooltip_texts.get("advanced.conversion_flags.mp3.setting", "MP3 Encoding Settings:\n128k-320k are Constant Bitrate (CBR).\nVBR -V0 uses qscale:a 0 for highest variable bitrate quality.")
                        CTkToolTip(mp3_slider_frame, message=tooltip_mp3_text, bg_color=TOOLTIP_MENU_BG, text_color="#dddddd")
                        row += 1
                        continue
                    label_widget = customtkinter.CTkLabel(global_settings_frame, text=field.replace("_", " ").title())
                    label_widget.grid(row=row, column=0, sticky="w", padx=(10, 10), pady=5)
                    widget = None; browse_btn = None

                    if isinstance(default_value, bool):
                        var = tkinter.BooleanVar(value=bool(current_value)); settings_vars["globals"][full_key] = var
                        widget = customtkinter.CTkCheckBox(global_settings_frame, text="", variable=var)
                        widget.grid(row=row, column=1, sticky="w", padx=5, pady=5)
                    elif isinstance(default_value, dict):
                        if field == "codec_conversions":
                            codec_frame = customtkinter.CTkFrame(global_settings_frame, fg_color="transparent")
                            codec_frame.grid(row=row, column=1, sticky="ew", padx=5, pady=5, columnspan=2)
                            codec_frame.grid_columnconfigure(2, weight=1)
                            if isinstance(current_value, dict) and current_value:
                                current_conversions = current_value
                            else:
                                current_conversions = default_value if isinstance(default_value, dict) else {}
                            
                            conversion_row = 0
                            
                            if current_conversions:
                                for source_codec, target_codec in current_conversions.items():
                                    source_var = tkinter.StringVar(value=str(source_codec).lower())
                                    codec_options = ['flac', 'alac', 'wav', 'vorbis', 'mp3', 'aac', 'opus']
                                    source_dropdown = customtkinter.CTkComboBox(codec_frame, variable=source_var, values=codec_options, width=100, state="readonly", dropdown_fg_color="#2B2B2B")
                                    source_dropdown.grid(row=conversion_row, column=0, sticky="w", padx=(0, 3), pady=5)
                                    
                                    arrow_label = customtkinter.CTkLabel(codec_frame, text="---->", width=40)
                                    arrow_label.grid(row=conversion_row, column=1, sticky="w", padx=(0, 3), pady=5)
                                    target_var = tkinter.StringVar(value=str(target_codec).lower())
                                    target_dropdown = customtkinter.CTkComboBox(codec_frame, variable=target_var, values=codec_options, width=100, state="readonly", dropdown_fg_color="#2B2B2B")
                                    target_dropdown.grid(row=conversion_row, column=2, sticky="w", padx=(0, 5), pady=5)
                                    
                                    if full_key not in settings_vars["globals"]: settings_vars["globals"][full_key] = {}
                                    settings_vars["globals"][full_key][f"{source_codec}_source"] = source_var
                                    settings_vars["globals"][full_key][f"{source_codec}_target"] = target_var
                                    
                                    conversion_row += 1
                        else:
                            widget = customtkinter.CTkLabel(global_settings_frame, text="(Complex Setting)")
                            widget.grid(row=row, column=1, sticky="w", padx=5, pady=5)
                            settings_vars["globals"][full_key] = {}
                    else:
                         var = tkinter.StringVar(value=str(current_value)); settings_vars["globals"][full_key] = var
                         if section_key == "general" and field == "output_path":
                            # Add trace to sync Global Settings output_path → Download tab path_var_main
                            def _sync_global_settings_path_to_download_tab(*args, var_ref=var):
                                """Callback to sync Global Settings output_path changes to Download tab."""
                                global path_var_main, current_settings
                                try:
                                    new_path = var_ref.get()
                                    if not new_path:
                                        return
                                    # Update path_var_main in Download tab if it exists and differs
                                    if 'path_var_main' in globals() and path_var_main:
                                        current_download_tab_path = path_var_main.get()
                                        if new_path != current_download_tab_path:
                                            path_var_main.set(new_path)
                                    # Update in-memory settings
                                    if "globals" not in current_settings: current_settings["globals"] = {}
                                    if "general" not in current_settings["globals"]: current_settings["globals"]["general"] = {}
                                    current_settings["globals"]["general"]["output_path"] = new_path
                                    # Auto-save settings
                                    save_settings(show_confirmation=False)
                                except Exception as e:
                                    print(f"[Sync Error] Failed to sync Global Settings path to Download tab: {e}")
                            var.trace_add("write", _sync_global_settings_path_to_download_tab)
                            
                            widget = customtkinter.CTkEntry(global_settings_frame, textvariable=var)
                            widget.grid(row=row, column=1, sticky="ew", padx=(5, 5), pady=5)
                            widget.bind("<Button-3>", show_context_menu)
                            widget.bind("<Button-2>", show_context_menu)
                            widget.bind("<Control-Button-1>", show_context_menu)
                            widget.bind("<FocusIn>", lambda e, w=widget: handle_focus_in(w))
                            widget.bind("<FocusOut>", lambda e, w=widget: handle_focus_out(w))
                            browse_btn = customtkinter.CTkButton(global_settings_frame, text="Browse", width=100, height=30,
                                                               command=lambda v=var: browse_output_path(v),
                                                               fg_color=widget._fg_color, hover_color="#1F6AA5",
                                                               border_width=0, 
                                                               border_color=None)
                            browse_btn.grid(row=row, column=2, sticky="w", padx=(5, 5))
                         elif section_key == "general" and field == "quality":
                            quality_options = ["hifi", "lossless", "high", "low"]
                            current_val_str = var.get().lower()
                            if current_val_str not in quality_options: var.set(quality_options[0])
                            widget = customtkinter.CTkComboBox(global_settings_frame, variable=var, values=quality_options, state="readonly", dropdown_fg_color="#2B2B2B")
                            widget.grid(row=row, column=1, sticky="ew", padx=(5, 5), pady=2)
                         elif section_key == "general" and field == "concurrent_downloads":
                            try:
                                current_concurrent = int(var.get())
                                if current_concurrent < 1 or current_concurrent > 10:
                                    current_concurrent = 3
                            except (ValueError, TypeError):
                                current_concurrent = 3

                            slider_frame = customtkinter.CTkFrame(global_settings_frame, fg_color="transparent")
                            slider_frame.grid(row=row, column=1, sticky="ew", padx=(5, 5), pady=5)
                            slider_frame.grid_columnconfigure(0, weight=1)

                            # Value label in column 2 (like Browse button position)
                            value_label = customtkinter.CTkLabel(global_settings_frame, text=f"{current_concurrent}", width=100, anchor="center")
                            value_label.grid(row=row, column=2, sticky="e", padx=(5, 5))

                            def update_concurrent_value(value, var_ref=var, label_ref=value_label):
                                int_value = int(round(value))
                                var_ref.set(str(int_value))
                                label_ref.configure(text=f"{int_value}")

                            slider = customtkinter.CTkSlider(slider_frame, from_=1, to=10, number_of_steps=9, command=update_concurrent_value)
                            slider.set(current_concurrent)
                            slider.grid(row=0, column=0, sticky="ew")

                            var.set(str(current_concurrent))

                            widget = slider_frame
                         elif section_key == "covers" and field == "main_compression":
                            compression_options = ["high", "low"]
                            if var.get() not in compression_options: var.set(compression_options[0])
                            
                            radio_frame = customtkinter.CTkFrame(global_settings_frame, fg_color="transparent")
                            radio_frame.grid(row=row, column=1, sticky="ew", padx=5, pady=5, columnspan=2)
                            
                            high_radio = customtkinter.CTkRadioButton(radio_frame, text="High", variable=var, value="high")
                            high_radio.pack(side="left", padx=(0, 10))
                            
                            low_radio = customtkinter.CTkRadioButton(radio_frame, text="Low", variable=var, value="low")
                            low_radio.pack(side="left")
                            
                            widget = radio_frame
                         elif section_key == "covers" and field == "external_format":
                            format_options = ["png", "jpg", "webp"]
                            if var.get() not in format_options: var.set(format_options[0])
                            
                            radio_frame = customtkinter.CTkFrame(global_settings_frame, fg_color="transparent")
                            radio_frame.grid(row=row, column=1, sticky="ew", padx=5, pady=5, columnspan=2)
                            
                            png_radio = customtkinter.CTkRadioButton(radio_frame, text="PNG", variable=var, value="png")
                            png_radio.pack(side="left", padx=(0, 10))
                            
                            jpg_radio = customtkinter.CTkRadioButton(radio_frame, text="JPG", variable=var, value="jpg")
                            jpg_radio.pack(side="left", padx=(0, 10))
                            
                            webp_radio = customtkinter.CTkRadioButton(radio_frame, text="WebP", variable=var, value="webp")
                            webp_radio.pack(side="left")
                            
                            widget = radio_frame
                         elif section_key == "covers" and field == "external_compression":
                            compression_options = ["low", "high"]
                            if var.get() not in compression_options: var.set(compression_options[0])
                            
                            radio_frame = customtkinter.CTkFrame(global_settings_frame, fg_color="transparent")
                            radio_frame.grid(row=row, column=1, sticky="ew", padx=5, pady=5, columnspan=2)
                            
                            low_radio = customtkinter.CTkRadioButton(radio_frame, text="Low", variable=var, value="low")
                            low_radio.pack(side="left", padx=(0, 10))
                            
                            high_radio = customtkinter.CTkRadioButton(radio_frame, text="High", variable=var, value="high")
                            high_radio.pack(side="left")
                            
                            widget = radio_frame
                         elif section_key == "covers" and field == "main_resolution":
                            try:
                                current_res = int(var.get())
                                if current_res < 100 or current_res > 1400:
                                    current_res = 1400
                            except (ValueError, TypeError):
                                current_res = 1400
                            
                            current_res = round(current_res / 100) * 100
                            
                            slider_frame = customtkinter.CTkFrame(global_settings_frame, fg_color="transparent")
                            slider_frame.grid(row=row, column=1, sticky="ew", padx=(5, 5), pady=5)
                            slider_frame.grid_columnconfigure(0, weight=1)
                            
                            # Value label in column 2 (like Browse button position)
                            value_label = customtkinter.CTkLabel(global_settings_frame, text=f"{current_res}px", width=100, anchor="center")
                            value_label.grid(row=row, column=2, sticky="e", padx=(5, 5))
                            
                            def update_resolution_value(value, var_ref=var, label_ref=value_label):
                                int_value = round(value / 100) * 100
                                var_ref.set(str(int_value))
                                label_ref.configure(text=f"{int_value}px")
                        
                            slider = customtkinter.CTkSlider(slider_frame, from_=100, to=1400, number_of_steps=13, command=update_resolution_value)
                            slider.set(current_res)
                            slider.grid(row=0, column=0, sticky="ew")
                            
                            var.set(str(current_res))
                            
                            widget = slider_frame
                         elif section_key == "covers" and field == "external_resolution":
                            try:
                                current_res = int(var.get())
                                if current_res < 200 or current_res > 3000:
                                    current_res = 3000
                            except (ValueError, TypeError):
                                current_res = 3000
                            
                            current_res = round(current_res / 200) * 200
                            
                            slider_frame = customtkinter.CTkFrame(global_settings_frame, fg_color="transparent")
                            slider_frame.grid(row=row, column=1, sticky="ew", padx=(5, 5), pady=5)
                            slider_frame.grid_columnconfigure(0, weight=1)
                            
                            # Value label in column 2 (like Browse button position)
                            value_label = customtkinter.CTkLabel(global_settings_frame, text=f"{current_res}px", width=100, anchor="center")
                            value_label.grid(row=row, column=2, sticky="e", padx=(5, 5))
                            
                            def update_external_resolution_value(value, var_ref=var, label_ref=value_label):
                                int_value = round(value / 200) * 200
                                var_ref.set(str(int_value))
                                label_ref.configure(text=f"{int_value}px")
                            
                            slider = customtkinter.CTkSlider(slider_frame, from_=200, to=3000, number_of_steps=14, command=update_external_resolution_value)
                            slider.set(current_res)
                            slider.grid(row=0, column=0, sticky="ew")
                            
                            var.set(str(current_res))
                            
                            widget = slider_frame
                         elif section_key == "playlist" and field == "paths_m3u":
                            paths_options = ["absolute", "relative"]
                            if var.get() not in paths_options: var.set(paths_options[0])
                            
                            radio_frame = customtkinter.CTkFrame(global_settings_frame, fg_color="transparent")
                            radio_frame.grid(row=row, column=1, sticky="ew", padx=5, pady=5, columnspan=2)
                            
                            absolute_radio = customtkinter.CTkRadioButton(radio_frame, text="Absolute", variable=var, value="absolute")
                            absolute_radio.pack(side="left", padx=(0, 10))
                            
                            relative_radio = customtkinter.CTkRadioButton(radio_frame, text="Relative", variable=var, value="relative")
                            relative_radio.pack(side="left")
                            
                            widget = radio_frame
                         elif section_key == "advanced" and field == "cover_variance_threshold":
                            try:
                                current_threshold = int(var.get())
                                if current_threshold < 0 or current_threshold > 100:
                                    current_threshold = 0
                            except (ValueError, TypeError):
                                current_threshold = 0
                            
                            current_threshold = round(current_threshold / 2) * 2
                            
                            slider_frame = customtkinter.CTkFrame(global_settings_frame, fg_color="transparent")
                            slider_frame.grid(row=row, column=1, sticky="ew", padx=(5, 5), pady=5)
                            slider_frame.grid_columnconfigure(0, weight=1)
                            
                            # Value label in column 2 (like Browse button position)
                            value_label = customtkinter.CTkLabel(global_settings_frame, text=f"{current_threshold}%", width=100, anchor="center")
                            value_label.grid(row=row, column=2, sticky="e", padx=(5, 5))
                            
                            def update_threshold_value(value, var_ref=var, label_ref=value_label):
                                int_value = round(value / 2) * 2
                                var_ref.set(str(int_value))
                                label_ref.configure(text=f"{int_value}%")
                            
                            slider = customtkinter.CTkSlider(slider_frame, from_=0, to=100, number_of_steps=50, command=update_threshold_value)
                            slider.set(current_threshold)
                            slider.grid(row=0, column=0, sticky="ew")
                            
                            var.set(str(current_threshold))

                            widget = slider_frame
                         elif section_key == "advanced" and field == "ffmpeg_path":
                            ffmpeg_path_frame = customtkinter.CTkFrame(global_settings_frame, fg_color="transparent")
                            ffmpeg_path_frame.grid(row=row, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
                            ffmpeg_path_frame.grid_columnconfigure(0, weight=1)

                            widget = customtkinter.CTkEntry(ffmpeg_path_frame, textvariable=var)
                            widget.grid(row=0, column=0, sticky="ew", padx=(0, 5))
                            widget.bind("<Button-3>", show_context_menu)
                            widget.bind("<Button-2>", show_context_menu)
                            widget.bind("<Control-Button-1>", show_context_menu)
                            widget.bind("<FocusIn>", lambda e, w=widget: handle_focus_in(w))
                            widget.bind("<FocusOut>", lambda e, w=widget: handle_focus_out(w))

                            browse_btn = customtkinter.CTkButton(ffmpeg_path_frame, text="Browse", width=100, height=30,
                                                               command=lambda v=var: browse_ffmpeg_path(v),
                                                               fg_color=widget._fg_color, hover_color="#1F6AA5",
                                                               border_width=0, 
                                                               border_color=None)
                            browse_btn.grid(row=0, column=1, sticky="w", padx=(5, 0))
                         else:
                            widget = customtkinter.CTkEntry(global_settings_frame, textvariable=var)
                            widget.grid(row=row, column=1, sticky="ew", padx=(5, 5), pady=5)
                            widget.bind("<Button-3>", show_context_menu)
                            widget.bind("<Button-2>", show_context_menu)
                            widget.bind("<Control-Button-1>", show_context_menu)
                            widget.bind("<FocusIn>", lambda e, w=widget: handle_focus_in(w))
                            widget.bind("<FocusOut>", lambda e, w=widget: handle_focus_out(w))

                    tooltip_text = tooltip_texts.get(full_key)
                    if tooltip_text and widget:
                         CTkToolTip(widget, message=tooltip_text, bg_color=TOOLTIP_MENU_BG, text_color="#dddddd")

                    row += 1
        credential_keys_for_settings_tabs = [pk for pk in installed_platform_keys if pk != "Musixmatch"]        
        
        sorted_platform_keys_for_tabs = sorted(credential_keys_for_settings_tabs)
        for platform_key in sorted_platform_keys_for_tabs:
            platform_tab_frame = settings_tabview.add(platform_key)
            credential_tabs_config[platform_key] = {'frame': platform_tab_frame}
        settings_tabview.set("Global")
        # Bottom wrapper frame so Save section never shrinks/disappears regardless of content above
        settings_tabview.pack_forget()
        settings_tab.grid_columnconfigure(0, weight=1)
        settings_tab.grid_rowconfigure(0, weight=1)
        settings_tab.grid_rowconfigure(1, weight=0, minsize=40)
        settings_tabview.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 0))
        settings_bottom_frame = customtkinter.CTkFrame(settings_tab, fg_color="transparent")
        # Padding above Save: Global=5px, Deezer/Qobuz=0, other platform tabs=20px (see _handle_settings_tab_change)
        settings_bottom_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(5, 5))
        settings_bottom_frame.grid_columnconfigure(0, weight=1)
        globals()['settings_bottom_frame'] = settings_bottom_frame
        save_controls_frame = customtkinter.CTkFrame(settings_bottom_frame, fg_color="transparent")
        save_controls_frame.pack(side="bottom", anchor="se", padx=(8, 5), pady=(0, 5))
        save_status_var = tkinter.StringVar()
        save_status_label = customtkinter.CTkLabel(save_controls_frame, textvariable=save_status_var, text_color=("#00C851", "#00C851"))
        globals()['save_status_label'] = save_status_label
        save_status_label.pack(side="left", padx=(0, 10))
        save_button = customtkinter.CTkButton(save_controls_frame, text="Save", width=100, height=30, command=handle_save_settings, fg_color=BUTTON_COLOR, hover_color="#1F6AA5")
        save_button.pack(side="left", padx=5, pady=(0, 0))
        about_tab = tabview.add("About")
        about_container = customtkinter.CTkFrame(about_tab, fg_color="transparent")
        about_container.pack(fill="both", expand=True, padx=16, pady=(0, 0))
        canvas = customtkinter.CTkFrame(about_container, fg_color="transparent")
        canvas.pack(fill="both", expand=True)
        canvas.grid_columnconfigure(0, weight=1)
        canvas.grid_rowconfigure(0, weight=1)
        canvas.grid_rowconfigure(1, weight=0)
        about_mid = customtkinter.CTkFrame(canvas, fg_color="transparent")
        about_mid.grid(row=0, column=0, sticky="nsew")
        about_mid.grid_columnconfigure(0, weight=1)
        about_mid.grid_rowconfigure(0, weight=1)
        mid_inner = customtkinter.CTkFrame(about_mid, fg_color="transparent")
        icon_title_frame = customtkinter.CTkFrame(mid_inner, fg_color="transparent")
        icon_title_frame.pack(pady=(0, 5))
        try:
            current_platform = platform.system()
            if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                print(f"[DEBUG AboutIcon] Platform detected: {current_platform}")
            if current_platform == "Linux":
                icon_filename = "icon.png"
                icon_display_size = (48, 48)
                if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                    print(f"[DEBUG AboutIcon] Set Linux display size to {icon_display_size}")
            elif current_platform == "Darwin":
                icon_filename = "icon.icns"
                icon_display_size = (72, 72)
                if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                    print(f"[DEBUG AboutIcon] Set macOS display size to {icon_display_size}")
            else:
                # Prefer icon.png for the About image on Windows if available, as PIL handles PNG better than some ICOs
                if os.path.exists(resource_path("icon.png")):
                    icon_filename = "icon.png"
                else:
                    icon_filename = "icon.ico"
                icon_display_size = (48, 48)
                if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                    print(f"[DEBUG AboutIcon] Set default display size to {icon_display_size}")
            if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                print(f"[DEBUG AboutIcon] Determined icon filename: {icon_filename}")
            icon_path = resource_path(icon_filename)
            if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                print(f"[DEBUG AboutIcon] Generated icon path: {icon_path}")
                print(f"[DEBUG AboutIcon] Looking for AboutTab icon at: {icon_path}")

            icon_exists = os.path.exists(icon_path)
            if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                print(f"[DEBUG AboutIcon] Does icon exist at path? {icon_exists}")

            if icon_path and icon_exists:

                try:
                    if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                        print("[DEBUG AboutIcon] Attempting to open image...")
                    img = Image.open(icon_path).resize(icon_display_size, Image.LANCZOS)
                    if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                        print("[DEBUG AboutIcon] Image opened successfully.")
                    icon_image = customtkinter.CTkImage(light_image=img, dark_image=img, size=icon_display_size)
                    if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                        print("[DEBUG AboutIcon] CTkImage created successfully.")
                    icon_label = customtkinter.CTkLabel(icon_title_frame, text="", image=icon_image)
                    icon_pady = 0 if current_platform == "Darwin" else 5
                    icon_label.pack(pady=icon_pady)
                except Exception as img_e:
                    if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                        print(f"[DEBUG AboutIcon] Could not load/process icon image: {type(img_e).__name__}: {img_e}")
            else:
                if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                    print(f"[DEBUG AboutIcon] Icon file not found or path invalid: {icon_path}")
        except Exception as path_e:
            if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                print(f"[DEBUG AboutIcon] Error during icon path processing/loading: {type(path_e).__name__}: {path_e}")
        title_label = customtkinter.CTkLabel(icon_title_frame, text="OrpheusDL GUI", font=customtkinter.CTkFont(weight="bold"))
        title_label.pack(pady=(0, 0))
        description_text = ("Makes downloading music with OrpheusDL easy on Win, macOS & Linux.\nSearch multiple platforms & download high-quality audio with metadata.")
        description_label = customtkinter.CTkLabel(mid_inner, text=description_text, justify="center", wraplength=450)
        description_label.pack(pady=(0, 10))
        github_url = "https://github.com/bascurtiz/OrpheusDL-GUI"
        command = lambda u=github_url: os.startfile(u) if platform.system() == "Windows" else subprocess.Popen(["open", u]) if platform.system() == "Darwin" else subprocess.Popen(["xdg-open", u])
        github_button = customtkinter.CTkButton(mid_inner, text="GitHub", command=command, width=100, height=30, fg_color="#343638", hover_color=LINK_COLOR)
        github_button.pack(pady=10)
        section_header_font = ("Segoe UI", 11)
        section_header_color = SECONDARY_TEXT_COLOR
        version_heading_label = customtkinter.CTkLabel(mid_inner, text="GUI VERSION", font=section_header_font, text_color=section_header_color)
        version_heading_label.pack(pady=(10, 0))
        version_number_label = customtkinter.CTkLabel(mid_inner, text=__version__)
        version_number_label.pack(pady=(0, 10))
        credits_heading_label = customtkinter.CTkLabel(mid_inner, text="CREDITS", font=section_header_font, text_color=section_header_color)
        credits_heading_label.pack(pady=(0, 2))
        credits_names_text = ("""OrfiDev (Project Lead)\nDniel97 (Current Lead Developer)\nCommunity developers (Modules)\nBas Curtiz (GUI)""")
        credits_names_label = customtkinter.CTkLabel(mid_inner, text=credits_names_text.strip(), justify="center")
        credits_names_label.pack(pady=(0, 0))
        mid_inner.place(relx=0.5, rely=0.5, anchor="center")
        about_bottom = customtkinter.CTkFrame(canvas, fg_color="transparent")
        about_bottom.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        about_bottom.grid_columnconfigure(0, weight=1)
        modules_title = customtkinter.CTkLabel(about_bottom, text="MODULES", font=section_header_font, text_color=section_header_color)
        modules_title.pack(pady=(0, 5), anchor="center")
        modules_center_wrapper = customtkinter.CTkFrame(about_bottom, fg_color="transparent")
        modules_center_wrapper.pack(fill="x", pady=(0, 10))
        modules_frame = customtkinter.CTkFrame(modules_center_wrapper, fg_color="transparent")
        modules_frame.pack(anchor="center", padx=20)
        module_buttons_data = [
            ("Apple Music", "https://github.com/bascurtiz/orpheusdl-applemusic"),
            ("Beatport", "https://github.com/bascurtiz/orpheusdl-beatport"),
            ("Beatsource", "https://github.com/bascurtiz/orpheusdl-beatsource"),
            ("Bugs", "https://github.com/Dniel97/orpheusdl-bugsmusic"),
            ("Deezer", "https://github.com/bascurtiz/OrpheusDL-deezer"),            
            ("Genius", "https://github.com/Dniel97/orpheusdl-genius"),
            ("Idagio", "https://github.com/Dniel97/orpheusdl-idagio"),
            ("KKBOX", "https://github.com/uhwot/orpheusdl-kkbox"),
            ("Musixmatch", "https://github.com/yarrm80s/orpheusdl-musixmatch"),
            ("Napster", "https://github.com/yarrm80s/orpheusdl-napster"),
            ("Nugs.net", "https://github.com/Dniel97/orpheusdl-nugs"),
            ("Qobuz", "https://github.com/bascurtiz/orpheusdl-qobuz"),            
            ("SoundCloud", "https://github.com/bascurtiz/orpheusdl-soundcloud"),
            ("Spotify", "https://github.com/bascurtiz/orpheusdl-spotify"),
            ("Tidal", "https://github.com/bascurtiz/orpheusdl-tidal"),
            ("YouTube", "https://github.com/bascurtiz/orpheusdl-youtube")
        ]
        module_buttons_data.sort(key=lambda item: item[0])
        cols = 8
        rows = (len(module_buttons_data) + cols - 1) // cols if module_buttons_data else 0
        button_width = 100
        button_height = 30
        button_padx = 2
        button_pady = 2
        for index, (name, url) in enumerate(module_buttons_data):
            row = index // cols
            col = index % cols
            command = lambda u=url: (subprocess.Popen(["open", u]) if platform.system() == "Darwin" else subprocess.Popen(["xdg-open", u]) if platform.system() == "Linux" else os.startfile(u))
            button = customtkinter.CTkButton(
                modules_frame,
                text=name,
                command=command,
                width=button_width,
                height=button_height,
                fg_color="#343638",
                hover_color=LINK_COLOR
            )
            button.grid(row=row, column=col, padx=button_padx, pady=button_pady, sticky="nw")

        
        # Check for FFmpeg on macOS/Linux and show helpful message if missing
        if platform.system() in ('Darwin', 'Linux'):
            ffmpeg_found, ffmpeg_path = find_system_ffmpeg()
            if not ffmpeg_found:
                def _show_ffmpeg_install_message():
                    # Check if user chose to hide this message
                    if current_settings.get("globals", {}).get("advanced", {}).get("hide_ffmpeg_warning", False):
                        return
                    
                    dialog = customtkinter.CTkToplevel(app)
                    dialog.title("FFmpeg Not Found")
                    dialog.resizable(False, False)
                    dialog.attributes("-topmost", True)
                    dialog.transient(app)
                    
                    # Helper to copy command with feedback
                    def copy_command(cmd, button):
                        try:
                            if not _copy_to_system_clipboard(cmd):
                                app.clipboard_clear()
                                app.clipboard_append(cmd)
                                app.update()
                            original_text = button.cget("text")
                            button.configure(text="✓")
                            button.after(1500, lambda: button.configure(text=original_text))
                        except Exception as e:
                            print(f"Error copying to clipboard: {e}")
                    
                    # Main frame
                    main_frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
                    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
                    
                    # Warning icon and title
                    title_label = customtkinter.CTkLabel(
                        main_frame, 
                        text="⚠️  FFmpeg Not Found",
                        font=("", 18, "bold")
                    )
                    title_label.pack(pady=(0, 10))
                    
                    # Description
                    desc_label = customtkinter.CTkLabel(
                        main_frame,
                        text="FFmpeg is required for audio conversion (e.g., FLAC to MP3/ALAC).\nDownloads will work, but conversion will be skipped.",
                        justify="center"
                    )
                    desc_label.pack(pady=(0, 15))
                    
                    if platform.system() == 'Darwin':
                        # macOS instructions
                        dialog.geometry("620x600")
                        
                        # Step 1: Homebrew
                        step1_frame = customtkinter.CTkFrame(main_frame, fg_color="#2B2B2B", corner_radius=8)
                        step1_frame.pack(fill="x", pady=5)
                        
                        step1_label = customtkinter.CTkLabel(step1_frame, text="1. Install Homebrew (if not installed):", anchor="w")
                        step1_label.pack(fill="x", padx=10, pady=(8, 2))
                        
                        homebrew_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
                        cmd1_frame = customtkinter.CTkFrame(step1_frame, fg_color="#1E1E1E", corner_radius=5)
                        cmd1_frame.pack(fill="x", padx=10, pady=(2, 8))
                        
                        cmd1_label = customtkinter.CTkLabel(cmd1_frame, text=homebrew_cmd, font=("Segoe UI", 10), anchor="w", text_color="#98C379")
                        cmd1_label.pack(side="left", fill="x", expand=True, padx=10, pady=8)
                        
                        copy1_btn = customtkinter.CTkButton(
                            cmd1_frame, text="⧉", width=24, height=24, 
                            font=("Segoe UI", 14),
                            fg_color="#2B2B2B", hover_color="#3B3B3B", 
                            text_color="#999999", corner_radius=3,
                            command=lambda: copy_command(homebrew_cmd, copy1_btn)
                        )
                        copy1_btn.pack(side="right", padx=8, pady=5)
                        copy1_btn.bind("<Enter>", lambda e: copy1_btn.configure(text_color="#FFFFFF"))
                        copy1_btn.bind("<Leave>", lambda e: copy1_btn.configure(text_color="#999999"))
                        
                        # Step 2: FFmpeg
                        step2_frame = customtkinter.CTkFrame(main_frame, fg_color="#2B2B2B", corner_radius=8)
                        step2_frame.pack(fill="x", pady=5)
                        
                        step2_label = customtkinter.CTkLabel(step2_frame, text="2. Install FFmpeg:", anchor="w")
                        step2_label.pack(fill="x", padx=10, pady=(8, 2))
                        
                        ffmpeg_cmd = 'brew install ffmpeg'
                        cmd2_frame = customtkinter.CTkFrame(step2_frame, fg_color="#1E1E1E", corner_radius=5)
                        cmd2_frame.pack(fill="x", padx=10, pady=(2, 8))
                        
                        cmd2_label = customtkinter.CTkLabel(cmd2_frame, text=ffmpeg_cmd, font=("Segoe UI", 11), anchor="w", text_color="#98C379")
                        cmd2_label.pack(side="left", fill="x", expand=True, padx=10, pady=8)
                        
                        copy2_btn = customtkinter.CTkButton(
                            cmd2_frame, text="⧉", width=24, height=24,
                            font=("Segoe UI", 14),
                            fg_color="#2B2B2B", hover_color="#3B3B3B",
                            text_color="#999999", corner_radius=3,
                            command=lambda: copy_command(ffmpeg_cmd, copy2_btn)
                        )
                        copy2_btn.pack(side="right", padx=8, pady=5)
                        copy2_btn.bind("<Enter>", lambda e: copy2_btn.configure(text_color="#FFFFFF"))
                        copy2_btn.bind("<Leave>", lambda e: copy2_btn.configure(text_color="#999999"))
                        
                        step3_label = customtkinter.CTkLabel(main_frame, text="3. Restart OrpheusDL GUI", anchor="w")
                        step3_label.pack(fill="x", pady=(10, 5), padx=10)

                        # Option 4: Manual Install (Alternative)
                        step4_frame = customtkinter.CTkFrame(main_frame, fg_color="#2B2B2B", corner_radius=8)
                        step4_frame.pack(fill="x", pady=5)

                        step4_label = customtkinter.CTkLabel(step4_frame, text="Alternative: Manual Install", anchor="w", font=("", 12, "bold"))
                        step4_label.pack(fill="x", padx=10, pady=(8, 2))

                        def open_ffmpeg_site():
                            webbrowser.open("https://evermeet.cx/ffmpeg/")

                        download_btn = customtkinter.CTkButton(
                            step4_frame, text="Download FFmpeg (evermeet.cx)", 
                            command=open_ffmpeg_site,
                            height=24,
                            fg_color="transparent", 
                            text_color="#3B8ED0",
                            hover_color="#2B2B2B",
                            anchor="w"
                        )
                        download_btn.pack(padx=10, pady=(0, 0), anchor="w")
                        
                        # Add underline effect on hover
                        def on_enter(e):
                            download_btn.configure(text_color="#1F6AA5")
                        def on_leave(e):
                            download_btn.configure(text_color="#3B8ED0")
                        download_btn.bind("<Enter>", on_enter)
                        download_btn.bind("<Leave>", on_leave)

                        def open_app_folder(event=None):
                            # Use get_data_directory() to get the correct writable path (Application Support on macOS)
                            app_dir = get_data_directory()
                            if not app_dir:
                                app_dir = get_script_directory()
                                
                            if platform.system() == "Windows":
                                os.startfile(app_dir)
                            elif platform.system() == "Darwin":
                                subprocess.Popen(["open", app_dir])
                            else:
                                subprocess.Popen(["xdg-open", app_dir])

                        # Container for the text - Horizontal flow
                        instr_container = customtkinter.CTkFrame(step4_frame, fg_color="transparent")
                        instr_container.pack(fill="x", padx=(15, 10), pady=(0, 0))

                        # Part 1: Text before link
                        part1 = customtkinter.CTkLabel(
                            instr_container, 
                            text="Download, unzip, and place the 'ffmpeg' file in the ", 
                            text_color="#999999", font=("", 11),
                            anchor="w"
                        )
                        part1.pack(side="left", padx=0)

                        # Part 2: Link (Label instead of Button for better spacing)
                        # Use CTkFont for proper underlining
                        link_font = customtkinter.CTkFont(size=11, underline=True)
                        
                        part2_link = customtkinter.CTkLabel(
                            instr_container,
                            text="same folder",
                            text_color="#3B8ED0",
                            font=link_font,
                            cursor="pointinghand"
                        )
                        part2_link.pack(side="left", padx=0)
                        part2_link.bind("<Button-1>", open_app_folder)

                        # Part 3: Text after link
                        part3 = customtkinter.CTkLabel(
                            instr_container,
                            text=" as this app.",
                            text_color="#999999", font=("", 11),
                            anchor="w"
                        )
                        part3.pack(side="left", padx=0)
                        
                        # Hover effects for link
                        def on_enter_link(e): 
                            part2_link.configure(text_color="#1F6AA5", cursor="pointinghand")
                        def on_leave_link(e): 
                            part2_link.configure(text_color="#3B8ED0", cursor="arrow")
                        part2_link.bind("<Enter>", on_enter_link)
                        part2_link.bind("<Leave>", on_leave_link)

                        # Part 4: Path on new line
                        target_dir = get_data_directory()
                        if not target_dir: target_dir = get_script_directory()
                        
                        part4 = customtkinter.CTkLabel(
                            step4_frame,
                            text=f"Default: {target_dir}",
                            text_color="#888888", font=("", 10),
                            anchor="w"
                        )
                        part4.pack(fill="x", padx=(15, 10), pady=(0, 8))
                        
                    else:  # Linux
                        dialog.geometry("520x500")
                        
                        # Linux instructions with multiple options
                        info_label = customtkinter.CTkLabel(main_frame, text="Install FFmpeg using your package manager:", anchor="w")
                        info_label.pack(fill="x", pady=(0, 10))
                        
                        linux_commands = [
                            ("Ubuntu / Debian:", "sudo apt install ffmpeg"),
                            ("Fedora:", "sudo dnf install ffmpeg"),
                            ("Arch Linux:", "sudo pacman -S ffmpeg"),
                        ]
                        
                        for distro, cmd in linux_commands:
                            cmd_frame = customtkinter.CTkFrame(main_frame, fg_color="#2B2B2B", corner_radius=8)
                            cmd_frame.pack(fill="x", pady=3)
                            
                            distro_label = customtkinter.CTkLabel(cmd_frame, text=distro, anchor="w", width=120)
                            distro_label.pack(side="left", padx=10, pady=8)
                            
                            inner_frame = customtkinter.CTkFrame(cmd_frame, fg_color="#1E1E1E", corner_radius=5)
                            inner_frame.pack(side="left", fill="x", expand=True, padx=(0, 5), pady=5)
                            
                            cmd_label = customtkinter.CTkLabel(inner_frame, text=cmd, font=("Segoe UI", 11), anchor="w", text_color="#98C379")
                            cmd_label.pack(side="left", fill="x", expand=True, padx=10, pady=6)
                            
                            # Create button first, then configure command to capture correct reference
                            copy_btn = customtkinter.CTkButton(
                                cmd_frame, text="⧉", width=24, height=24,
                                font=("Segoe UI", 14),
                                fg_color="#2B2B2B", hover_color="#3B3B3B",
                                text_color="#999999", corner_radius=3
                            )
                            copy_btn.configure(command=lambda c=cmd, b=copy_btn: copy_command(c, b))
                            copy_btn.pack(side="right", padx=8, pady=5)
                            copy_btn.bind("<Enter>", lambda e, b=copy_btn: b.configure(text_color="#FFFFFF"))
                            copy_btn.bind("<Leave>", lambda e, b=copy_btn: b.configure(text_color="#999999"))
                        
                        restart_label = customtkinter.CTkLabel(main_frame, text="Then restart OrpheusDL GUI", anchor="w")
                        restart_label.pack(fill="x", pady=(15, 5))
                    
                    # "Don't show again" checkbox
                    dont_show_var = customtkinter.BooleanVar(value=False)
                    
                    def on_close():
                        if dont_show_var.get():
                            # Save preference to settings
                            if "globals" not in current_settings:
                                current_settings["globals"] = {}
                            if "advanced" not in current_settings["globals"]:
                                current_settings["globals"]["advanced"] = {}
                            current_settings["globals"]["advanced"]["hide_ffmpeg_warning"] = True
                            
                            # Also update settings_vars so save_settings() picks it up
                            if "globals" not in settings_vars:
                                settings_vars["globals"] = {}
                            
                            # Create a BooleanVar for the setting if it doesn't exist
                            # This ensures save_settings() sees the change
                            settings_vars["globals"]["advanced.hide_ffmpeg_warning"] = tkinter.BooleanVar(value=True)
                            
                            save_settings(show_confirmation=False)
                        dialog.destroy()
                    
                    checkbox_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
                    checkbox_frame.pack(fill="x", pady=(15, 5))
                    
                    dont_show_checkbox = customtkinter.CTkCheckBox(
                        checkbox_frame,
                        text="Don't show this message again",
                        variable=dont_show_var,
                        font=("", 12),
                        checkbox_height=18,
                        checkbox_width=18
                    )
                    dont_show_checkbox.pack(anchor="center")
                    
                    # OK button
                    ok_btn = customtkinter.CTkButton(main_frame, text="OK", command=on_close, width=100)
                    ok_btn.pack(pady=(10, 0))
                    
                    # Center on parent
                    dialog.update_idletasks()
                    parent_x = app.winfo_x()
                    parent_y = app.winfo_y()
                    parent_width = app.winfo_width()
                    parent_height = app.winfo_height()
                    dialog_width = dialog.winfo_width()
                    dialog_height = dialog.winfo_height()
                    center_x = parent_x + (parent_width // 2) - (dialog_width // 2)
                    center_y = parent_y + (parent_height // 2) - (dialog_height // 2)
                    dialog.geometry(f"+{center_x}+{center_y}")
                    
                    dialog.grab_set()
                    
                app.after(1000, _show_ffmpeg_install_message)
        
        setup_logging(output_queue)
        update_log_area()
        try:
            run_check_in_thread(__version__, app)
        except Exception as update_err:
            print(f"[Error] Failed to start update check: {update_err}")

        def _initial_ui_update():
            if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                print("[DEBUG] Running _initial_ui_update...")
            try:
                if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                    print("  -> Calling _update_settings_tab_widgets()")
                _update_settings_tab_widgets()
                if 'update_search_platform_dropdown' in globals() and callable(update_search_platform_dropdown):
                    update_search_platform_dropdown()
                if current_settings.get("globals", {}).get("advanced", {}).get("debug_mode", False):
                    print("[DEBUG] _initial_ui_update finished.")
            except Exception as e_init_update:
                 print(f"[Error] in _initial_ui_update: {e_init_update}")

        _initial_ui_update()
        app.protocol("WM_DELETE_WINDOW", _on_gui_exit)
        _setup_macos_window_management()
        
        
        app.attributes('-alpha', 1)
        app.deiconify() # Ensure it's not minimized
        try:
            app.state("normal")
        except:
            pass
        app.lift()
        
        # Start background initialization
        def run_async_init():
            global _settings_just_created
            print("[Async Init] Starting background initialization...")
            init_success = initialize_orpheus()
            
            if not init_success and _settings_just_created:
                print("[First Run] Initial Orpheus setup may have updated settings. Retrying initialization...")
                time.sleep(0.5)
                load_settings()
                init_success = initialize_orpheus()
            
            if init_success:
                def enable_buttons():
                    print("[Async Init] Enabling buttons...")
                    if 'download_button' in globals() and download_button and download_button.winfo_exists():
                        download_button.configure(state="normal")
                    if 'search_button' in globals() and search_button and search_button.winfo_exists():
                        search_button.configure(state="normal")
                
                if app and app.winfo_exists():
                    app.after(0, enable_buttons)
            else:
                def show_init_error():
                    print("Disabling Download/Search buttons due to Orpheus initialization failure.")
                    # Define and show the dialog
                    dialog = customtkinter.CTkToplevel(app)
                    dialog.title("Initialization Error")
                    dialog.geometry("500x220")
                    dialog.resizable(False, False)
                    dialog.attributes("-topmost", True)
                    dialog.transient(app)
                    dialog.update_idletasks()
                    
                    # Center on parent
                    parent_width = app.winfo_width()
                    parent_height = app.winfo_height()
                    parent_x = app.winfo_x()
                    parent_y = app.winfo_y()
                    dialog_width = 500
                    dialog_height = 220
                    center_x = parent_x + (parent_width // 2) - (dialog_width // 2)
                    center_y = parent_y + (parent_height // 2) - (dialog_height // 2)
                    dialog.geometry(f"{dialog_width}x{dialog_height}+{center_x}+{center_y}")
                    
                    message = (
                        "The Orpheus download engine failed to initialize.\n\n"
                        "This usually happens when:\n"
                        "• No download modules are installed in the 'modules' folder\n"
                        "• The settings.json file is corrupted\n"
                        "• Required dependencies are missing\n\n"
                        "Download and Search features are disabled."
                    )
                    
                    message_label = customtkinter.CTkLabel(dialog, text=message, wraplength=460, justify="left")
                    message_label.pack(pady=(20, 15), padx=20)
                    
                    button_frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
                    button_frame.pack(fill="x", padx=20, pady=(0, 20))
                    
                    def view_logs():
                        dialog.destroy()
                        show_log_viewer("Initialization Logs", parent=app)
                    
                    view_logs_btn = customtkinter.CTkButton(button_frame, text="View Logs", command=view_logs, width=120, fg_color="#2D5A88", hover_color="#1F6AA5")
                    view_logs_btn.pack(side="left", padx=5)
                    
                    ok_btn = customtkinter.CTkButton(button_frame, text="OK", command=dialog.destroy, width=100)
                    ok_btn.pack(side="right", padx=5)
                    
                    dialog.grab_set()

                if app and app.winfo_exists():
                    app.after(0, show_init_error)

        threading.Thread(target=run_async_init, daemon=True).start()
        
        app.mainloop()
    else:
        print(f"[Child Process {os.getpid()}] Detected, exiting.")
        os._exit(0)