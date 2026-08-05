import os, re, json
MOV="J:/Media-Archive/Movies"
DRY=os.environ.get("DRY","1")=="1"
VID_EXT=('.mkv','.mp4','.avi','.m2ts')
EXCLUDE=set()  # none
def videos(folder):
    p=os.path.join(MOV,folder); out=[]
    for r,_,fs in os.walk(p):
        for f in fs:
            if f.lower().endswith(VID_EXT):
                out.append((os.path.join(r,f), os.path.getsize(os.path.join(r,f))))
    return out
def res_rank(name):
    m=re.search(r'(2160|4k|1440|1080|720|480)p', name.lower())
    return int(m.group(1).replace('4k','2160').replace('k','')) if m else 1080

log=[]; freed=0; locked=[]
for f in sorted(os.listdir(MOV)):
    p=os.path.join(MOV,f)
    if not os.path.isdir(p): continue
    if f in EXCLUDE: continue
    vids=videos(f)
    if len(vids)<=1: continue
    best=max(vids, key=lambda x:(res_rank(os.path.basename(x[0])), x[1]))
    for fp,sz in vids:
        if fp==best[0]: continue
        # don't delete if it's actually higher res than best despite size (size already considered)
        freed+=sz//1024//1024
        log.append(f"PRUNE {f}: {os.path.basename(fp)} ({sz//1024//1024}MB)")
        if not DRY:
            try: os.remove(fp)
            except PermissionError:
                locked.append(f"{f}/{os.path.basename(fp)}")

print(f"DRY={DRY} pruned={len(log)} freed~{freed}MB={freed//1024}GB")
for l in log[:40]: print("  "+l)
if locked:
    print(f"LOCKED (skip, retry later): {len(locked)}")
    for l in locked: print("  LOCKED "+l)
with open("C:/Users/jonat/prune_log.txt","w") as fh: fh.write("\n".join(log+["LOCKED:"]+locked))
