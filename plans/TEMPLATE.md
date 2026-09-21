# Recovery Plan & Tracking SOP: DISC-XXX

## 1. Physical Specifications & Media Identity
- **Disc ID:** DISC-XXX
- **Label / Inscription:** [Text written on disc label]
- **Media Type:** [CD-R / DVD-R / DVD+R / VCD]
- **Manufacturer / MID:** [e.g. TYG02, MCC 03RG20, CMC MAG M01 via dvd+rw-mediainfo]
- **Physical Condition:** [Clean / Lightly Scratched / Heavily Scratched / Dye Degradation]
- **Estimated Year:** [YYYY]
- **Capacity / Sectors:** [Estimated sectors and byte size]

## 2. Recovery Workflow Checklist
- [ ] Physical inspection & microfiber cleaning (radial wiping, center to rim)
- [ ] Optical diagnostic gate (30s TOC detection via `cd-info` or `dvd+rw-mediainfo`)
- [ ] Drive speed pinning (`hdparm -E 8 /dev/sr0` to limit thermal stress)
- [ ] Block-level direct raw imaging (`ddrescue -b 2048 -d -v ...`)
- [ ] Mapfile review & second-pass scraping if bad sectors exist
- [ ] Bit-level SHA-256 / MD5 master hash generation
- [ ] Read-only loopback mount & filesystem extraction (`hdiutil attach -readonly` or `mount -o loop,ro`)
- [ ] Original timestamp restoration (`touch -r` from disc master)
- [ ] Tier 2 Modernization:
  - [ ] Video transcoding to H.265 MP4 (`modernize_videos.py` or `modernize_dvd.py`)
  - [ ] Photo synchronization via APFS hardlinks (`link_photos.py`)
  - [ ] Timestamp verification & QuickTime atom sealing (`stamp_video_dates.py`)
- [ ] Catalog update (`catalogue/inventory.csv`)

## 3. Technical Notes & Recovery Strategy
- **Command Used:**
  ```bash
  ddrescue -b 2048 -d -v -r 2 /dev/sr0 raw_discs/DISC-XXX.iso logs/DISC-XXX.map
  ```
- **Obstacles & Root Cause:** [Note any unreadable sectors, disc rot, or Lead-in retries]
- **Outcome & File Verification:** [Number of rescued files, checksum verification, video stream continuity]
