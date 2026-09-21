#!/usr/bin/env python3
"""
stamp_video_dates.py
Losslessly stamps MP4 container metadata (creation_time) and filesystem
timestamps (mtime, btime via touch & SetFile on macOS).
Useful for correcting DVD burn-date artifacts where legacy authoring software
overwrote original capture dates with compilation burn dates.
"""

import argparse
import os
import platform
import subprocess
import sys
from datetime import datetime

def stamp_single_file(filepath, dt):
    if not os.path.exists(filepath):
        print(f"[-] File not found: {filepath}")
        return False

    iso_date = dt.strftime("%Y-%m-%d %H:%M:%S")
    touch_date = dt.strftime("%Y%m%d%H%M.%S")
    tmp_path = filepath + ".tmp.mp4"

    print(f"[+] Stamping: {filepath} -> {iso_date}")

    # Lossless remux to embed QuickTime creation_time atom
    cmd_ffmpeg = [
        "ffmpeg", "-y", "-v", "error",
        "-i", filepath,
        "-c", "copy",
        "-metadata", f"creation_time={iso_date}",
        "-movflags", "+faststart",
        tmp_path
    ]
    res = subprocess.run(cmd_ffmpeg)
    if res.returncode != 0 or not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
        print(f"[-] ffmpeg remux failed for {filepath}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False

    os.replace(tmp_path, filepath)

    # Filesystem timestamps
    subprocess.run(["touch", "-t", touch_date, filepath], check=True)

    if platform.system() == 'Darwin' and os.path.exists('/usr/bin/SetFile'):
        setfile_date = dt.strftime("%m/%d/%Y %H:%M:%S")
        subprocess.run(["/usr/bin/SetFile", "-d", setfile_date, "-m", setfile_date, filepath], check=True)

    print(f"[✓] Successfully sealed: {filepath}")
    return True

def parse_date_string(d_str):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(d_str, fmt)
        except ValueError:
            pass
    raise ValueError(f"Unable to parse date string: {d_str}")

def main():
    parser = argparse.ArgumentParser(description="Stamp container metadata and filesystem timestamps on video files.")
    parser.add_argument('file', help="Target MP4 video file.")
    parser.add_argument('date', help="Capture date (YYYY-MM-DD or DD.MM.YYYY).")
    args = parser.parse_args()

    try:
        dt = parse_date_string(args.date)
        stamp_single_file(args.file, dt)
    except Exception as e:
        print(f"[-] Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
