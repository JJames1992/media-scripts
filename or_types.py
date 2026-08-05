
import json, urllib.request
BASE="http://localhost:20128"
def api(method, path, payload=None, t=30):
    data=json.dumps(payload).encode() if payload is not None else None
    req=urllib.request.Request(BASE+path,data=data,method=method,headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=t) as r:
            return r.status, json.loads(r.read() or b"{}")
    except Exception as e:
        body=""
        try: body=e.read().decode()[:1500]
        except Exception: pass
        return getattr(e,"code","ERR"), body or str(e)
st,d = api("POST","/api/providers",{"provider":"__bogus__","name":"__bogus__","apiKey":"x"})
print("INVALID PROVIDER PROBE:", st)
print(d if isinstance(d,str) else json.dumps(d)[:2000])
