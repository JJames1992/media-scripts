import os, re, json

MOV = "J:/Media-Archive/Movies"
VID_EXT = ('.mkv', '.mp4', '.avi', '.m2ts', '.ts', '.m4v')

def vid_files(folder):
    p = os.path.join(MOV, folder)
    out = []
    for root, _, fns in os.walk(p):
        for f in fns:
            if f.lower().endswith(VID_EXT):
                fp = os.path.join(root, f)
                out.append((fp, os.path.getsize(fp), f))
    return out

def res_rank(name):
    m = re.search(r'(2160|1440|1080|720|480)p', name.lower())
    if not m: return None
    return int(m.group(1))

def normalize(name):
    s = name.lower()
    s = re.sub(r'\((\d{4})\)', '', s)          # drop year
    s = re.sub(r'[^\w\s]', ' ', s)             # punctuation -> space
    s = re.sub(r'\s+', ' ', s).strip()
    return s

groups = {}
for f in os.listdir(MOV):
    p = os.path.join(MOV, f)
    if os.path.isdir(p):
        groups.setdefault(normalize(f), []).append(f)

# number-word map for extra collisions
NUM = {'twelve':'12','12':'12'}
def alt_key(name):
    s = normalize(name)
    for k,v in NUM.items():
        s = s.replace(k, v)
    return s
groups2 = {}
for f in os.listdir(MOV):
    p = os.path.join(MOV, f)
    if os.path.isdir(p):
        groups2.setdefault(alt_key(f), []).append(f)

report = {}
for key, folders in sorted(groups2.items()):
    if len(folders) < 2:
        continue
    entry = []
    for fol in sorted(folders):
        vids = vid_files(fol)
        info = []
        for fp, sz, fn in vids:
            info.append({"file": fn, "bytes": sz, "mb": round(sz/1e6,1),
                         "res": res_rank(fn)})
        entry.append({"folder": fol, "videos": info})
    report[key] = entry

print(f"duplicate title-groups: {len(report)}\n")
for key, entry in report.items():
    print(f"### {key}")
    for e in entry:
        vids = e["videos"]
        if not vids:
            print(f"  - {e['folder']}:  <NO VIDEO FILES>")
            continue
        for v in vids:
            print(f"  - {e['folder']}: {v['file']}  ({v['mb']}MB, res={v['res']})")
    print()

with open("C:/Users/jonat/dup_audit.json","w") as fh:
    json.dump(report, fh, indent=2)
print("saved dup_audit.json")
