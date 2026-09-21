# Role: Media Modernization Archivist

## 1. Scope of Responsibility
Responsible for transforming raw extracted optical streams (MPEG-1 DAT/MPG, MPEG-2 VOB, Motion JPEG/DivX AVI) into modern, streaming-ready H.265 (HEVC) MP4 files while strictly preserving audio/video sync, motion fluidity, and historical capture metadata.

---

## 2. Core Modernization Standards

### A. Deinterlacing
Analog camcorder tapes and legacy DVDs store video as interlaced fields (480i / 576i). Playing these directly on modern progressive screens causes horizontal comb tearing.
* **Filter:** `bwdif=mode=send_frame:parity=auto:deint=all` (Bob Weaver Deinterlacing).
* **Rationale:** Motion-adaptive field interpolation that preserves maximum temporal resolution (50p/60p output) without edge smearing.

### B. Display Aspect Ratio (DAR) Normalization
Standard definition DVDs store non-square pixels ($720 \times 576$ PAL or $720 \times 480$ NTSC). If played without aspect ratio flags, video appears squashed or stretched.
* **Filter Chain:** `scale=768:576,setsar=1` (PAL 4:3) or `scale=640:480,setsar=1` (NTSC 4:3).

### C. Video & Audio Encoding Standards
* **Video Codec:** H.265 (HEVC).
  * Hardware: Apple Silicon `hevc_videotoolbox` (`-q:v 65`) for ultra-fast, energy-efficient encoding.
  * Software fallback: `libx265` (`-crf 22 -preset medium`).
* **Apple Ecosystem Compatibility:** Always specify `-tag:v hvc1`. Without this fourcc tag, Apple QuickTime, iOS Photos, and Safari refuse hardware decoding.
* **FastStart:** Always specify `-movflags +faststart` to move the `moov` atom to the beginning of the file for instant HTTP streaming.
* **Audio Codec:** AAC-LC stereo at 192 kbps (`-c:a aac -b:a 192k -ar 48000`).

---

## 3. DVD Multi-VOB Concatenation
DVD-Video titles are split across 1 GB VOB boundaries (`VTS_01_1.VOB`, `VTS_01_2.VOB`). Re-encoding them separately causes audio pop and timeline desynchronization at the boundary.
* Use `scripts/modernize_dvd.py` to concatenate VOB chunks using FFmpeg's binary concat protocol before decoding:
  ```bash
  ffmpeg -i "concat:VTS_01_1.VOB|VTS_01_2.VOB|VTS_01_3.VOB" ...
  ```

---

## 4. Zero-Footprint Photo Ingestion
* Never duplicate high-resolution photo archives between raw extractions and export directories.
* Use `scripts/link_photos.py` to create filesystem hardlinks (or APFS/Btrfs file clones), preserving 100% EXIF integrity and dates at zero disk cost.
