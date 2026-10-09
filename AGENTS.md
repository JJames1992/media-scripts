# Home PC — Media Management Agent Rules

## This Machine
- Windows 11 Pro 64-bit, build 26200 (not Windows 10), git-bash (MSYS) for terminal
- GEEKOM A9 Max — AMD Ryzen AI 9 HX 470 (Radeon 890M iGPU), 12C/24T
- NVIDIA GeForce RTX 5070 Ti, 16 GB VRAM (sm_120 / CC 12.0), driver 616.92
- RAM: 128 GB total (2x64 GB Micron DDR5-5600 CL46)
- Docker Desktop 29.7.2 on WSL2
- User home: C:\Users\jonat
- Scripts dir: C:\Users\jonat\media-scripts
- Jellyfin at J:\Media-Archive (Movies/, TV Shows/)
- Jellyfin server: native Windows, runs as a **process** not a registered
  service (C:\Program Files\Jellyfin\Server\jellyfin.exe, port 8096)
- Primary drive: J: 3.6 TB (was labelled "4TB")

## Drives (verify free space before large ops)
- C: 1.87 TB — ⚠️ was at 31 GB free (1.6%) on 2026-09-30; watch for venv/Docker/browser growth
- D: 1.82 TB "Internal 2TB" — 139 GB free
- J: 3.64 TB "4TB" — 1.10 TB free (Jellyfin media + J:\Backups)
- K: 1.82 TB — 1.18 TB free (qBittorrent downloads bind-mount to K:/docker-data)

## Media Workflows

NOTE: there is NO scheduled media automation. Everything below is either a
one-shot script you run by hand, or a container stack that must be started by
hand. Do not assume a cron job exists — verify with `cronjob_manage list`.

### TV Gap-Filling (manual, no automation)
- `python gap_discovery.py` — compares on-disk episodes vs TVMaze; ANALYSIS ONLY,
  it does not search or download anything
- `python tv_fix_plan.py` — builds a per-season fix plan (search strings)
- These print a plan. Acting on it is a separate manual step.

### Movie Dedup
- `python dedup_movies.py` — finds duplicate movie copies on disk and reports
  them; it does not delete unless you pass the delete flag

### Downloads (the *arr stack — NOT the scripts above)
- Acquisition is Docker: qbittorrent (:8080), radarr (:7878), sonarr (:8989),
  prowlarr (:8920). Containers, not Windows services.
- The gap-fill Python scripts are NOT wired into these and do not drive them.
- No seeder thresholds, parallel-download limits, or per-item timeouts are
  configured in any script here. (An earlier version of this file claimed
  "min seeders 2/5", "3 parallel, 15min timeout", "7200s low-seed timeout" —
  none of that code exists. It was removed 2026-09-30.)

### VPN
- ProtonVPN, "Fastest Country P2P", manual via GUI (not CLI)

## Conventions
- Verify files on disk before marking any task "done"
- Batch parallel tool calls when possible — this is a home PC, not a server
- Scheduling is split, contrary to an earlier claim here: Hermes crons handle
  YNAB/Outlook/backup work, while the media side runs on a raw Windows
  Scheduled Task named `MediaMonitor` (hourly, runs
  `%LOCALAPPDATA%\hermes\scripts\media_monitor.py`). Both exist. Prefer
  `cronjob_manage` for new work, but do not "migrate" MediaMonitor without
  reading it first.
