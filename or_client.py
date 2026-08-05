
import json, urllib.request
BASE="http://localhost:20128"
d=json.load(urllib.request.urlopen(BASE+"/api/providers/client",timeout=60))
print(type(d), list(d)[:20] if isinstance(d,dict) else len(d))
open(r"C:\Users\jonat\or_client.json","w",encoding="utf-8").write(json.dumps(d,indent=1))
print("written")
