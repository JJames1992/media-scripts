# Subtitle Pipeline — Resume Instructions

**Current Status (as of Oct 10 ~06:00 UTC):**
- 52 EN SRTs / 50 ES SRTs downloaded successfully
- OpenSubtitles free API key (`0aP1frJExP49O5il7X97JbivcKdeIDiy`) is rate-blocked on the host IP
- VPN-Argentina (vpn-torrent-docker) server AR#106 is down (Proton infrastructure maintenance: Aug 31–Oct 12)

## Option 1: Fresh OpenSubtitles Account (Recommended)

1. **On any device with a browser**, visit: https://opensubtitles.com/sign-up
2. **Create a free account** (requires email verification — check your inbox)
3. After account creation, visit your profile → Settings → **API consumers**
4. Click **Generate new consumer** (give it any name like "hermes-script")
5. **Copy the API key** (32-char alphanumeric)
6. On your home PC, edit `OneDrive/AI/api-keys.txt`:
   - Find the `opensubtitles.com` section
   - Add a new line below it: `new_api_key = YOUR_NEW_KEY_HERE`
7. In `media-scripts/.env`, change:
   ```
   OPENSUBTITLESCOM_API_KEY=YOUR_NEW_KEY_HERE
   ```
8. Re-run:
   ```powershell
   cd C:\Users\jonat\media-scripts
   python3 subtitle_pipeline.py download --all
   ```

## Option 2: Use VPN to Get Past IP Ban

1. **Stop the current VPN container:**
   ```powershell
   cd C:\Users\jonat\vpn-torrent-docker
   docker compose stop vpn
   ```

2. **Download WireGuard configs for a different server:**
   - Visit https://account.protonvpn.com/downloads
   - Log in → Downloads → WireGuard config
   - Pick any server **except Argentina AR#** servers (e.g., US-East, US-West, Netherlands, Switzerland)
   - Download the `.conf` file

3. **Replace the VPN config:**
   - Extract just the `[Interface]` and `[Peer]` sections
   - Replace `vpn/wg0.conf` contents with the new config

4. **Restart:**
   ```powershell
   docker compose up -d vpn aria2
   ```

5. **Verify TCP connectivity:**
   ```powershell
   docker exec vpn-argentina wget -q -O - "https://api.opensubtitles.com/api/v1" --header="Api-Key: YOUR_KEY"
   ```

6. Re-run the subtitle pipeline.

## Progress Snapshot (current)

```
Total movies: 1574
EN SRTs: 52
ES SRTs: 50
Both EN+ES: 50
Remaining: ~1524
```

## Notes

- The free OpenSubtitles API allows ~100 downloads/day
- With rate limiting (5 req/sec) and the daily refresh, expect ~100 files per day
- Pipeline will continue from where it left off (only downloads missing subtitles)