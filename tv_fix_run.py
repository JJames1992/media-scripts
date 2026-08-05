import os, re, shutil
TV="J:/Media-Archive/TV Shows"; MOV="J:/Media-Archive/Movies"
DRY=os.environ.get("DRY","1")=="1"
VID=('.mkv','.mp4','.avi')

def move_tree(src, dst):
    os.makedirs(dst, exist_ok=True)
    for r,_,fs in os.walk(src):
        for f in fs:
            fp=os.path.join(r,f); dstf=os.path.join(dst, os.path.relpath(fp,src))
            os.makedirs(os.path.dirname(dstf), exist_ok=True)
            shutil.move(fp, dstf)
    shutil.rmtree(src)

# 1) Frasier (1993) -> Frasier (2023) (it's the reboot S02)
s=os.path.join(TV,"Frasier (1993)"); d=os.path.join(TV,"Frasier (2023)")
if os.path.isdir(s) and not os.path.isdir(d):
    print(f"{'DRY ' if DRY else ''}RENAME Frasier (1993) -> Frasier (2023)")
    if not DRY: os.rename(s,d)

# 2) Gravity Falls (bare, redundant) -> delete
s=os.path.join(TV,"Gravity Falls"); d=os.path.join(TV,"Gravity Falls (2012)")
if os.path.isdir(s):
    # keep only files NOT already in (2012)
    exist={fn for _,_,fs in os.walk(d) for fn in fs if fn.lower().endswith(VID)}
    unique=[]
    for r,_,fs in os.walk(s):
        for fn in fs:
            if fn.lower().endswith(VID) and fn not in exist:
                unique.append(os.path.join(r,fn))
    if unique:
        print(f"KEEP unique from Gravity Falls: {[os.path.basename(u) for u in unique]}")
    else:
        print(f"{'DRY ' if DRY else ''}DELETE redundant Gravity Falls (all in 2012)")
        if not DRY: shutil.rmtree(s)

# 3) Dark (2017) -> Movies/The Dark Tower (2017)
s=os.path.join(TV,"Dark (2017)")
if os.path.isdir(s):
    dst=os.path.join(MOV,"The Dark Tower (2017)")
    print(f"{'DRY ' if DRY else ''}MOVE Dark (2017) -> Movies/The Dark Tower (2017)")
    if not DRY:
        os.makedirs(dst, exist_ok=True)
        for r,_,fs in os.walk(s):
            for f in fs:
                if f.lower().endswith(VID):
                    shutil.move(os.path.join(r,f), os.path.join(dst,f))
        shutil.rmtree(s)

# 4) The X-Files (bare) merge into The X-Files (1993)
s=os.path.join(TV,"The X-Files"); d=os.path.join(TV,"The X-Files (1993)")
if os.path.isdir(s) and os.path.isdir(d):
    print(f"{'DRY ' if DRY else ''}MERGE The X-Files -> The X-Files (1993)")
    if not DRY: move_tree(s, d)
print("done")
