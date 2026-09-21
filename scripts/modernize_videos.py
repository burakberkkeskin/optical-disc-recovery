#!/usr/bin/env python3
"""
modernize_videos.py
Batch video modernization pipeline for optical disc extractions (VCD, DVD, AVI, MPG).
Converts legacy interlaced MPEG-1/MPEG-2/DivX streams into streaming-ready H.265 (HEVC) MP4
with hardware acceleration (Apple Silicon VideoToolbox or libx265 fallback),
maintaining exact historical timestamps and deduplicating identical titles.
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys

VIDEO_EXTENSIONS = {'.avi', '.mpg', '.mpeg', '.dat', '.vob', '.wmv', '.mov', '.asf', '.m4v'}

def get_file_md5(filepath, block_size=65536):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            hasher.update(block)
    return hasher.hexdigest()

def probe_video(filepath):
    """Probe video streams and container metadata via ffprobe."""
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', '-show_streams', filepath
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return json.loads(res.stdout)
    except Exception as e:
        print(f"[-] Probe error on {filepath}: {e}")
        return None

def detect_encoder():
    """Detect hardware encoder availability."""
    system = platform.system()
    machine = platform.machine()
    if system == 'Darwin':
        # Check if videotoolbox is supported
        cmd = ['ffmpeg', '-v', 'quiet', '-encoders']
        res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        if 'hevc_videotoolbox' in res.stdout:
            return 'hevc_videotoolbox'
    return 'libx265'

def convert_video(src_path, dst_path, encoder):
    """Modernizes legacy video to H.265 MP4 with faststart, bwdif deinterlacing, and DAR correction."""
    info = probe_video(src_path)
    if not info:
        return False

    v_stream = next((s for s in info.get('streams', []) if s.get('codec_type') == 'video'), None)
    if not v_stream:
        print(f"[-] No video stream found in {src_path}")
        return False

    width = int(v_stream.get('width', 0))
    height = int(v_stream.get('height', 0))

    # Standard SD 4:3 correction (PAL 720x576 / NTSC 720x480)
    dar = v_stream.get('display_aspect_ratio', '')
    vf_filters = ['bwdif=mode=send_frame:parity=auto:deint=all'] # High quality deinterlacing

    if dar == '4:3' or (width in [720, 704] and height == 576):
        vf_filters.append('scale=768:576,setsar=1')
    elif dar == '4:3' or (width in [720, 704] and height == 480):
        vf_filters.append('scale=640:480,setsar=1')
    elif width > 0 and height > 0:
        vf_filters.append('setsar=1')

    vf_chain = ','.join(vf_filters)

    cmd = [
        'ffmpeg', '-y', '-v', 'error', '-stats',
        '-i', src_path,
        '-vf', vf_chain,
    ]

    if encoder == 'hevc_videotoolbox':
        cmd.extend([
            '-c:v', 'hevc_videotoolbox',
            '-q:v', '65',
            '-tag:v', 'hvc1',
        ])
    else:
        cmd.extend([
            '-c:v', 'libx265',
            '-crf', '22',
            '-preset', 'medium',
            '-tag:v', 'hvc1',
        ])

    cmd.extend([
        '-c:a', 'aac',
        '-b:a', '192k',
        '-movflags', '+faststart',
        dst_path
    ])

    print(f"[+] Modernizing: {os.path.basename(src_path)} -> {os.path.basename(dst_path)}")
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"[-] Conversion failed for {src_path}")
        if os.path.exists(dst_path):
            os.remove(dst_path)
        return False

    # Preserve exact historical filesystem timestamps
    shutil.copystat(src_path, dst_path)
    return True

def process_directory(target_dir, output_root, sync_photos=True):
    encoder = detect_encoder()
    print(f"[*] Encoder detected: {encoder}")

    os.makedirs(output_root, exist_ok=True)
    hash_cache = {}

    for root, _, files in os.walk(target_dir):
        for f in sorted(files):
            ext = os.path.splitext(f)[1].lower()
            src = os.path.join(root, f)
            rel_path = os.path.relpath(src, target_dir)

            if ext in VIDEO_EXTENSIONS:
                # Video file
                dst_name = os.path.splitext(f)[0] + '.mp4'
                dst_dir = os.path.join(output_root, os.path.dirname(rel_path))
                os.makedirs(dst_dir, exist_ok=True)
                dst = os.path.join(dst_dir, dst_name)

                if os.path.exists(dst):
                    print(f"[*] Skipping existing: {dst}")
                    continue

                f_hash = get_file_md5(src)
                if f_hash in hash_cache:
                    cached_dst = hash_cache[f_hash]
                    print(f"[*] Deduplicating identical video: {f} -> Linking to {cached_dst}")
                    try:
                        os.link(cached_dst, dst)
                    except OSError:
                        shutil.copy2(cached_dst, dst)
                    continue

                if convert_video(src, dst, encoder):
                    hash_cache[f_hash] = dst

            elif sync_photos and ext in {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}:
                # Photo hardlink/clone
                dst_dir = os.path.join(output_root, os.path.dirname(rel_path))
                os.makedirs(dst_dir, exist_ok=True)
                dst = os.path.join(dst_dir, f)
                if not os.path.exists(dst):
                    try:
                        os.link(src, dst)
                    except OSError:
                        shutil.copy2(src, dst)

def main():
    parser = argparse.ArgumentParser(description="Modernize legacy videos to Apple/Immich compatible H.265 MP4.")
    parser.add_argument('--target', '-t', required=True, help="Target directory containing extracted raw media.")
    parser.add_argument('--output-root', '-o', default='modernized_export', help="Output root directory.")
    parser.add_argument('--no-photos', action='store_true', help="Do not hardlink/sync photos.")
    args = parser.parse_args()

    process_directory(args.target, args.output_root, sync_photos=not args.no_photos)

if __name__ == '__main__':
    main()
