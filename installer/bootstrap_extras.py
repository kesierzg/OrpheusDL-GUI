#!/usr/bin/env python3
"""Shared installer helpers: stale package cleanup and Shaka Packager download."""

from __future__ import annotations

import argparse
import platform
import shutil
import site
import stat
import sys
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SHAKA_PACKAGER_ASSETS = {
    "Windows": ("packager-win-x64.exe", "packager-win-x64.exe"),
    "Darwin": ("packager-osx-x64", "packager-osx-x64"),
    "Linux": ("packager-linux-x64", "packager-linux-x64"),
}


def cleanup_stale_unplayplay_metadata() -> bool:
    """Remove broken unplayplay 0.0.8 dist-info that triggers repeated pip warnings."""
    removed: list[str] = []
    search_roots: list[Path] = []

    try:
        search_roots.extend(Path(p) for p in site.getsitepackages())
    except AttributeError:
        pass

    if site.ENABLE_USER_SITE:
        try:
            search_roots.append(Path(site.getusersitepackages()))
        except AttributeError:
            pass

    for root in search_roots:
        if not root.is_dir():
            continue
        for entry in root.iterdir():
            if entry.name.startswith("unplayplay-0.0.8"):
                shutil.rmtree(entry, ignore_errors=True)
                removed.append(str(entry))

    if removed:
        print(f"[cleanup] Removed stale unplayplay metadata: {', '.join(removed)}")
    else:
        print("[cleanup] No stale unplayplay 0.0.8 metadata found")
    return bool(removed)


def ensure_shaka_packager(project_root: Path | None = None) -> bool:
    """Download Shaka Packager for the current OS if missing from project root."""
    root = project_root or PROJECT_ROOT
    asset = SHAKA_PACKAGER_ASSETS.get(platform.system())
    if not asset:
        print("[Shaka] Unknown platform; skipping Shaka Packager download")
        return False

    filename, url_name = asset
    dest = root / filename
    if dest.is_file() and dest.stat().st_size > 0:
        print(f"[Shaka] Found {filename}")
        return True

    url = f"https://github.com/shaka-project/shaka-packager/releases/latest/download/{url_name}"
    print(f"[Shaka] Downloading {filename} from GitHub releases...")
    try:
        urllib.request.urlretrieve(url, dest)
        if platform.system() != "Windows":
            dest.chmod(dest.stat().st_mode | stat.S_IEXEC)
        print(f"[Shaka] Saved to {dest}")
        return True
    except Exception as exc:
        print(f"[Shaka] WARNING: Could not download Shaka Packager: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="OrpheusDL installer bootstrap helpers")
    parser.add_argument(
        "--cleanup-unplayplay",
        action="store_true",
        help="Remove broken unplayplay 0.0.8 dist-info folders",
    )
    parser.add_argument(
        "--shaka",
        action="store_true",
        help="Download Shaka Packager binary for the current platform",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Project root directory (default: parent of installer/)",
    )
    args = parser.parse_args()

    if not args.cleanup_unplayplay and not args.shaka:
        parser.error("Specify at least one of --cleanup-unplayplay or --shaka")

    ok = True
    if args.cleanup_unplayplay:
        cleanup_stale_unplayplay_metadata()

    if args.shaka:
        ok = ensure_shaka_packager(args.project_root) and ok

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
