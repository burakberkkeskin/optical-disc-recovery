# Optical Disc Forensic Recovery & Modernization Pipeline

A production-grade, dual-tier digital preservation toolkit designed to rescue, repair, modernize, and catalog degraded optical media (CD-R, CD-RW, DVD-R, DVD+R, VCD) from the late 1990s through the early 2010s.

---

## 1. The Challenge of Optical Media Longevity

Writable optical media produced between 1995 and 2012 are reaching the end of their physical lifespans. Unlike stamped commercial discs (pressed aluminum), recordable discs rely on **organic dye layers** (cyanine, phthalocyanine, or azo) bonded to a polycarbonate substrate.

Common degradation mechanisms include:
* **Organic Dye Oxidation (Disc Rot):** Chemical breakdown of the dye layer, resulting in unreadable Lead-in tracks or uncorrectable Reed-Solomon errors (`L-EC`).
* **Adhesive Delamination:** Separation of the reflective foil from the polycarbonate disc.
* **Surface Polycarbonate Scratches:** Diffraction and scattering of the read laser beam.
* **Operating System File Copy Failure:** Standard file managers (`cp`, Finder, Windows Explorer) abort immediately upon encountering an I/O error or freeze when attempting to read bad sectors.

This toolkit implements a **Dual-Tier Preservation Architecture** that separates forensic raw preservation from daily streaming access.

---

## 2. Dual-Tier Preservation Architecture

```
┌─────────────────────────────────────────────────────────────┐
│               Degraded Physical Optical Disc                │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ddrescue (Direct SCSI Passthrough)
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│       TIER 1: FORENSIC BIT-STREAM MASTER (Immutable)        │
├─────────────────────────────────────────────────────────────┤
│  • Raw Disc Image: .iso / .bin                              │
│  • Rescue Mapfile: .map (Sector-level status ledger)        │
│  • Integrity Hashes: SHA-256 / MD5 checksums                │
│  • Pristine Extracted Filesystem: Original VOB / DAT / AVI  │
│  • Strictly 100% Read-Only: Zero modifications or re-encode │
└──────────────────────────────┬──────────────────────────────┘
                               │
                  Pipeline Scripts / Modernizers
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│            TIER 2: STREAM-READY ACCESS COPY                 │
├─────────────────────────────────────────────────────────────┤
│  • Video: H.265 (HEVC / hvc1) in MP4 container              │
│  • Deinterlacing: High-fidelity adaptive bwdif              │
│  • Streaming: +faststart moov atom header placement         │
│  • Audio: Resampled AAC-LC (192 kbps stereo)                │
│  • Photos: APFS hardlinked / reflinked (Zero extra disk)    │
│  • Timestamps: Sealed QuickTime container atoms & mtime/btime│
│  • Destination: Immich Timeline / Apple Photos / Jellyfin   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Hardware Reading Station

For maximum read success on failing discs, use a dedicated optical drive attached via direct SATA or an ASMedia/Prolific USB bridge with SCSI pass-through support:

```bash
# 1. Inspect drive capabilities and media information
dvd+rw-mediainfo /dev/sr0

# 2. Pin drive read speed (prevents head overheating and read buffer thrashing)
# High speeds cause vibration and read failure on scratched media.
sudo hdparm -E 8 /dev/sr0
```

---

## 4. Extraction & Forensic Imaging Workflow

### Step 1: Multi-Phase Block-Level Rescue with `ddrescue`

Run `GNU ddrescue` with direct hardware access (`-d`) to copy readable sectors first, followed by a targeted scraping pass on damaged blocks:

```bash
# Phase 1: Fast copy of all readable sectors without retries
ddrescue -b 2048 -d -v -n /dev/sr0 raw_discs/DISC-001.iso logs/DISC-001.map

# Phase 2: Reverse direction pass for edge-rot discs
ddrescue -b 2048 -d -v -R -n /dev/sr0 raw_discs/DISC-001.iso logs/DISC-001.map

# Phase 3: Targeted scraping pass on stubborn bad sectors (1-2 retries)
ddrescue -b 2048 -d -v -r 2 /dev/sr0 raw_discs/DISC-001.iso logs/DISC-001.map
```

### Step 2: Loopback Mounting & Bit-for-Bit Verification

Mount the image read-only and extract the raw filesystem:

```bash
# macOS
hdiutil attach -readonly raw_discs/DISC-001.iso -mountpoint /Volumes/DISC_001

# Linux
sudo mount -o loop,ro raw_discs/DISC-001.iso /mnt/disc
```

---

## 5. Modernization & Pipeline Scripts

### 1. Batch Video Modernizer (`modernize_videos.py`)
Converts legacy MPEG-1, MPEG-2 (VOB/DAT), and DivX/AVI into streaming-ready H.265 MP4 files. Uses Apple Silicon `hevc_videotoolbox` when available, falling back to `libx265`.

```bash
python3 scripts/modernize_videos.py \
  --target recovered_data/DISC-001 \
  --output-root modernized_export/DISC-001
```

**Key Features:**
* **Deinterlacing:** Motion-adaptive `bwdif` deinterlacer eliminates comb artifacts from 480i/576i camcorder footage.
* **Aspect Ratio Correction:** Normalizes non-square pixel DVD/VCD footage (720x576 -> 768x576 4:3 DAR).
* **Direct Streaming:** Sets `-tag:v hvc1` for native Safari/iOS hardware acceleration and `-movflags +faststart` for instant HTTP streaming.
* **Zero-Waste Photo Sync:** Automatically links photos (`.jpg`, `.png`) via filesystem hardlinks so no redundant disk space is consumed.

### 2. DVD-Video Processor (`modernize_dvd.py`)
Concatenates multi-part split VOBs (`VTS_01_1.VOB`, `VTS_01_2.VOB`) into single unified titles, corrects display ratios, and extracts individual chapters.

```bash
python3 scripts/modernize_dvd.py \
  --input recovered_data/DISC-048/extracted/VIDEO_TS \
  --output modernized_export/DISC-048 \
  --prefix Graduation_Ceremony
```

### 3. Timestamp & Metadata Sealing (`stamp_video_dates.py`)
**The DVD Authoring Trap:** When home videos were burned to DVD in the 2000s, software like Nero Burning ROM stamped the *burn date* (e.g. 2007) onto all filesystem entries, obliterating the original capture date (e.g. 2001).

This tool losslessly injects the correct historical capture date into the MP4 `moov` container atom and aligns filesystem `mtime` and `btime`:

```bash
python3 scripts/stamp_video_dates.py modernized_export/DISC-046/Summer_Trip.mp4 "2001-07-15"
```

### 4. Photo Linker (`link_photos.py`)
Synchronizes photos from raw disc extractions into the export tree using APFS hardlinks (or file clones), preserving 100% byte integrity without consuming additional disk space.

```bash
python3 scripts/link_photos.py \
  --source recovered_data/DISC-014 \
  --dest modernized_export/DISC-014
```

### 5. Collection Auditor & Deduplication (`audit_archive.py`)
Scans directories using SHA-256 content hashing to identify duplicate files across different backup discs and reports wasted storage.

```bash
python3 scripts/audit_archive.py modernized_export/
```

---

## 6. Self-Hosted Cloud Ingestion (Immich / PhotoPrism)

To ingest modernized files into self-hosted platforms like [Immich](https://immich.app) directly onto the chronological timeline:

### 1. Configure Container Acceptance
By default, some servers may attempt to transcode all uploaded MP4s. To prevent redundant server-side re-encoding, ensure `mp4` is included in accepted containers:
* **Immich Settings:** `Administration -> Settings -> Video Transcoding Settings -> Accepted Containers` -> Add `mp4`.

### 2. Upload via `immich-go`
Use `immich-go` (v0.32.0+ for Immich v3 compatibility) to ingest assets without creating artificial folder albums:

```bash
immich-go upload from-folder \
  --server="https://immich.example.com" \
  --api-key="YOUR_API_KEY" \
  --on-errors=continue \
  --concurrent-tasks=5 \
  --no-ui \
  modernized_export/
```

---

## 7. Cataloging & SOP Checklists

* **Inventory Tracking:** Use [`catalogue/inventory_template.csv`](catalogue/inventory_template.csv) to record media IDs, manufacturer codes, sector counts, and recovery percentages.
* **Standard Operating Procedure:** Use [`plans/TEMPLATE.md`](plans/TEMPLATE.md) as a standard checklist when receiving and processing each physical disc.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
