# AGENTS.md

This file provides persistent context, architectural invariants, operational rules, and execution workflows for all AI agents working in this repository.

---

## 1. Project Mission & Invariants

This repository provides an automated, dual-tier digital preservation framework for degraded optical media (CD-R, CD-RW, DVD-R, DVD+R, VCD) from 1995–2012.

### The Dual-Tier Invariant (Never Violate)
1. **Tier 1 (`raw_discs/` or `recovered_data/`):**
   * **Immutable forensic bit-stream masters.**
   * Contains raw disc images (`.iso`, `.bin`), sector mapfiles (`.map`), and untouched extracted filesystems.
   * **Rule:** NEVER modify, re-encode, or delete Tier 1 files. They represent the exact physical bits rescued from optical media.
2. **Tier 2 (`modernized_export/`):**
   * **Streaming-ready, modernized access copies.**
   * Contains H.265 MP4 (`-tag:v hvc1`, faststart, deinterlaced) and hardlinked photos.
   * Sealed with true historical capture dates.

---

## 2. Specialized Roles (`roles/`)

When tasked with specific operations, adopt the corresponding role protocol:

* **Forensic Hardware & Imaging Specialist (`roles/forensic_operator.md`):**
  * Drive speed pinning (`hdparm -E 8 /dev/sr0`), SCSI passthrough, `ddrescue` multi-phase execution (forward, reverse, scraping), and sector patching.
* **Media Modernization Archivist (`roles/media_archivist.md`):**
  * Multi-part VOB concatenation, aspect ratio normalization (768x576 4:3), `bwdif` deinterlacing, and Apple Silicon / libx265 encoding.
* **Cloud Ingestion & Metadata Librarian (`roles/cloud_librarian.md`):**
  * QuickTime atom timestamp sealing (`stamp_video_dates.py`), server container acceptance tuning (`acceptedContainers`), and bulk timeline ingestion via `immich-go`.

---

## 3. Operational Rules (Absolute)

1. **Safety & Laser Preservation:**
   * Never run raw optical drives at maximum speed (>12x) on degraded media. Always pin to `8x` or `4x` to prevent head overheating and track vibration.
2. **Never Overwrite Capture Dates with Burn Dates:**
   * DVD authoring software (e.g. Nero Burning ROM) stamped compilation burn dates (e.g. 2007) over legacy videos (e.g. 2001).
   * Always verify video capture dates (via on-screen OSD or filenames) and seal both the MP4 container atom and filesystem timestamps using `scripts/stamp_video_dates.py`.
3. **Zero Inode Waste (Photos):**
   * Never copy photo files blindly between tiers. Always use APFS / POSIX hardlinks (`scripts/link_photos.py`) to share physical disk blocks.
4. **Privacy & Anonymity:**
   * Never commit personal family names, private domain names, internal IP addresses, or API keys into git. Always use generic placeholders (`Sample_2001`, `https://immich.example.com`).
5. **No Blind Commits or Force Pushes:**
   * Test code before committing (`python3 -m py_compile scripts/*.py`).
   * Do not push to remote repositories without explicit user alignment.

---

## 4. Standard Recovery Lifecycle (Per-Disc SOP)

For each physical optical disc, execute the following state machine:

```
[1. Inspection & Cleaning]
        │ (Microfiber radial wipe, Media ID detection via dvd+rw-mediainfo)
        ▼
[2. Hardware Speed Pinning]
        │ (sudo hdparm -E 8 /dev/sr0)
        ▼
[3. Multi-Pass ddrescue Imaging]
        │ (Pass 1: forward sweep -> Pass 2: reverse sweep -> Pass 3: scraping)
        ▼
[4. Bit Verification & Loopback Extraction]
        │ (SHA-256 hash, read-only mount via hdiutil or mount -o loop,ro)
        ▼
[5. Tier 2 Modernization]
        │ (scripts/modernize_videos.py or scripts/modernize_dvd.py)
        ▼
[6. Metadata & Timestamp Sealing]
        │ (scripts/stamp_video_dates.py)
        ▼
[7. Inventory & Catalog Logging]
        │ (Update catalogue/inventory.csv and plans/DISC-XXX.md)
        ▼
[8. Cloud Timeline Ingestion]
        │ (immich-go upload from-folder --on-errors=continue)
```

---

## 5. Tooling Quick Reference

```bash
# Modernize raw video files to H.265 MP4
python3 scripts/modernize_videos.py --target <RAW_DIR> --output-root <EXPORT_DIR>

# Process DVD-Video (VIDEO_TS) split VOB titles
python3 scripts/modernize_dvd.py --input <VIDEO_TS_PATH> --output <EXPORT_DIR> --prefix <TITLE>

# Seal true capture date into MP4 container and filesystem stamps
python3 scripts/stamp_video_dates.py <FILE.mp4> "YYYY-MM-DD"

# Hardlink photos without extra storage
python3 scripts/link_photos.py --source <RAW_DIR> --dest <EXPORT_DIR>

# Audit collection for duplicate files via SHA-256
python3 scripts/audit_archive.py <EXPORT_DIR>
```
