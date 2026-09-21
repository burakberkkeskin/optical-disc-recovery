# Role: Cloud Ingestion & Metadata Librarian

## 1. Scope of Responsibility
Responsible for chronological metadata verification, evading legacy disc burning timestamp traps, container atom sealing, self-hosted cloud platform configuration (Immich / PhotoPrism), and bulk timeline ingestion.

---

## 2. The DVD Authoring Burn Date Trap

### The Problem
When home videos or photo CDs were authored in the 2000s, burning software (such as Nero Burning ROM, Sonic MyDVD, or Roxio) wrote the **disc burning date** (e.g., August 2007) onto the disc filesystem. The original camcorder capture date (e.g., October 2001) was completely lost in filesystem attributes.

If uploaded directly, indexing engines (Immich, Apple Photos, Google Photos) will index the asset in 2007 instead of 2001.

### The Solution: QuickTime Atom & Filesystem Sealing
Use `scripts/stamp_video_dates.py` to losslessly embed the true historical date:
1. **Container Atom:** Sets QuickTime `creation_time` in the MP4 `moov` metadata header without re-encoding video streams (`-c copy`).
2. **Filesystem Timestamps:** Aligns filesystem modification time (`mtime`) and birth/creation time (`btime`) via `touch -t` and macOS `SetFile`.

```bash
python3 scripts/stamp_video_dates.py modernized_export/Sample_2001.mp4 "2001-10-07"
```

---

## 3. Immich Ingestion Optimization

### A. Preventing Redundant Server Transcoding
Immich server settings may default to `transcode: "required"` and omit `mp4` from `acceptedContainers`:
* **Config Endpoint:** `PUT /api/system-config`
* **Setting:** Ensure `"acceptedContainers": ["mp4", "mov", "ogg", "webm"]`.
* **Benefit:** When modernized H.265/AAC MP4 files are uploaded, Immich recognizes them as direct-play compatible and skips server-side CPU/GPU transcoding.

### B. Reliable Bulk Upload via `immich-go`
Use `immich-go` (version 0.32.0+ for Immich v3 compatibility) to upload assets directly to the chronological timeline without creating redundant folder albums:

```bash
immich-go upload from-folder \
  --server="https://immich.example.com" \
  --api-key="$IMMICH_API_KEY" \
  --on-errors=continue \
  --concurrent-tasks=5 \
  --no-ui \
  modernized_export/
```

* `--on-errors=continue`: Prevents temporary network socket resets from aborting multi-gigabyte batch uploads.
* `--concurrent-tasks=5`: Balances upload throughput while preventing reverse-proxy connection drops on large video files.
* `--dry-run`: Always simulate full uploads first to verify asset counts and deduplication before transferring bytes.
