import os, shutil, os.path as P
MOV="J:/Media-Archive/Movies"; TV="J:/Media-Archive/TV Shows"
DRY=os.environ.get("DRY","1")=="1"

move_map = {
    "Chernobyl": ("Chernobyl", "Season 01"),
    "Moon Knight": ("Moon Knight", "Season 01"),
    "Agent Kim Reactivated (2026)": ("Agent Kim Reactivated", "Season 01"),
}

for src_name,(show,season) in move_map.items():
    src=P.join(MOV,src_name)
    if not P.isdir(src): 
        print(f"skip {src_name} (not found)"); continue
    dst=P.join(TV,show,season)
    if not DRY: os.makedirs(dst, exist_ok=True)
    moved=0
    for r,_,fs in os.walk(src):
        for f in fs:
            fp=P.join(r,f)
            ext=f.lower()
            if ext.endswith(('.mkv','.mp4','.avi')) or ext.endswith('.srt') or ext.endswith('.nfo'):
                # keep season-special/extra videos too if inside an 'extra' subfolder
                dstf=P.join(dst,f)
                if not DRY:
                    os.makedirs(P.dirname(dstf), exist_ok=True)
                    shutil.move(fp,dstf)
                moved+=1
    print(f"{'DRY ' if DRY else ''}moved {moved} files: {src_name} -> TV/{show}/{season}")
    if not DRY:
        # remove emptied movie folder
        try: shutil.rmtree(src)
        except OSError: pass
