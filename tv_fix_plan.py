import os, re, shutil
TV="J:/Media-Archive/TV Shows"
MOV="J:/Media-Archive/Movies"
DRY=os.environ.get("DRY","1")=="1"

def tv_vids(folder):
    p=os.path.join(TV,folder); out=[]
    for r,_,fs in os.walk(p):
        for f in fs:
            if f.lower().endswith(('.mkv','.mp4','.avi')): out.append(os.path.join(r,f))
    return out

actions=[]
# 1) Frasier (1993) -> rename to Frasier (2023), it's the reboot S02
src="Frasier (1993)"; dst="Frasier (2023)"
if os.path.isdir(os.path.join(TV,src)) and not os.path.isdir(os.path.join(TV,dst)):
    actions.append(("RENAME", src, dst))
# 2) Gravity Falls (bare, partial S1) -> merge into Gravity Falls (2012)
#    The bare folder only has S1 E1,9,10,15 which already exist in (2012). So just delete the redundant bare folder.
src="Gravity Falls"; dst="Gravity Falls (2012)"
if os.path.isdir(os.path.join(TV,src)):
    # confirm overlap: everything in bare is in (2012)
    bare=tv_vids(src); keep=[]
    for v in bare:
        s,e=re.search(r'[Ss](\d{1,2})[Ee](\d{1,2})',v).groups() if re.search(r'[Ss](\d{1,2})[Ee](\d{1,2})',v) else (None,None)
        keep.append((os.path.basename(v), s, e))
    actions.append(("DELETE_REDUNDANT", src, "already in "+dst, keep))
# 3) Dark (2017) -> The Dark Tower movie into Movies
src="Dark (2017)"
if os.path.isdir(os.path.join(TV,src)):
    for r,_,fs in os.walk(os.path.join(TV,src)):
        for f in fs:
            if f.lower().endswith(('.mkv','.mp4')):
                actions.append(("MOVE_TO_MOVIES", os.path.join(r,f), "Movies/The Dark Tower (2017)"))
# 4) The X-Files merge: bare 'The X-Files' -> 'The X-Files (1993)'
src="The X-Files"; dst="The X-Files (1993)"
if os.path.isdir(os.path.join(TV,src)) and os.path.isdir(os.path.join(TV,dst)):
    actions.append(("MERGE", src, dst))

for a in actions: print(a)
print(f"DRY={DRY}")
