import os, re, json

MOV = "J:/Media-Archive/Movies"
DRY = os.environ.get("DRY", "1") == "1"

VID_EXT = ('.mkv', '.mp4', '.avi', '.m2ts', '.ts')
def vid_files(folder):
    p = os.path.join(MOV, folder)
    out = []
    for root, _, fns in os.walk(p):
        for f in fns:
            if f.lower().endswith(VID_EXT):
                out.append((os.path.join(root, f), os.path.getsize(os.path.join(root, f))))
    return out

def res_rank(name):
    m = re.search(r'(2160|4k|1440|1080|720|480)p', name.lower())
    if not m: return 1080  # assume 1080 if unspecified
    return int(m.group(1).replace('4k','2160').replace('k',''))

def is_tv(name):
    return bool(re.search(r'[Ss]\d{1,2}[Ee]\d{1,2}', name)) or bool(re.search(r'\d{1,2}x\d{1,2}', name))

def year_of(folder):
    m = re.search(r'\((\d{4})\)', folder)
    return m.group(1) if m else None

groups = {}
for f in os.listdir(MOV):
    p = os.path.join(MOV, f)
    if os.path.isdir(p):
        base = re.sub(r'\s*\(\d{4}\)\s*$', '', f).strip()
        groups.setdefault(base, []).append(f)

plan = []
flags = []
for base, folders in sorted(groups.items()):
    if len(folders) < 2:
        continue
    yered = [f for f in folders if year_of(f) is not None]
    yr = year_of(yered[0]) if yered else None
    canonical = f"{base} ({yr})" if yr else base
    # score each folder by best video
    scored = []
    for f in folders:
        vids = vid_files(f)
        if not vids:
            scored.append((f, -1, 0, None)); continue
        best = max(vids, key=lambda x: (res_rank(os.path.basename(x[0])), x[1]))
        # skip zero-byte videos for ranking
        vids_nz = [v for v in vids if v[1] > 0]
        if vids_nz:
            best = max(vids_nz, key=lambda x: (res_rank(os.path.basename(x[0])), x[1]))
        scored.append((f, res_rank(os.path.basename(best[0])), best[1], os.path.basename(best[0])))
    winner = max(scored, key=lambda x: (x[1], x[2]))[0]
    losers = [f for f in folders if f != winner]
    # flag TV episodes inside movie winners
    win_vids = vid_files(winner)
    tvflag = [os.path.basename(v[0]) for v in win_vids if is_tv(os.path.basename(v[0]))]
    if tvflag:
        flags.append((base, winner, tvflag))
    plan.append({"base": base, "canonical": canonical, "winner": winner,
                 "losers": losers,
                 "winner_video": scored[[s[0] for s in scored].index(winner)][3]})

print(f"DRY={DRY} pairs={len(plan)} tv_flagged={len(flags)}")
# print only flagged/edge cases + first 8 normal
for base, winner, tvf in flags:
    print(f"  !! TV-EPISODE IN MOVIE: {base}  winner={winner}  ep={tvf}")
print("--- sample plan ---")
for p in plan[:8]:
    print(f"  {p['base'][:38]:38s} keep[{p['winner']}] drop{p['losers']}")
with open("C:/Users/jonat/movie_plan.json","w") as fh:
    json.dump(plan, fh, indent=2)
print("saved movie_plan.json")
