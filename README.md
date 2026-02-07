# OrpheusDL GUI

## Trailer
[![Watch trailer](https://i.imgur.com/UENa7ln.png)](https://youtu.be/RAXsW67SjGU)

## How to install:

1. Download the compiled installer from the [Releases page](https://github.com/bascurtiz/OrpheusDL-GUI/releases).
2. Double-click the exe/app
   - Windows - Demo how to install: https://youtu.be/rMeBUanEK9Q (1m4s)
   - macOS - Demo how to install: https://youtu.be/j39ryXFAxzw (1m54s)
   - macOS - For older macOS / if Homebrew isn't supported: https://youtu.be/7pE6xgm1fsg (1m30s)
   - Linux - Demo to install: https://youtu.be/51eESmveCME (1m8s)

### If you prefer running from source:
1. Clone this repository (`git clone https://github.com/bascurtiz/OrpheusDL-GUI`) or download the ZIP file.
2. Ensure all files from this repository are placed in the same folder where your `orpheus.py` is located.
3. Update your package list: `sudo apt update`
4. Install the Python virtual environment package: `sudo apt install python3-venv`
5. Create a virtual environment: `python3 -m venv venv`
6. Activate the virtual environment: `source venv/bin/activate`
7. Install the required dependencies: `pip3 install -r requirements-gui.txt`
8. Run the GUI: `python3 gui.py`<br>
<br>
<img src="https://i.imgur.com/WP7yUMr.gif" alt="GUI overview">

## Compatibility

### Operating Systems

| OS            | Tested |
|---------------|--------|
| Windows 10    | ✅     |
| Windows 11    | ✅     |
| macOS 11.4+   | ✅     |
| Linux Ubuntu 24 | ✅     |

### Platforms

| Platform     | Tested | Platform     | Tested | Platform     | Tested | Platform     | Tested |
|--------------|--------|--------------|--------|--------------|--------|--------------|--------|
| Apple Music  | ✅     | Beatport     | ✅     | Beatsource   | ✅     | Bugs         | \*     |
| Deezer       | ✅     | Genius       | \*     | Idagio       | \*     | ~~JioSaavn~~ | ❌     |
| KKBOX        | \*     | Musixmatch   | \*     | Napster      | \*     | Nugs.net     | \*     |
| Qobuz        | ✅     | SoundCloud   | ✅     | Spotify      | ✅     | Tidal        | ✅     |
| YouTube      | ✅     |              |        |              |        |              |        |

\* *If this platform isn't working properly and you have a valid subscription you can share, please open an issue or contact me. I'm willing to debug!* 
