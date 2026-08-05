
import json, urllib.request
BASE="http://localhost:20128"
def api(method, path, payload=None, t=60):
    data=json.dumps(payload).encode() if payload is not None else None
    req=urllib.request.Request(BASE+path,data=data,method=method,
                               headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=t) as r:
            return r.status, json.loads(r.read() or b"{}")
    except Exception as e:
        body = ""
        try: body = e.read().decode()[:300]
        except Exception: pass
        return getattr(e,"code","ERR"), body or str(e)

st, prov = api("GET","/api/providers")
print("PROVIDERS status", st)
if isinstance(prov, dict):
    for c in prov.get("connections", []):
        print(f"  {c['name']:<20} type={c['provider']:<14} active={c['isActive']} status={c['testStatus']} key={c.get('apiKey')}")
st, combos = api("GET","/api/combos")
print("COMBOS status", st)
if isinstance(combos, dict):
    lst = combos.get("combos", combos.get("data", []))
elif isinstance(combos, list):
    lst = combos
else:
    lst = []
for c in lst:
    print(f"  {c.get('name')} id={c.get('id')} strategy={c.get('strategy')} models={len(c.get('models') or [])}")
    for m in (c.get('models') or []):
        print("      -", m.get('model'), "|", m.get('provider'))
