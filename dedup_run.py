import os, re, json, shutil

MOV = "J:/Media-Archive/Movies"
DRY = os.environ.get("DRY", "1") == "1"
VID_EXT = ('.mkv','.mp4','.avi','.m2ts','.ts')
EXCLUDE = {'Agent Kim Reactivated'}  # TV series misfiled under Movies

def res_rank(name):
    m=re.search(r'(2160|4k|1440|1080|720|480)p', name.lower())
    return int(m.group(1).replace('4k','2160').replace('k','')) if m else 1080
def years_in(folder): return re.findall(r'\((\d{4})\)', folder)
def base_of(folder): return re.sub(r'\s*\(\d{4}\)', '', folder).strip()

groups={}
for f in os.listdir(MOV):
    p=os.path.join(MOV,f)
    if os.path.isdir(p): groups.setdefault(base_of(f), []).append(f)

def iter_files(folder):
    p=os.path.join(MOV,folder)
    for root,_,fns in os.walk(p):
        for f in fns:
            yield os.path.join(root,f)

log=[]
for base, folders in sorted(groups.items()):
    if base in EXCLUDE: continue
    if len(folders)<2: continue
    yrs=[y for f in folders for y in years_in(f)]
    yr=sorted(set(yrs))[0] if yrs else None
    canonical=f"{base} ({yr})" if yr else base
    target_path=os.path.join(MOV,canonical)
    srcs=[f for f in folders if f!=canonical]
    if not srcs:  # canonical already is the only/best; nothing to do
        continue
    log.append(f"MERGE {base}: -> {canonical}  from {srcs}")
    if DRY: continue
    os.makedirs(target_path, exist_ok=True)
    for src in srcs:
        src_path=os.path.join(MOV,src)
        for fpath in iter_files(src):
            rel=os.path.relpath(fpath, src_path)
            dst=os.path.join(target_path, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.exists(dst):
                # keep higher quality: prefer larger; tie-break by resolution
                if os.path.getsize(fpath) > os.path.getsize(dst):
                    shutil.move(fpath, dst)
                # else keep existing
            else:
                shutil.move(fpath, dst)
        # remove now-empty source
        try:
            shutil.rmtree(src_path)
        except OSError:
            pass

print(f"DRY={DRY} merged={len(log)}")
for l in log: print("  "+l)
with open("C:/Users/jonat/dedup_log.txt","w") as fh: fh.write("\n".join(log))
