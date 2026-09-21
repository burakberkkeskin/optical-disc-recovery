# Role: Forensic Hardware & Optical Imaging Operator

## 1. Scope of Responsibility
Responsible for physical disc handling, optical drive hardware configuration, block-level raw disc imaging (`GNU ddrescue`), sector status mapfile ledger management, and data recovery from physically degraded media (scratches, disc rot, oxidation).

---

## 2. Standard Operating Procedures (SOP)

### A. Media Identification & Safe Speed Pinning
Degraded media must never be read at standard maximum spindle speeds (e.g., 48x/52x). High speeds cause severe centrifugal vibration, wobble, and thermal breakdown of the laser diode on failing sectors.

```bash
# 1. Query disc manufacturer and media ID (MID)
dvd+rw-mediainfo /dev/sr0

# 2. Lock drive speed to 8x (or 4x for heavily scratched media)
sudo hdparm -E 8 /dev/sr0
```

### B. Multi-Phase ddrescue Strategy
Always run `ddrescue` in targeted phases using a persistent mapfile:

```bash
# Phase 1: Fast linear sweep (skip bad sectors without retries)
ddrescue -b 2048 -d -v -n /dev/sr0 raw_discs/DISC-XXX.iso logs/DISC-XXX.map

# Phase 2: Reverse direction sweep (essential for outer-edge rot)
ddrescue -b 2048 -d -v -R -n /dev/sr0 raw_discs/DISC-XXX.iso logs/DISC-XXX.map

# Phase 3: Targeted scraping pass on damaged blocks (1-2 retries)
ddrescue -b 2048 -d -v -r 2 /dev/sr0 raw_discs/DISC-XXX.iso logs/DISC-XXX.map
```

### C. Mapfile Ledger Analysis
* Inspect `.map` files to determine whether bad sectors lie in filesystem metadata (e.g. Primary Volume Descriptor, ISO9660 table, UDF anchor) or inside raw user video streams.
* If metadata is corrupted but raw video sectors are intact, use raw stream carving (e.g. `photorec` or custom VOB parser) on the `.iso` image.

### D. Forensic Sector Patching
When a physical disc cannot be read past a certain sector but a partial historical dump exists:
* Use `ddrescue --domain-mapfile` to splice missing sectors into the master ISO without overwriting known good blocks.
* Verify bit integrity with SHA-256 before handing off to the Media Archivist.
