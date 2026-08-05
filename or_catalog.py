
import json, urllib.request
BASE="http://localhost:20128"
def get(path, t=60):
    try:
        return json.load(urllib.request.urlopen(BASE+path,timeout=t))
    except Exception as e:
        return {"__err__": str(e)}
for p in ["/api/providers/catalog","/api/provider-types","/api/providers/types","/api/providers/available","/api/catalog","/api/settings"]:
    r = get(p, 20)
    s = json.dumps(r)[:400]
    print(p, "->", s)
    print()
