import os, re, json, urllib.request, urllib.parse, time
TV_DIR = "J:/Media-Archive/TV Shows"

# TVMaze IDs for accurate episode data (avoids search ambiguity)
TVMAZE_IDS = {
    "Adventure Time": 290,
    "Agent Kim Reactivated": 89784,
    "Battle of Fates": 90255,
    "Better Call Saul": 618,
    "Breaking Bad": 169,
    "Chernobyl": 30770,           # HBO miniseries (1 season, 5 eps). 32844 was "Children's Ward" (wrong show -> fake S02/S03 gaps)
    "Dark": 17861,
    "Frasier": 540,           # 1993 series
    "Frasier (2023)": 53775,  # 2023 revival
    "Fringe": 158,
    "Gravity Falls": 396,
    "Guillermo del Toro's Cabinet of Curiosities": 36748,
    "Jaadugar A Witch in Mongolia": 89023,
    "Moon Knight": 43518,
    "Mr. Robot": 1871,
    "Over the Garden Wall": 1744,
    "Silo": 38052,
    "Sunny": 60398,
    "The Expanse": 1825,
    "The X-Files": 430,
    "Widows Bay": 79390,
    "Widow's Bay": 79390,     # TVMaze canonical name
}

def http_get(url, timeout=15):
    for a in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception:
            if a: return None
            time.sleep(2)
    return None

EP_RE = re.compile(r'[Ss](\d{1,2})[Ee](\d{1,2})')
EP2_RE = re.compile(r'(\d{1,2})x(\d{1,2})')
EP_COMBO_RE = re.compile(r'[Ss](\d{1,2})[Ee](\d{1,2})[Ee](\d{1,2})')

def on_disk_eps(show_folder):
    """Return set of (season, episode) present on disk for a show folder.
    Handles combined episode files (S01E19E20 covers both E19 and E20)."""
    sp = os.path.join(TV_DIR, show_folder)
    have = set()
    if not os.path.isdir(sp): return have
    for root,_,fns in os.walk(sp):
        for f in fns:
            if not f.lower().endswith(('.mkv','.mp4','.avi','.m2ts')): continue
            m = EP_RE.search(f) or EP2_RE.search(f)
            if m:
                s = int(m.group(1)); e = int(m.group(2))
                have.add((s, e))
                # combined episode file (S01E19E20) covers the range
                mc = EP_COMBO_RE.search(f)
                if mc and int(mc.group(1)) == s:
                    e2 = int(mc.group(3))
                    for extra in range(int(mc.group(2))+1, e2+1):
                        have.add((s, extra))
    return have

def tvmaze_episodes(show_name):
    """Return {season: set(episodes)} canonical, or None on failure."""
    # Use known TVMaze ID if available, otherwise fall back to search
    tid = TVMAZE_IDS.get(show_name)
    if tid:
        url = f"https://api.tvmaze.com/shows/{tid}/episodes"
    else:
        q = urllib.parse.quote_plus(show_name)
        url = f"https://api.tvmaze.com/singlesearch/shows?q={q}&embed=episodes"
    j = http_get(url, 20)
    if not j: return None
    try: data = json.loads(j)
    except: return None
    eps = {}
    # Direct episodes endpoint returns a list; singlesearch returns embedded
    episodes = data if isinstance(data, list) else data.get("_embedded",{}).get("episodes",[])
    for e in episodes:
        s = e.get("season"); n = e.get("number")
        if s and n:
            eps.setdefault(int(s), set()).add(int(n))
    return eps

def canonical_name(show_name):
    q = urllib.parse.quote_plus(show_name)
    j = http_get(f"https://api.tvmaze.com/singlesearch/shows?q={q}", 20)
    if not j: return show_name
    try: return json.loads(j).get("name", show_name)
    except: return show_name

def discover_gaps(show_name, disk_folder=None):
    """Compare on-disk episodes to TVMaze canonical; return sorted list of missing (s,e)."""
    disk_folder = disk_folder or show_name
    have = on_disk_eps(disk_folder)
    canon = tvmaze_episodes(show_name)
    if canon is None:
        return None  # cannot verify
    missing = []
    for s in sorted(canon):
        for e in sorted(canon[s]):
            if (s,e) not in have:
                missing.append((s,e))
    return missing

if __name__ == "__main__":
    # quick test
    for name in ["Dark","Fringe","Adventure Time"]:
        g = discover_gaps(name)
        print(name, "->", (f"{len(g)} missing" if g is not None else "TVMaze N/A"), g[:6] if g else "")
