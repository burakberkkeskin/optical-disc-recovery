#!/usr/bin/env python3
"""
audit_archive.py
Performs deduplication analysis and file integrity audits across optical archive directories
using SHA-256 content hashing.
"""

import argparse
import hashlib
import os
import sys
from collections import defaultdict

def calculate_sha256(filepath, block_size=65536):
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b''):
                hasher.update(block)
        return hasher.hexdigest()
    except Exception as e:
        return None

def audit_directory(root_dir):
    print(f"[*] Scanning directory: {root_dir}...")
    by_hash = defaultdict(list)
    by_ext = defaultdict(lambda: {'count': 0, 'size': 0})
    total_files = 0
    total_bytes = 0

    for root, _, files in os.walk(root_dir):
        for f in files:
            if f.startswith('.'):
                continue
            path = os.path.join(root, f)
            try:
                sz = os.path.getsize(path)
            except OSError:
                continue

            ext = os.path.splitext(f)[1].lower() or '[no_ext]'
            by_ext[ext]['count'] += 1
            by_ext[ext]['size'] += sz
            total_files += 1
            total_bytes += sz

            h = calculate_sha256(path)
            if h:
                by_hash[h].append((path, sz))

    print("\n==========================================")
    print(f"Total Files Scanned : {total_files}")
    print(f"Total Archive Size  : {total_bytes / (1024**3):.2f} GB")
    print("==========================================\n")

    print("Extension Breakdown:")
    for ext, stats in sorted(by_ext.items(), key=lambda x: x[1]['size'], reverse=True):
        print(f"  {ext:12s}: {stats['count']:5d} files, {stats['size'] / (1024*1024):8.2f} MB")

    duplicates = {h: paths for h, paths in by_hash.items() if len(paths) > 1}
    print(f"\nDuplicate Groups Found: {len(duplicates)}")
    dup_wasted_bytes = sum((len(paths) - 1) * paths[0][1] for paths in duplicates.values())
    print(f"Redundant Storage Space: {dup_wasted_bytes / (1024*1024):.2f} MB")

def main():
    parser = argparse.ArgumentParser(description="Audit and deduplicate media archive directories.")
    parser.add_argument('directory', help="Root directory to audit.")
    args = parser.parse_args()

    audit_directory(args.directory)

if __name__ == '__main__':
    main()
