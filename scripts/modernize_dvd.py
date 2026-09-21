#!/usr/bin/env python3
"""
modernize_dvd.py
Specialized DVD-Video (VIDEO_TS) processor and modernizer.
Concatenates split VOB titles (e.g. VTS_01_1.VOB, VTS_01_2.VOB), deinterlaces
with bwdif, fixes non-square pixel display aspect ratios, and outputs clean H.265 MP4.
"""

import argparse
import glob
import os
import platform
import shutil
import subprocess
import sys

def detect_encoder():
    if platform.system() == 'Darwin':
        cmd = ['ffmpeg', '-v', 'quiet', '-encoders']
        res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        if 'hevc_videotoolbox' in res.stdout:
            return 'hevc_videotoolbox'
    return 'libx265'

def process_dvd_vts(video_ts_dir, output_dir, prefix="Title"):
    os.makedirs(output_dir, exist_ok=True)
    encoder = detect_encoder()

    # Find unique title sets (VTS_01, VTS_02, etc.)
    all_vobs = glob.glob(os.path.join(video_ts_dir, "VTS_[0-9][0-9]_[1-9].VOB")) + \
               glob.glob(os.path.join(video_ts_dir, "vts_[0-9][0-9]_[1-9].vob"))
    
    title_sets = sorted(list(set(os.path.basename(v)[:6].upper() for v in all_vobs)))
    if not title_sets:
        print(f"[-] No standard VTS_XX_X.VOB titles found in {video_ts_dir}")
        return

    print(f"[*] Discovered {len(title_sets)} Title Set(s): {', '.join(title_sets)}")

    for idx, vts in enumerate(title_sets, 1):
        vob_parts = sorted(glob.glob(os.path.join(video_ts_dir, f"{vts}_[1-9].*")) + \
                           glob.glob(os.path.join(video_ts_dir, f"{vts.lower()}_[1-9].*")))
        if not vob_parts:
            continue

        out_name = f"{prefix}_{idx:02d}.mp4"
        out_file = os.path.join(output_dir, out_name)

        if os.path.exists(out_file):
            print(f"[*] Skipping existing: {out_file}")
            continue

        print(f"[+] Concatenating and modernizing {vts} ({len(vob_parts)} parts) -> {out_name}")

        concat_input = "concat:" + "|".join(vob_parts)
        vf_filters = "bwdif=mode=send_frame:parity=auto:deint=all,scale=768:576,setsar=1"

        cmd = [
            'ffmpeg', '-y', '-v', 'error', '-stats',
            '-i', concat_input,
            '-vf', vf_filters,
        ]

        if encoder == 'hevc_videotoolbox':
            cmd.extend(['-c:v', 'hevc_videotoolbox', '-q:v', '65', '-tag:v', 'hvc1'])
        else:
            cmd.extend(['-c:v', 'libx265', '-crf', '22', '-preset', 'medium', '-tag:v', 'hvc1'])

        cmd.extend([
            '-c:a', 'aac', '-b:a', '192k',
            '-movflags', '+faststart',
            out_file
        ])

        res = subprocess.run(cmd)
        if res.returncode == 0:
            # Stamp timestamp from the first VOB part
            shutil.copystat(vob_parts[0], out_file)
            print(f"[✓] Completed: {out_file}")
        else:
            print(f"[-] Failed to modernize {vts}")
            if os.path.exists(out_file):
                os.remove(out_file)

def main():
    parser = argparse.ArgumentParser(description="Extract and modernize DVD VIDEO_TS titles into H.265 MP4.")
    parser.add_argument('--input', '-i', required=True, help="Path to VIDEO_TS directory.")
    parser.add_argument('--output', '-o', required=True, help="Output directory for modern MP4 files.")
    parser.add_argument('--prefix', '-p', default="Title", help="Prefix for output titles (default: Title).")
    args = parser.parse_args()

    process_dvd_vts(args.input, args.output, args.prefix)

if __name__ == '__main__':
    main()
