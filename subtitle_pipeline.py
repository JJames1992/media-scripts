#!/usr/bin/env python3
"""subtitle_pipeline.py — English + Spanish subtitles for J:/Media-Archive.

OpenSubtitles.com via apikey (no username/password login flow).
Frame-sync: every cue snapped to the video frame grid; verified
against video duration (half-frame tolerance).

Usage:
    python subtitle_pipeline.py inventory [--save PATH]
    python subtitle_pipeline.py download --pilot PATH
    python subtitle_pipeline.py download --all

Env:
    OPENSUBTITLESCOM_API_KEY  (required for download)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import time
from pathlib import Path

import requests
from babelfish import Language
from subliminal import ProviderPool, scan_video

logger = logging.getLogger("subtitle")

MOVIES_DIR = "J:/Media-Archive/Movies"
TV_SHOWS_DIR = "J:/Media-Archive/TV Shows"
SUPPORTED_LANGS = {"eng", "spa"}
API_KEY = os.environ.get("OPENSUBTITLESCOM_API_KEY", "")
BASE_URL = "https://api.opensubtitles.com/api/v1"

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
            if float(b):
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


def fmt_ms(t):
    hh = int(t // 3600000)
    mm = int((t % 3600000) // 60000)
    ss = int((t % 60000) // 1000)
    mmm = int(round(t % 1000))
    return f"{hh:02d}:{mm:02d}:{ss:02d},{mmm:03d}"


def snap_to_frame_grid(path: Path, fps: float):
    """Snap every cue start/end to the video frame grid."""
    ms_per_frame = 1000.0 / fps
    txt = path.read_text(encoding="utf-8", errors="replace")
    lines = txt.splitlines()
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

        def parse_ts(hh, mm, ss, ms_):
            return int(hh)*3600000 + int(mm)*60000 + int(ss)*1000 + int(ms_)

        sn = round(parse_ts(*m.group(1, 2, 3, 4)) / ms_per_frame)
        en = round(parse_ts(*m.group(5, 6, 7, 8)) / ms_per_frame)
        out.append(f"{fmt_ms(round(sn * ms_per_frame))} --> {fmt_ms(round(en * ms_per_frame))}")
        i += 1
        block = []
        while i < len(lines) and lines[i].strip() and not lines[i].strip().isdigit():
            block.append(lines[i]); i += 1
        out.extend(block)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def verify_frame_sync(video_path: Path, srt_path: Path, fps: float):
    """Return (frame_synced, report). Frame-synced = every cue
    within half a frame of the grid and no cue past video end."""
    ms_per_frame = 1000.0 / fps
    txt = srt_path.read_text(encoding="utf-8", errors="replace")
    cues = re.findall(
        r"(\d+):(\d+):(\d+),(\d{3}) --> (\d+):(\d+):(\d+),(\d{3})", txt)
    if not cues:
        return False, {"error": "no_cues"}

    def ms(hh, mm, ss, m):
        return int(hh)*3600000 + int(mm)*60000 + int(ss)*1000 + int(m)

    dur = get_video_duration_ms(video_path)
    tol = 0.5 / ms_per_frame  # half a frame in ms-units
    off_grid = 0
    past_end = 0
    for c in cues:
        s, e = ms(*c[:4]), ms(*c[4:])
        if abs(s / ms_per_frame - round(s / ms_per_frame)) > tol or \
           abs(e / ms_per_frame - round(e / ms_per_frame)) > tol:
            off_grid += 1
        if dur is not None and e > dur:
            past_end += 1
    return off_grid == 0 and past_end == 0, {
        "fps": fps, "num_cues": len(cues), "off_grid_cues": off_grid,
        "cues_past_video_end": past_end, "video_duration_ms": dur,
    }


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


def download_subtitle(subtitle, session: requests.Session):
    """Download subtitle content via the OpenSubtitles API (apikey auth)."""
    headers = {"Api-Key": API_KEY, "User-Agent": "subliminal/2.7.1",
               "Content-Type": "application/json", "Accept": "*/*"}
    body = {"file_id": subtitle.file_id, "file_name": subtitle.file_name,
            "sub_format": "srt"}
    r = session.post(f"{BASE_URL}/download", json=body, headers=headers,
                     timeout=30)
    r.raise_for_status()
    data = r.json()
    if "link" not in data:
        raise RuntimeError(f"no link in response: {data}")
    link = data["link"]
    remaining = int(data.get("remaining", -1))
    dl = session.get(link, timeout=60)
    dl.raise_for_status()
    return dl.content, remaining


def download_cmd(pilot=None, all_videos=False, dry_run=False):
    if not API_KEY:
        print("ERROR: OPENSUBTITLESCOM_API_KEY not set")
        return {"status": "no_api_key"}

    print("Provider reachability (from VPN tunnel):")
    try:
        r = requests.get(f"{BASE_URL}/subtitles", params={"languages": "en"},
                         headers={"Api-Key": API_KEY}, timeout=30)
        print(f"  opensubtitles.com: HTTP {r.status_code}")
        if r.status_code != 200:
            return {"status": "api_error", "code": r.status_code}
    except Exception as e:
        print(f"  opensubtitles.com: FAIL ({e})")
        return {"status": "unreachable", "error": str(e)}

    from subliminal import cache
    cache.region.configure("dogpile.cache.memory", replace_existing_backend=True)

    pool = ProviderPool(providers=["opensubtitlescom"])
    session = requests.Session()
    session.headers.update({"Api-Key": API_KEY,
                            "User-Agent": "subliminal/2.7.1"})

    if pilot:
        videos = [Path(pilot)]
    elif all_videos:
        videos = find_videos(MOVIES_DIR) + find_videos(TV_SHOWS_DIR)
    else:
        # default: first 20 that need subs
        candidates = []
        for v in find_videos(MOVIES_DIR) + find_videos(TV_SHOWS_DIR):
            if not ("en" in scan_sub_dirs(v) and "es" in scan_sub_dirs(v)):
                candidates.append(v)
        videos = candidates[:20]

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
            subs = pool.list_subtitles(video, SUPPORTED_LANGS)
        except Exception as e:
            print(f"    list_subtitles failed: {e}")
            results["failed"] += 1
            continue
        by_lang = {}
        for s in subs:
            by_lang.setdefault(s.language.alpha2, []).append(s)
        print(f"    found: en={len(by_lang.get('en', []))} es={len(by_lang.get('es', []))}")
        if dry_run:
            continue

        fps = get_video_fps(v)
        for lang, lst in sorted(by_lang.items()):
            if not lst:
                continue
            best = lst[0]
            try:
                content, remaining = download_subtitle(best, session)
            except Exception as e:
                print(f"    download {lang} failed: {e}")
                results["failed"] += 1
                continue
            out = v.with_suffix(f".{lang}.srt")
            out.write_bytes(content)
            if fps:
                snap_to_frame_grid(out, fps)
                synced, report = verify_frame_sync(v, out, fps)
                print(f"    wrote {out.name}: {len(content)}B, cues={report['num_cues']}, "
                      f"frame_synced={synced}, quota_left={remaining}")
            else:
                print(f"    wrote {out.name}: {len(content)}B (fps unknown, no snap)")
            results["downloaded"] += 1

    pool.terminate()
    session.close()
    return results


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    p = argparse.ArgumentParser("subtitle_pipeline.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    inv = sub.add_parser("inventory", help="Scan library, report en/es sub coverage")
    inv.add_argument("--save", help="Save JSON inventory to this path")

    dl = sub.add_parser("download", help="Download EN+ES subtitles")
    dl.add_argument("--pilot", help="Single video path for dry-run test")
    dl.add_argument("--all", action="store_true", help="Process all videos")
    dl.add_argument("--dry-run", action="store_true")

    args = p.parse_args()
    if args.cmd == "inventory":
        data = inventory_cmd(args.save)
        print(json.dumps(data["stats"], indent=2))
    elif args.cmd == "download":
        res = download_cmd(pilot=getattr(args, "pilot", None),
                           all_videos=args.all, dry_run=args.dry_run)
        print(json.dumps(res, indent=2, default=str))


if __name__ == "__main__":
    main()
