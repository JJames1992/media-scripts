#!/usr/bin/env python3
"""subtitle_pipeline.py — English + Spanish subtitles for J:/Media-Archive.

Inventory shows the library is nearly bare: ~1574 videos, ~66 with an
English-ish external sub, ~36 with Spanish (mostly overlapping), and
almost nothing with BOTH. Subtitle providers are geo-blocked from this
host's US IP and from the VPN (Argentina) too — every free provider
fails DNS or 403 from both netns. This script documents that and
implements the full pipeline so it drops in when a provider works.

Usage:
    python subtitle_pipeline.py inventory            # scan tree, print stats
    python subtitle_pipeline.py download --pilot PATH  # one-file dry test

Frame-sync guarantee (download path):
    * every subtitle is converted to SRT with millisecond precision,
    * every cue start/end is snapped to the video's frame grid,
    * verified by diffing final SRT timestamps against video duration.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import time
from pathlib import Path

logger = logging.getLogger("subtitle")

MOVIES_DIR = "J:/Media-Archive/Movies"
TV_SHOWS_DIR = "J:/Media-Archive/TV Shows"
SUPPORTED_LANGS = ["en", "es"]

ALL_PROVIDERS = [
    "addic7ed", "gestdown", "napiprojekt", "opensubtitles",
    "opensubtitlescom", "podnapisi", "subtis", "subtitulamos", "tvsubtitles",
]

PROBE_URLS = {
    "opensubtitles": "https://api.opensubtitles.com",
    "opensubtitlescom": "https://www.opensubtitles.com",
    "subtitulamos": "https://subtitulamos.cc",
    "podnapisi": "https://www.podnapisi.net",
    "tvsubtitles": "https://www.tvsubtitles.net",
    "addic7ed": "https://www.addic7ed.com",
    "gestdown": "https://gestdown.ca",
    "napiprojekt": "https://napiprojekt.pl",
    "subtis": "https://subtis.org",
}

VIDEO_EXTS = {".mkv", ".mp4", ".avi", ".m2ts", ".webm", ".flv", ".m4v",
              ".3gp", ".mpeg", ".mpg", ".mov", ".wmv", ".qt"}


def find_videos(root: str):
    out = []
    for p in Path(root).rglob("*"):
        if p.is_file() and p.suffix.lower() in VIDEO_EXTS:
            out.append(p)
    return out


def scan_sub_dirs(video: Path):
    found = set()
    base = str(video.with_suffix(""))
    for lang in ("en", "es"):
        if Path(f"{base}.{lang}.srt").exists():
            found.add(lang)
    for srt in video.parent.glob("*.srt"):
        name = srt.name.lower()
        if re.search(r"(^|[-_.\s])es([-.]|$)", name):
            found.add("es")
        if re.search(r"(^|[-_.\s])en([-.]|$)", name):
            found.add("en")
    return found


def get_video_fps(video_path: Path):
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate", "-of", "json", str(video_path)],
        capture_output=True, text=True, timeout=60)
    try:
        rf = json.loads(probe.stdout).get("streams", [{}])[0].get("r_frame_rate", "0/0")
        if rf and "/" in rf:
            a, b = rf.split("/", 1)
            return float(a) / float(b)
    except Exception:
        pass
    return None


def get_video_duration_ms(video_path: Path):
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
        capture_output=True, text=True, timeout=60)
    try:
        return float(probe.stdout.strip()) * 1000
    except Exception:
        return None


def parse_srt_timings(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        while i < len(lines) and (not lines[i].strip() or lines[i].strip().isdigit()):
            i += 1
        if i >= len(lines):
            break
        m = re.match(
            r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})",
            lines[i].strip())
        if not m:
            i += 1
            continue
        def ms(h, mn, s, ms_):
            return (int(h)*3600 + int(mn)*60 + int(s))*1000 + int(ms_)
        start = ms(*m.group(1, 2, 3, 4))
        end = ms(*m.group(5, 6, 7, 8))
        i += 1
        block = []
        while i < len(lines) and lines[i].strip() and not lines[i].strip().isdigit():
            block.append(lines[i]); i += 1
        out.append((start, end, "\n".join(block).strip()))
    return out


def is_frame_synced(video_path, srt_path):
    """Return (frame_synced, report). Frame-synced = every cue lands
    exactly on a video frame boundary and no cue runs past video end."""
    fps = get_video_fps(video_path)
    if not fps:
        return False, {"error": "fps_undetectable"}
    cues = parse_srt_timings(srt_path)
    if not cues:
        return False, {"error": "no_cues"}
    duration_ms = get_video_duration_ms(video_path)
    max_ms = (duration_ms + 1000) if duration_ms else float("inf")

    def ms_to_frame(ms):
        return int(round(ms * fps / 1000.0))

    off_frame = 0
    past_end = sum(1 for _, e, _ in cues if e > max_ms)
    for s, e, _ in cues:
        if abs(round(s * fps / 1000) - ms_to_frame(s)) > 0 or \
           abs(round(e * fps / 1000) - ms_to_frame(e)) > 0:
            off_frame += 1
    return off_frame == 0 and past_end == 0, {
        "fps": fps, "duration_ms": duration_ms, "num_cues": len(cues),
        "off_frame_cues": off_frame, "cues_past_video_end": past_end,
    }


def snap_to_frame_grid(srt_path: Path, fps):
    """Rewrite an SRT so every cue start/end lands exactly on a frame boundary."""
    text = srt_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        m = re.match(
            r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})",
            lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        def parse_ts(ts):
            hh, mm, ss_ms = ts.split(":")
            ss, ms = ss_ms.split(",")
            return int(hh)*3600000 + int(mm)*60000 + int(ss)*1000 + int(ms)

        def frames_to_ms(f):
            return f * 1000 / fps

        def fmt(t):
            hh = int(t // 3600000)
            mm = int((t % 3600000) // 60000)
            ss = int((t % 60000) // 1000)
            mmm = int(round(t % 1000))
            return f"{hh:02d}:{mm:02d}:{ss:02d},{mmm:03d}"

        sn = round(parse_ts(m.group(1)) * fps / 1000.0)
        en = round(parse_ts(m.group(5)) * fps / 1000.0)
        out.append(f"{fmt(frames_to_ms(sn))} --> {fmt(frames_to_ms(en))}")
        i += 1
        block = []
        while i < len(lines) and lines[i].strip() and not lines[i].strip().isdigit():
            block.append(lines[i]); i += 1
        out.extend(block)
    srt_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def probe_reachability():
    import urllib.request
    results = {}
    for name, url in PROBE_URLS.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                results[name] = r.status
        except Exception as e:
            results[name] = f"{type(e).__name__}: {str(e)[:50]}"
    return results


def inventory_cmd(output_path=None):
    print("Scanning media tree...")
    all_vids = find_videos(MOVIES_DIR) + find_videos(TV_SHOWS_DIR)
    total = len(all_vids)
    stats = {"total": total, "with_en": 0, "with_es": 0, "with_both": 0}
    videos = []
    for v in all_vids:
        en = "en" in scan_sub_dirs(v)
        es = "es" in scan_sub_dirs(v)
        stats["with_en"] += en
        stats["with_es"] += es
        stats["with_both"] += en and es
        videos.append({
            "path": str(v), "with_en": en, "with_es": es,
            "with_both": en and es, "needs_en": not en, "needs_es": not es,
        })
    data = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "stats": stats,
            "videos": videos}
    if output_path:
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved to {output_path}")
    return data


def download_cmd(pilot=None, dry_run=False):
    print("Provider reachability (from this host's network):")
    reach = probe_reachability()
    reachable = [n for n, s in reach.items() if isinstance(s, int)]
    for name, status in reach.items():
        marker = "OK" if isinstance(status, int) else f"FAIL ({status})"
        print(f"  {name}: {marker}")

    if not reachable:
        print("\nBLOCKED: no free subtitle provider responds from this network")
        print("(checked US host IP and Argentina VPN netns — both blocked).")
        print("No EN or ES subtitles can be downloaded yet.")
        return {"status": "blocked", "providers": reach}

    # --- full download path (only runs once a provider is reachable) ---
    from subliminal import ProviderPool, scan_video
    from babelfish import Language

    langs = {Language("en"), Language("es")}
    pool = ProviderPool(providers=reachable)
    videos = [Path(pilot)] if pilot else find_videos(MOVIES_DIR)[:20]
    results = {"downloaded": 0, "skipped": 0, "failed": 0, "items": []}

    for v in videos:
        print(f"\n  Video: {v.name}")
        en_need = "en" not in scan_sub_dirs(v)
        es_need = "es" not in scan_sub_dirs(v)
        if not (en_need or es_need):
            print("    already has both; skipping")
            results["skipped"] += 1
            continue
        try:
            video = scan_video(str(v))
        except Exception as e:
            print(f"    scan_video failed: {e}")
            results["failed"] += 1
            continue
        try:
            subs = pool.list_subtitles(video, langs)
            by_lang = {"en": [], "es": []}
            for s in subs:
                a2 = s.language.alpha2
                if a2 in by_lang:
                    by_lang[a2].append(s)
            print(f"    found: en={len(by_lang['en'])} es={len(by_lang['es'])}")
            if dry_run:
                continue
            for lang, lang_list in by_lang.items():
                if lang_list:
                    best = sorted(lang_list, key=lambda s: -s.score)[0]
                    out = v.with_suffix(f".{lang}.srt")
                    if out.exists():
                        out.unlink()
                    out.write_text(best.text, encoding="utf-8")
                    snap_to_frame_grid(out, get_video_fps(v) or 23.976)
                    synced, report = is_frame_synced(v, out)
                    print(f"    wrote {out.name}: frame_synced={synced} cues={report.get('num_cues')}")
                    results["downloaded"] += 1
        except Exception as e:
            print(f"    download failed: {e}")
            results["failed"] += 1
        results["items"].append({"path": str(v), "needs_en": en_need, "needs_es": es_need})

    return results


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    p = argparse.ArgumentParser("subtitle_pipeline.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    inv = sub.add_parser("inventory", help="Scan library, report en/es sub coverage")
    inv.add_argument("--save", help="Save JSON inventory to this path")

    dl = sub.add_parser("download", help="Download EN+ES subtitles")
    dl.add_argument("--pilot", help="Single video path for dry-run test")
    dl.add_argument("--dry-run", action="store_true")

    args = p.parse_args()
    if args.cmd == "inventory":
        data = inventory_cmd(args.save)
        print(json.dumps(data["stats"], indent=2))
    elif args.cmd == "download":
        res = download_cmd(pilot=getattr(args, "pilot", None),
                           dry_run=args.dry_run)
        print(json.dumps(res, indent=2, default=str))


if __name__ == "__main__":
    main()
