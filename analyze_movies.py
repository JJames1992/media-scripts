import os, re, json

MOV = "J:/Media-Archive/Movies"
VID_EXT = ('.mkv','.mp4','.avi','.m2ts','.ts')
def vid_files(folder):
    p=os.path.join(MOV,folder); out=[]
    for root,_,fns in os.walk(p):
        for f in fns:
            if f.lower().endswith(VID_EXT):
                out.append((os.path.join(root,f), os.path.getsize(os.path.join(root,f))))
    return out
def res_rank(name):
    m=re.search(r'(2160|4k|1440|1080|720|480)p', name.lower())
    return int(m.group(1).replace('4k','2160').replace('k','')) if m else 1080
def is_tv(name):
    return bool(re.search(r'[Ss]\d{1,2}[Ee]\d{1,2}', name)) or bool(re.search(r'\d{1,2}x\d{1,2}', name))
def years_in(folder):
    return re.findall(r'\((\d{4})\)', folder)
def base_of(folder):
    return re.sub(r'\s*\(\d{4}\)', '', folder).strip()

groups={}
for f in os.listdir(MOV):
    p=os.path.join(MOV,f)
    if os.path.isdir(p):
        groups.setdefault(base_of(f), []).append(f)

# collision check: any base whose folders disagree on year set (excluding double-year-only dup)
print("=== POTENTIAL YEAR COLLISIONS (same title, different years) ===")
collisions=0
for base,folders in groups.items():
    yr_sets=set()
    for f in folders:
        y=years_in(f)
        yr_sets.add(tuple(y))
    if len(yr_sets)>1:
        collisions+=1
        print(f"  {base!r}: {folders}  years={sorted(yr_sets)}")
if collisions==0: print("  none")

# also list double-year folders explicitly
print("\n=== DOUBLE-YEAR FOLDERS (junk) ===")
dbl=[f for f in os.listdir(MOV) if len(years_in(f))>=2]
for f in sorted(dbl): print(f"  {f}")
