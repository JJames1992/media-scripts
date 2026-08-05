# Home PC — Media Management Agent Rules

## This Machine
- Windows 10, git-bash (MSYS) for terminal
- User home: C:\Users\jonat
- Scripts dir: C:\Users\jonat\media-scripts
- Jellyfin at J:\Media-Archive (Movies/, TV Shows/)
- Primary drive: 4TB (J:)

## Media Workflows

### TV Gap-Filling
- Run via: `python tv_fix_plan.py` / `python gap_discovery.py`
- Cron: media-gapfill-2am / media-gapfill-9am
- Per-season torrent queries first, then generic fallback
- Min seeders: 2 for TV, 5 for movies

### Movie Dedup
- Run: `python dedup_movies.py`

### Downloads
- 3 parallel, 15min timeout per item
- 7200s timeout on low-seed torrents
- Partial downloads cleaned on failure

### VPN
- Use ProtonVPN "Fastest Country P2P"
- Manual via GUI (not CLI)

## Conventions
- Verify files on disk before marking any task "done"
- Batch parallel tool calls when possible — this is a home PC, not a server
- Use `hermes cronjob` for scheduling, not raw Windows tasks
